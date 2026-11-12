"""Conservative source-tree scan. Reports categories and paths, never matching values."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

PUBLIC_ROLE_IDS = frozenset(
    {
        "53ca6127-db72-4b80-b1b0-d745d6d5456d",  # Foundry User
        "7ca78c08-252a-4471-8644-bb5ff32d4ba0",  # Search Service Contributor
        "8ebe5a00-799e-43f5-93ac-243d3dce84a7",  # Search Index Data Contributor
        "a97b65f3-24c7-4388-baec-2e87135dc908",  # Cognitive Services User
        "73c42c96-874c-492b-b04d-ab87d138a893",  # Log Analytics Reader
    }
)

RULES = {
    "credential": re.compile(
        r"(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|"
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
    ),
    "tenant-or-subscription-guid": re.compile(
        r"\b[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}\b"
    ),
    "internal-url": re.compile(r"https?://[^\s\"<>]*(?:sharepoint\.com|microsoft-my\.)"),
    "private-filesystem-path": re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/"),
}


def main(manifest: Path | None = None) -> int:
    if manifest is None:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=True,
            capture_output=True,
        )
        names = set(result.stdout.decode().split("\0")) - {""}
    else:
        entries = json.loads(manifest.read_text(encoding="utf-8"))["files"]
        names = {entry["path"] for entry in entries}
        if not names:
            raise ValueError("Release manifest must not be empty")
        for name in names:
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or not path.is_file():
                raise ValueError("Invalid or missing release-manifest file")
        if any(
            hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest() != entry["sha256"]
            for entry in entries
        ):
            raise ValueError("Release candidate differs from its manifest")
    failures: list[str] = []
    for name in names:
        path = Path(name)
        if not path.is_file():
            continue
        # Offline decks embed fonts; retain a bounded limit and scan their full text.
        maximum_size = 8_000_000 if path.suffix == ".html" else 2_000_000
        if path.stat().st_size > maximum_size:
            failures.append(f"unexpected-size: {name}")
            continue
        if path.suffix in {".png", ".jpg", ".svg", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8")
        for category, pattern in RULES.items():
            matches = pattern.findall(text)
            if category == "tenant-or-subscription-guid":
                matches = [value for value in matches if value.lower() not in PUBLIC_ROLE_IDS]
            if matches:
                failures.append(f"{category}: {name}")
    for finding in failures:
        print(finding)
    print(
        "FAIL"
        if failures
        else "PASS: source patterns; manual confidentiality review still required"
    )
    return int(bool(failures))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    raise SystemExit(main(parser.parse_args().manifest))
