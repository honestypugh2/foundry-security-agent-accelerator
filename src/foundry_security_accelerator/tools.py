from .contracts import ToolRequest, ToolResult


class ToolRegistry:
    """Closed registry: no writer, shell, delegation, URL or model-controlled dispatch."""

    def execute(self, request: ToolRequest, roles: frozenset[str]) -> ToolResult:
        if request.name != "policy_lookup":
            raise PermissionError("TOOL_NOT_ALLOWLISTED")
        if "employee" not in roles:
            raise PermissionError("TOOL_ROLE_REQUIRED")
        if request.arguments:
            raise ValueError("policy_lookup accepts no arguments")
        return ToolResult(
            name=request.name, status="READ_ONLY", content="Limit: 1500; approval required."
        )
