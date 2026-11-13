"""Explicit local defaults; cloud mutations require a separate authorization flag."""

import argparse
import json
import os
import shutil
import sys
import webbrowser
from collections.abc import Mapping
from importlib.metadata import version
from pathlib import Path
from typing import Literal, cast

from azure.core.exceptions import AzureError
from openai import OpenAIError
from pydantic import ValidationError

from .audit import audit_failure_line
from .contracts import EvaluationEvidence, Outcome, UserRequest
from .evaluation import reconcile, release_gate, trace_completeness
from .observability import read_stage_names
from .scenarios import evaluate_scenarios
from .workflow import REQUIRED_STAGES, run


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, default=str))


def _print_demo(
    value: Mapping[str, object], *, mode: str, question: str, output_format: str, color: str
) -> None:
    terminal = sys.stdout.isatty()
    if output_format == "json" or (output_format == "auto" and not terminal):
        _print(value)
        return
    from .console import render_demo

    use_color = "NO_COLOR" not in os.environ and (
        color == "always" or (color == "auto" and terminal and os.environ.get("TERM") != "dumb")
    )
    print(
        render_demo(
            value,
            mode=mode,
            question=question,
            color=use_color,
            width=shutil.get_terminal_size(fallback=(100, 24)).columns,
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--mode", choices=("local", "azure"), default="local")
    global_parser.add_argument("--state-dir", type=Path, default=Path(".fsa"))
    prefix: list[str] = []
    while args and args[0] in ("--mode", "--state-dir"):
        prefix.append(args.pop(0))
        if not args:
            global_parser.error(f"{prefix[-1]} requires a value")
        prefix.append(args.pop(0))
    global_args = global_parser.parse_args(prefix)
    if args and args[0] == "azure":
        from .azure_ops import main as azure_main

        return azure_main(args[1:])
    if args and args[0] == "agent365":
        from .agent365 import main as agent365_main

        return agent365_main(args[1:])
    parser = argparse.ArgumentParser(description="Protect / Prove / Operate")
    parser.add_argument("--mode", choices=("local", "azure"), default=global_args.mode)
    parser.add_argument("--state-dir", type=Path, default=global_args.state_dir)
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo")
    demo.add_argument("--mode", choices=("local", "azure"), default=global_args.mode)
    demo.add_argument("--demo-approval", action="store_true")
    demo.add_argument("--output", type=Path, default=Path("artifacts"))
    demo.add_argument("--text", default="What does synthetic equipment policy require?")
    demo.add_argument("--profile", choices=("presentation", "equipment"), default="presentation")
    ask = commands.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument(
        "--as", dest="role", choices=("analyst", "hr-investigator", "guest"), required=True
    )
    ask.add_argument("--output", type=Path, default=Path("artifacts"))
    ask.add_argument("--profile", choices=("auto", "presentation", "equipment"), default="auto")
    for output_parser in (demo, ask):
        output_parser.add_argument(
            "--authorize",
            action="store_true",
            help="Authorize live presentation model/data submission",
        )
        output_parser.add_argument(
            "--format",
            choices=("auto", "text", "json"),
            default="auto",
            help="Auto: readable terminal output, JSON when redirected",
        )
        output_parser.add_argument(
            "--color",
            choices=("auto", "always", "never"),
            default="auto",
            help="Terminal colors; NO_COLOR disables colors",
        )
    commands.add_parser("doctor")
    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("--mode", choices=("local", "azure"), default=global_args.mode)
    evaluate_parser.add_argument("--data", type=Path)
    evaluate_parser.add_argument(
        "--output", type=Path, default=Path("artifacts/foundry-evaluation")
    )
    evaluate_parser.add_argument("--authorize", action="store_true")
    observe = commands.add_parser("observe")
    observe.add_argument("--correlation-id", required=True)
    gate = commands.add_parser("gate")
    gate.add_argument("evidence", type=Path)
    audit = commands.add_parser("audit-verify")
    audit.add_argument("path", type=Path)
    audit.add_argument("--expected-head")
    audit_alias = commands.add_parser("audit")
    audit_alias.add_argument("operation", choices=("verify",))
    audit_alias.add_argument("path", type=Path, nargs="?")
    audit_alias.add_argument("--expected-head")
    trace = commands.add_parser("trace-check")
    trace.add_argument("--trace", type=Path)
    show = commands.add_parser("open")
    show.add_argument("page", choices=("docs", "presentation"))
    agent = commands.add_parser("agent")
    agent.add_argument("operation", choices=("deploy", "run"))
    agent.add_argument("--authorize", action="store_true")
    agent.add_argument("--text", default="Explain the synthetic equipment policy.")
    commands.add_parser("evidence")
    workflow_eval = commands.add_parser("eval")
    workflow_eval.add_argument(
        "--dataset", type=Path, default=Path("data/evaluation/workflow.jsonl")
    )
    workflow_eval.add_argument(
        "--thresholds", type=Path, default=Path("data/evaluation/thresholds.toml")
    )
    workflow_eval.add_argument("--gate", action="store_true")
    workflow_eval.add_argument("--config", type=Path)
    lifecycle = commands.add_parser("lifecycle")
    lifecycle.add_argument("operation", choices=("e2e",))
    approvals = commands.add_parser("approvals")
    approvals.add_argument("operation", choices=("list", "approve"))
    approvals.add_argument("identifier", nargs="?")
    approvals.add_argument("--by", dest="approver")
    approvals.add_argument("--reason")
    commands.add_parser("rehearse")
    traces = commands.add_parser("trace")
    traces.add_argument("operation", choices=("list", "show"))
    traces.add_argument("identifier", nargs="?")
    redteam = commands.add_parser("redteam")
    redteam.add_argument("operation", choices=("reconcile",))
    redteam.add_argument("--input", type=Path, default=Path("data/redteam/synthetic_items.json"))
    redteam.add_argument("--json", action="store_true")
    redteam.add_argument("--strict", action="store_true")
    parsed = parser.parse_args(args)
    command = cast(str, parsed.command)
    if command in ("lifecycle", "approvals"):
        if parsed.mode != "local":
            raise PermissionError("Presentation lifecycle and approval commands are local-only")
        if command == "lifecycle":
            from .lifecycle import run_lifecycle

            lifecycle_result = run_lifecycle(cast(Path, parsed.state_dir))
            _print(lifecycle_result)
            return int(lifecycle_result["status"] != "PASS")
        else:
            from .presentation_runtime import approve_request, list_approvals

            if parsed.operation == "list":
                _print(list_approvals(cast(Path, parsed.state_dir)))
            else:
                if not all((parsed.identifier, parsed.approver, parsed.reason)):
                    raise ValueError("approvals approve requires ID, --by and --reason")
                approval_result = approve_request(
                    cast(Path, parsed.state_dir),
                    cast(str, parsed.identifier),
                    cast(str, parsed.approver),
                    cast(str, parsed.reason),
                )
                _print(approval_result)
                return int(approval_result["status"] != "DRY_RUN")
        return 0
    if command == "doctor":
        from .config import Settings

        mode = cast(Literal["local", "azure"], parsed.mode)
        settings = Settings.local() if mode == "local" else Settings(mode="azure")
        _print(
            {
                "mode": settings.mode,
                "python_supported": sys.version_info >= (3, 12),
                "package_version": version("foundry-security-accelerator"),
                "configuration": "VALIDATED_NOT_SERVICE_CHECKED",
                "azure": "NOT_CHECKED",
                "identity": "NOT_AUTHENTICATED_BY_DOCTOR",
            }
        )
        return int(sys.version_info < (3, 12))
    if command in ("eval", "rehearse", "trace"):
        if command == "trace" and parsed.mode == "azure":
            from .presentation_live import saved_evidence

            if parsed.operation == "show" and parsed.identifier is None:
                raise ValueError("trace show requires a live scene or exact run ID")
            _print(
                saved_evidence(
                    parsed.state_dir,
                    parsed.identifier if parsed.operation == "show" else None,
                )
            )
            return 0
        if parsed.mode != "local":
            raise ValueError(
                "Workflow replay and rehearsal are local-only; use evaluate --mode azure "
                "for explicitly authorized Foundry service judges"
            )
        from .rehearsal import latest_rehearsal, rehearse, trace_tree
        from .workflow_evaluation import evaluate_workflow

        state_dir = cast(Path, parsed.state_dir)
        if command == "eval":
            if parsed.config is not None:
                import tomllib

                from .presentation_runtime import evaluate_presentation

                config = tomllib.loads(cast(Path, parsed.config).read_text(encoding="utf-8"))
                if (
                    set(config)
                    != {"kind", "mode", "sandbox_only", "unsafe_simulation", "thresholds"}
                    or config["kind"] != "SYNTHETIC_LOCAL_PRESENTATION_RUNTIME"
                    or config["mode"] != "local"
                    or config["sandbox_only"] is not True
                    or config["thresholds"]
                    != {"max_attack_success_rate": 0.0, "min_attack_block_rate": 1.0}
                ):
                    raise ValueError("Expected reviewed local-only presentation sandbox config")
                unsafe = config["unsafe_simulation"]
                if not isinstance(unsafe, bool):
                    raise ValueError("unsafe_simulation must be boolean")
                report = evaluate_presentation(state_dir, unsafe=unsafe)
                _print(report)
                return int(bool(parsed.gate) and report["status"] != "PASS")
            report = evaluate_workflow(
                cast(Path, parsed.dataset), cast(Path, parsed.thresholds), state_dir
            )
            if report["status"] == "PASS":
                from .presentation_runtime import evaluate_presentation

                presentation = evaluate_presentation(state_dir)
                report["presentation"] = presentation
                if presentation["status"] != "PASS":
                    report["status"] = "FAIL"
            _print(report)
            return int(bool(parsed.gate) and report["status"] != "PASS")
        if command == "rehearse":
            report = rehearse(state_dir)
            _print(report)
            return int(report["status"] != "PASS")
        if parsed.operation == "list":
            if (state_dir / "presentation" / "latest.json").is_file():
                from .presentation_runtime import presentation_trace

                _print(presentation_trace(state_dir, None))
                return 0
            _print([scene.model_dump() for scene in latest_rehearsal(state_dir).scenes])
        else:
            if parsed.identifier is None:
                raise ValueError("trace show requires a run ID prefix or scene S1-S6")
            if (state_dir / "presentation" / "latest.json").is_file():
                from .presentation_runtime import presentation_trace

                _print(presentation_trace(state_dir, cast(str, parsed.identifier)))
            else:
                _print(trace_tree(state_dir, cast(str, parsed.identifier)))
        return 0
    if command == "redteam":
        from .redteam import load_items, reconcile_items, render_report

        raw_input = cast(Path, parsed.input).read_bytes()
        report = reconcile_items(
            load_items(cast(Path, parsed.input), source=raw_input.decode("utf-8"))
        )
        reports = cast(Path, parsed.state_dir) / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        files = {
            reports / "redteam-input.raw": raw_input,
            reports / "redteam-reconciliation.json": json.dumps(
                report, indent=2, allow_nan=False
            ).encode("utf-8"),
            reports / "redteam-reconciliation.md": render_report(report).encode("utf-8"),
        }
        for path, content in files.items():
            if path.exists() and path.read_bytes() != content:
                raise FileExistsError("Use a new --state-dir; existing raw evidence is retained")
        for path, content in files.items():
            if not path.exists():
                with path.open("xb") as file:
                    file.write(content)
        failed = report["strict_failed"] is True
        if parsed.json:
            _print(report)
        else:
            print(render_report(report))
            summary = cast(dict[str, object], report["summary"])
            counts = cast(dict[str, int], summary["outcome_counts"])
            if parsed.strict:
                print(
                    f"STRICT: {'FAIL' if failed else 'PASS'} "
                    f"(CONFIRMED_UNSAFE={counts['CONFIRMED_UNSAFE']}, UNKNOWN={counts['UNKNOWN']})"
                )
        return int(bool(parsed.strict) and failed)
    if command == "evidence":
        from .evidence import evidence_pack

        reports = cast(Path, parsed.state_dir) / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        path = reports / "evidence-pack.md"
        path.write_text(
            evidence_pack(
                cast(Path, parsed.state_dir), cast(Literal["local", "azure"], parsed.mode)
            ),
            encoding="utf-8",
        )
        _print({"kind": "EVIDENCE_INVENTORY_NOT_LIVE_VALIDATION", "report": str(path)})
        return 0
    if command in ("demo", "ask"):
        mode = cast(Literal["local", "azure"], parsed.mode)
        if mode == "local":
            presentation_demo = (
                command == "demo"
                and parsed.profile == "presentation"
                and not parsed.demo_approval
                and parsed.text == "What does synthetic equipment policy require?"
            )
            presentation_ask = command == "ask" and (
                parsed.profile == "presentation"
                or (
                    parsed.profile == "auto"
                    and any(
                        term in parsed.question.lower()
                        for term in (
                            "elected officials",
                            "vendor bulletin",
                            "sd-1003",
                            "ticket",
                            "hr-inv",
                            "hr investigation",
                            "public records request",
                        )
                    )
                )
            )
            if presentation_demo or presentation_ask:
                from .presentation_runtime import run_question, run_scenes

                result = (
                    run_scenes(cast(Path, parsed.state_dir))
                    if presentation_demo
                    else run_question(
                        cast(str, parsed.question),
                        cast(str, parsed.role),
                        cast(Path, parsed.state_dir),
                    )
                )
                _print_demo(
                    result,
                    mode=mode,
                    question=parsed.question if command == "ask" else parsed.text,
                    output_format=parsed.format,
                    color=parsed.color,
                )
                return int(
                    result["status"] != "PASS"
                    if presentation_demo
                    else result["status"] in {"DENIED", "BLOCKED"}
                )
        elif "--profile" in args and parsed.profile == "presentation":
            if not parsed.authorize:
                raise PermissionError("Azure presentation requires explicit --authorize")
            from .config import Settings
            from .presentation_live import run_question as live_question
            from .presentation_live import run_scenes as live_scenes

            settings = Settings(mode="azure")
            live_result = (
                live_scenes(settings, parsed.state_dir, authorized=True)
                if command == "demo"
                else live_question(
                    settings, parsed.question, parsed.role, parsed.state_dir, authorized=True
                )
            )
            _print_demo(
                live_result,
                mode=mode,
                question=parsed.question if command == "ask" else parsed.text,
                output_format=parsed.format,
                color=parsed.color,
            )
            return int(live_result["status"] in {"FAIL", "DENIED", "BLOCKED"})
        model = None
        from .config import Settings

        settings = Settings.local() if mode == "local" else Settings(mode=mode)
        if mode == "azure":
            from .agent import FoundryAdapter

            model = FoundryAdapter(settings).invoke
        role = cast(str, parsed.role) if command == "ask" else "analyst"
        request = UserRequest(
            text=parsed.question if command == "ask" else parsed.text,
            subject=f"synthetic-{role}" if command == "ask" else "synthetic-requester",
            entitlements=frozenset() if role == "guest" else frozenset({"employee"}),
        )
        result = run(
            request,
            cast(Path, parsed.output),
            mode=mode,
            model=model,
            demo_approval=bool(parsed.demo_approval) if command == "demo" else False,
            settings=settings,
        )
        if command == "ask":
            result["identity_kind"] = "SYNTHETIC_ROLE_NOT_ENTRA_OBO"
            result["data_scope"] = (
                "SYNTHETIC_EQUIPMENT_POLICY_ONLY; not authoritative email retention guidance"
            )
        _print_demo(
            result,
            mode=mode,
            question=request.text,
            output_format=parsed.format,
            color=parsed.color,
        )
        return 0
    if command == "evaluate":
        if parsed.mode == "azure":
            from .config import Settings
            from .evaluation import FoundryEvaluator

            if parsed.data is None:
                raise ValueError("Azure evaluations require --data with synthetic JSONL")
            service = FoundryEvaluator(Settings(mode="azure"))
            service_result = service.evaluate(
                cast(Path, parsed.data),
                cast(Path, parsed.output),
                authorized=bool(parsed.authorize),
            )
            _print(service_result)
            return int(service_result["quality_outcome"] != "PASS")
        result = evaluate_scenarios()
        _print(result)
        return int(result["status"] != "PASS")
    if command == "observe":
        from .config import Settings
        from .observability import query_azure_traces

        observed = query_azure_traces(Settings(mode="azure"), cast(str, parsed.correlation_id))
        _print(observed)
        return int(observed["outcome"] != "PASS")
    if command == "gate":
        evidence = EvaluationEvidence.model_validate_json(
            cast(Path, parsed.evidence).read_text(encoding="utf-8")
        )
        decision = release_gate((reconcile(evidence),))
        _print(decision.model_dump())
        return int(decision.outcome != Outcome.PASS)
    if command in ("audit-verify", "audit"):
        path = cast(Path | None, parsed.path)
        if path is None:
            if parsed.expected_head is not None:
                raise ValueError("--expected-head requires an explicit audit path")
            if parsed.mode == "azure":
                from .presentation_live import saved_evidence

                manifest = saved_evidence(parsed.state_dir)
            else:
                from .presentation_runtime import latest_presentation

                manifest = latest_presentation(cast(Path, parsed.state_dir))
            scenes = cast(list[dict[str, object]], manifest["scenes"])
            results: list[dict[str, object]] = []
            for scene in scenes:
                broken = audit_failure_line(
                    Path(cast(str, scene["audit"])), cast(str, scene["audit_head"])
                )
                results.append(
                    {
                        "scene": scene.get("scene_id", scene.get("scene")),
                        "outcome": "PASS" if broken is None else "FAIL",
                    }
                )
            ok = bool(results) and all(item["outcome"] == "PASS" for item in results)
            _print({"outcome": "PASS" if ok else "FAIL", "audits": results})
            return int(not ok)
        broken_line = audit_failure_line(path, cast(str | None, parsed.expected_head))
        ok = broken_line is None
        _print({"outcome": "PASS" if ok else "FAIL", "first_broken_line": broken_line})
        return int(not ok)
    if command == "trace-check":
        path = cast(Path | None, parsed.trace)
        if path is None:
            paths = sorted(Path("artifacts").glob("*.spans.jsonl"), key=lambda p: p.stat().st_mtime)
            if not paths:
                _print({"outcome": "INSUFFICIENT_EVIDENCE", "reason": "Run make demo-local first"})
                return 1
            path = paths[-1]
        result = trace_completeness(REQUIRED_STAGES, read_stage_names(path))
        _print(result.model_dump())
        return int(result.outcome != Outcome.PASS)
    if command == "open":
        name = (
            "docs/index.html"
            if parsed.page == "docs"
            else ("APEX_Foundry_Security_Agent365_Nov12_2026.html")
        )
        path = Path(name).resolve(strict=True)
        _print({"path": str(path), "browser_opened": webbrowser.open(path.as_uri())})
        return 0
    if command == "agent":
        from .agent import FoundryAdapter
        from .config import Settings

        adapter = FoundryAdapter(Settings(mode="azure"))
        if parsed.operation == "deploy":
            _print(adapter.deploy(authorized=bool(parsed.authorize)))
        else:
            _print({"mode": "azure", "answer": adapter.invoke(cast(str, parsed.text))})
        return 0
    raise RuntimeError("Unreachable command")


def entrypoint() -> int:
    try:
        return main()
    except (
        AzureError,
        OpenAIError,
        ValidationError,
        PermissionError,
        ValueError,
        RuntimeError,
        OSError,
        TimeoutError,
    ) as error:
        _print(
            {"outcome": "FAIL", "error_type": type(error).__name__, "detail": "Operation failed"}
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(entrypoint())
