"""mccp — Multi-cloud AI Control Plane add-on.

Shows how Microsoft Foundry (Control Plane), Azure API Management (AI gateway),
ServiceNow (registry / system of record), Okta (agent identity) and Datadog /
OpenTelemetry (observability) combine into one control plane for agents that run
in Azure, AWS and SaaS platforms.

Local mode is offline, deterministic and uses synthetic "Contoso Health" data only.
Everything it prints is labelled SIMULATED.
"""

__version__ = "0.1.0"

ORG_NAME = "Contoso Health"
ORG_PREFIX = "contoso"
