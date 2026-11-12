"""Verify resource-level RBAC survives Bicep compilation."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.security
@pytest.mark.skipif(shutil.which("az") is None, reason="Azure CLI required for Bicep compilation")
def test_compiled_roles_keep_explicit_resource_scopes() -> None:
    root = Path(__file__).resolve().parents[1]
    compiled = subprocess.run(
        ["az", "bicep", "build", "--file", str(root / "infra/main.bicep"), "--stdout"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    roles = [
        resource
        for resource in json.loads(compiled.stdout)["resources"]
        if resource["type"] == "Microsoft.Authorization/roleAssignments"
    ]
    assert len(roles) == 5
    expected = {
        "foundryRole": "Microsoft.CognitiveServices/accounts",
        "searchServiceRole": "Microsoft.Search/searchServices",
        "searchDataRole": "Microsoft.Search/searchServices",
        "safetyRole": "Microsoft.CognitiveServices/accounts",
        "logsRole": "Microsoft.OperationalInsights/workspaces",
    }
    for role in roles:
        definition = role["properties"]["roleDefinitionId"]
        key = next(name for name in expected if f"variables('{name}')" in definition)
        assert role["scope"].startswith(f"[resourceId('{expected[key]}', ")
        assert "principalId" in role["properties"]
