# Standalone operation

CareGrid runs as a local research/prototype application. It does not require a Groundstate account, StaffRoot, Groundstate Admin Center, or an organization identity provider.

Local telemetry ingestion, normalization, dashboards, storage, exports, thresholds, and alerts remain application-owned. A future organization integration may supply optional user identity or role assertions, but it must be disabled by default, provider-neutral, and unable to block access to locally stored data during an outage.

Clinical deployments require their own validated authentication, authorization, audit, privacy, device-association, alarm, recovery, and regulatory controls. Connecting CareGrid to an organization directory would not make the prototype clinically validated.
