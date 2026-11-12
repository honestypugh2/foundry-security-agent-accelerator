"""Verify that the public gate rejects unsafe evidence, not merely a command error."""

import json
import subprocess


def main() -> None:
    result = subprocess.run(
        ["fsa", "gate", "data/evaluation/unsafe-execution.json"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 1:
        raise RuntimeError("Unsafe evidence did not produce the required gate exit")
    decision = json.loads(result.stdout)
    if decision.get("outcome") != "FAIL" or "CRITICAL_FAILURE" not in decision.get("reasons", []):
        raise RuntimeError("An unrelated CLI error is not proof of unsafe-release rejection")
    print("PASS: confirmed unsafe execution blocks release despite a safe evaluator verdict")


if __name__ == "__main__":
    main()
