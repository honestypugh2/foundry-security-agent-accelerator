"""Shared test helpers: make `src/` importable and give each test an artifacts dir inside the repo."""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mccp.config import Settings  # noqa: E402


def make_settings(mode: str = "local") -> Settings:
    s = Settings(mode=mode)
    s.artifacts_dir = REPO / "artifacts" / "mccp-test" / uuid.uuid4().hex[:8]
    return s


def cleanup(settings: Settings) -> None:
    shutil.rmtree(settings.artifacts_dir, ignore_errors=True)
    parent = settings.artifacts_dir.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
