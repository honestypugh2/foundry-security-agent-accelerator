import runpy
import subprocess
from pathlib import Path
from unittest.mock import patch
from uuid import UUID


def test_source_scan_exempts_only_verified_public_builtin_roles(tmp_path: Path) -> None:
    scanner = runpy.run_path("scripts/scan_public.py")
    path = tmp_path / "example.bicep"
    output = subprocess.CompletedProcess(args=["git"], returncode=0, stdout=str(path).encode())
    with patch("subprocess.run", return_value=output):
        path.write_text(next(iter(scanner["PUBLIC_ROLE_IDS"])))
        assert scanner["main"]() == 0
        path.write_text(str(UUID(int=1)))
        assert scanner["main"]() == 1
        path.write_text(next(iter(scanner["PUBLIC_ROLE_IDS"])) + "\n" + str(UUID(int=2)))
        assert scanner["main"]() == 1
