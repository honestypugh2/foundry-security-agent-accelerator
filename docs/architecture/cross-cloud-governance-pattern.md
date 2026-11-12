# Report centrally; enforce natively

The application separates four responsibilities: Azure resource controls,
Foundry workload execution, Entra identity enforcement, and applicable Agent 365
lifecycle/activity integration. Defender and Purview retain their own signal and
policy scopes. No cross-cloud "god credential" or model-dispatched control plane
is implemented.

Portable contracts, deterministic policy, approval validation, DRY_RUN receipts,
audit reconciliation and OpenTelemetry evidence are shared. Credential authority,
resource audiences, endpoints, licensing and product availability are selected
and verified per cloud. Azure errors terminate the Azure run.

The local fallback starts an explicitly labeled synthetic run; it does not
replay cloud data or assert equivalent governance coverage. See
[cloud boundaries](../clouds/cross-cloud-governance.md).
