# Egress security

Local mode does not construct remote providers or exporters and tests block socket
connections and DefaultAzureCredential token acquisition. Azure mode validates
cloud-specific HTTPS service endpoints and never silently falls back.

The reusable egress allowlist is not a host firewall. Production must also enforce
network boundaries, private endpoints where appropriate, DNS/proxy controls,
workload identity, credential restrictions and approved destinations.

OTLP permits HTTPS or explicit loopback HTTP; local mode rejects even configured
OTLP export. Enable an exporter only after data-handling review. Service evaluators
submit synthetic query/response/context with explicit authorization.

The teaching Bicep template is not a private-network production architecture.
Do not claim network isolation from suffix validation or compilation alone.
