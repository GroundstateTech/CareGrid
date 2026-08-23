# Security Policy

CareGrid is open-source prototype/research software under GPL-3.0-or-later. It is **not** an FDA-cleared medical device and is not validated as a primary clinical alarm, bedside-monitoring, nurse-call, or life-safety system.

## Reporting security issues

Please do not publish exploit details, credentials, real patient information, or other sensitive deployment data in a public issue. Report enough information privately to the repository owner/maintainers to reproduce and assess the issue before coordinated public disclosure.

Useful reports include the affected version/commit, environment, reproduction steps using synthetic/de-identified data, expected vs observed behavior, impact, and a proposed mitigation when available.

## Data handling

Do not commit PHI, patient identifiers, production logs, credentials, private keys, clinical exports, local databases, or institution-specific configuration. Development and CI should use synthetic or properly de-identified test data.

The repository ignores local settings, the runtime SQLite database, snapshots, logs, virtual environments, and build output. Contributors should still inspect staged changes before every commit.

## Network boundary

Local APIs/listeners are development features. Do not expose CareGrid to a hospital LAN or the public internet without appropriate authentication, authorization, TLS, key management, audit controls, network segmentation, threat modeling, and institutional approval.

## Clinical safety

A software-security fix is not automatically a clinical-safety validation. Changes affecting alarms, thresholds, patient association, device identity, message parsing, timing, persistence, or failover require explicit verification appropriate to the intended use.

## Supported security posture

Security fixes are prioritized on the current `main` branch. Pre-release builds may change rapidly and do not carry a production-support guarantee.
