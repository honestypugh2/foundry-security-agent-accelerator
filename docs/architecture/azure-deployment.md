# Deployment boundaries

See the [participant live lab](../participant-lab/azure-live-lab.md) for executable
Bash/PowerShell guidance. Use existing infrastructure when possible.

The Bicep uses stable `Microsoft.CognitiveServices` `2025-06-01` account/project
schemas; local compilation validates schema/types, not region or service success.
No hardcoded tenant, subscription, resource group, model or private endpoint is
included. The template creates managed identities and disables local-key auth.
Network isolation is NOT_IMPLEMENTED in this teaching template.

Both entries use **new Foundry**, not classic: AI Services with
`allowProjectManagement: true` and a child project resource. The optional live
module adds the GA model, Search, Content Safety and resource-scoped operator
roles; [subscription entry](../../infra/live.bicep) creates an explicitly approved
isolated group with monitoring. Search has a separate regional parameter for
reviewed capacity recovery. See the [Azure lab](../participant-lab/azure-live-lab.md).
The templates are tenant-neutral workshop references, not evidence of deployment
success or a production private-network design. Validate your own environment
separately and keep tenant-specific deployment evidence private.

Verify compiled and actual RBAC scopes, not just role names. All five lab grants
must remain resource-scoped. The regression in
[test_infra](../../tests/test_infra.py) compiles Bicep and asserts those scopes;
it skips without Azure CLI, while `make validate` independently requires Bicep.

`azure.yaml` describes infrastructure only; it is not evidence that an agent was
deployed or published. Agent creation is a separate explicitly authorized SDK
operation. Publishing for Microsoft 365/Agent 365 is separate again.

`azure provision` without authorization returns NOT_EXECUTED. Even with the flag,
the wrapper refuses until parameters/what-if have been reviewed via the documented
CLI path. `azure cleanup` is a plan/manual boundary, not a destructive group delete.

For production, implement scoped private endpoints, DNS, approved egress, managed
identity RBAC, protected environments and GitHub OIDC. Do not deploy from forked
PRs or put client secrets in CI. There is intentionally no automatic deployment
workflow with ambient credentials.
