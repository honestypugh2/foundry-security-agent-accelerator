"""Validate participant notebooks; execute only allowlisted local notebooks in memory."""

import argparse
import ast
import os
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
MODES = {
    "00_environment_setup.ipynb": "local",
    "01_foundry_agent_live.ipynb": "azure",
    "02_protect_identity_and_tools.ipynb": "local",
    "03_prove_evaluations_and_redteam.ipynb": "local",
    "04_operate_traces_and_audit.ipynb": "local",
    "05_agent365_extension.ipynb": "azure",
    "06_local_fallback.ipynb": "local",
    "07_agent365_request_approval_publish.ipynb": "local",
}
GUARD = """
import os
import socket
from unittest.mock import patch
from contextlib import ExitStack
from azure.identity import DefaultAzureCredential
from foundry_security_accelerator.config import Settings
for name in tuple(os.environ):
    if name.startswith('FSA_'):
        del os.environ[name]
Settings.model_config['env_file'] = None
def deny_network(*args, **kwargs):
    raise AssertionError('Local notebook attempted network or credential acquisition')
_guard = ExitStack()
_guard.enter_context(patch.object(socket.socket, 'connect', deny_network))
_guard.enter_context(patch.object(socket, 'create_connection', deny_network))
_guard.enter_context(patch.object(socket, 'getaddrinfo', deny_network))
_guard.enter_context(patch.object(DefaultAzureCredential, 'get_token', deny_network))
"""


def validate(path: Path) -> nbformat.NotebookNode:
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    expected_mode = MODES[path.name]
    metadata = notebook.metadata
    if metadata.get("kernelspec", {}).get("name") != "python3":
        raise ValueError(f"{path.name}: Python kernel required")
    if metadata.get("language_info", {}).get("name") != "python":
        raise ValueError(f"{path.name}: Python language metadata required")
    apex = metadata.get("apex", {})
    if (
        apex.get("mode") != expected_mode
        or apex.get("ci_execute") is not (expected_mode == "local")
        or not apex.get("level")
        or not isinstance(apex.get("duration_minutes"), int)
        or apex["duration_minutes"] <= 0
    ):
        raise ValueError(f"{path.name}: invalid execution metadata")
    prose = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "markdown")
    for heading in (
        "Learning objective",
        "Technical level",
        "Prerequisites",
        "Cost and permissions",
        "Expected results",
        "Security explanation",
        "Troubleshooting",
        "Cleanup",
        "Source modules",
    ):
        if heading not in prose:
            raise ValueError(f"{path.name}: missing {heading}")
    package_imported = False
    for cell in notebook.cells:
        if cell.cell_type == "code":
            if cell.outputs or cell.execution_count is not None:
                raise ValueError(f"{path.name}: committed outputs/counts forbidden")
            for node in ast.walk(ast.parse(cell.source)):
                if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                    "foundry_security_accelerator"
                ):
                    module = import_module(node.module)
                    if any(not hasattr(module, name.name) for name in node.names):
                        raise ValueError(f"{path.name}: unresolved implementation import")
                    package_imported = True
        elif cell.get("attachments"):
            raise ValueError(f"{path.name}: embedded attachments require manual review")
    if not package_imported:
        raise ValueError(f"{path.name}: import the existing implementation")
    return notebook


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-local", action="store_true")
    args = parser.parse_args()
    paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
    if {path.name for path in paths} != set(MODES):
        raise ValueError("Expected exactly the reviewed participant notebook allowlist")
    executed = 0
    for path in paths:
        notebook = validate(path)
        if args.execute_local and MODES[path.name] == "local":
            notebook.cells.insert(0, nbformat.v4.new_code_cell(GUARD))
            with TemporaryDirectory(prefix="fsa-notebook-") as runtime:
                manager = KernelManager(
                    transport="ipc" if os.name == "posix" else "tcp",
                    ip=str(Path(runtime) / "kernel-ipc") if os.name == "posix" else "127.0.0.1",
                    connection_file=str(Path(runtime) / "connection.json"),
                )
                NotebookClient(
                    notebook,
                    timeout=120,
                    kernel_name="python3",
                    km=manager,
                    resources={"metadata": {"path": str(ROOT)}},
                ).execute(cleanup_kc=True)
            executed += 1
        print(f"PASS: {path.name} ({MODES[path.name]}; source unchanged)")
    print(f"Validated {len(paths)} notebooks; executed {executed} local; Azure excluded.")


if __name__ == "__main__":
    main()
