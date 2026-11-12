import importlib.util
from pathlib import Path

import nbformat
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_notebooks", ROOT / "scripts/validate_notebooks.py"
)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.mark.parametrize("filename", validator.MODES)
def test_notebook_contract(filename: str) -> None:
    validator.validate(ROOT / "notebooks" / filename)


@pytest.mark.parametrize("invalid", ["outputs", "execution_count", "mode", "import", "symbol"])
def test_notebook_rejects_leaked_outputs_or_unsafe_ci_contract(
    tmp_path: Path, invalid: str
) -> None:
    path = ROOT / "notebooks/01_foundry_agent_live.ipynb"
    notebook = nbformat.read(path, as_version=4)
    if invalid == "mode":
        notebook.metadata.apex.update(mode="local", ci_execute=True)
    else:
        cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
        if invalid == "outputs":
            cells[0].outputs = [nbformat.v4.new_output("stream", name="stdout", text="private")]
        elif invalid == "execution_count":
            cells[0].execution_count = 1
        elif invalid == "symbol":
            for cell in cells:
                cell.source = "from foundry_security_accelerator.config import missing_symbol"
        else:
            for cell in cells:
                cell.source = "print('not using the package')"
    target = tmp_path / path.name
    nbformat.write(notebook, target)
    with pytest.raises(ValueError):
        validator.validate(target)
