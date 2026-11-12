# Cross-cloud governance

Select one explicit cloud per execution. AzureCloud and AzureUSGovernment
configuration map authorities, audiences and permitted endpoint suffixes.
These routing checks do not certify product availability or data residency.

Never route government content to commercial evaluators, tracing collectors or
telemetry ingestion to make a lab pass. The service-evaluation adapter currently
rejects government mode pending verification.

Central reporting may use approved metadata/evidence contracts, but enforcement
stays with the selected cloud's native identities, policies and controls.
Cross-cloud data transfer is not implemented or authorized. Missing capabilities
require an explicit applicability decision or approved compensating control,
not automatic fallback. [Availability](feature-availability.md).
