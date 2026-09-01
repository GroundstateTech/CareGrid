# CareGrid

**CareGrid - Unified Patient Signal Intelligence** is a lightweight desktop platform for normalizing, reviewing, and visualizing heterogeneous medical-device telemetry and log data.

> **Important:** CareGrid is prototype/research software. It is **not an FDA-cleared medical device**, not validated for primary clinical alarm annunciation, and must not replace approved bedside monitoring, nurse-call, or life-safety systems. Use de-identified/synthetic data for development unless a deployment has appropriate privacy, security, validation, and institutional approvals.

## Open-source philosophy

CareGrid is licensed under **GPL-3.0-or-later**. Community research and engineering contributions are welcome. The GPL keeps distributed covered derivatives open while copyright remains with the applicable copyright holders. Groundstate/CareGrid names, logos, and official-project identity are separate from the source-code license.

See `LICENSE` and `CONTRIBUTING.md`.

## What this release does

- Central nurse-station-style dashboard with live patient/bed rows, alerts, device connections, and recent logs.
- Ingest for CSV, JSON/FHIR, HL7 text, EDF metadata, ODS/ODT, RTF/XML, DAT, SQLite DBs, TXT/LOG, and QRS-style text.
- Live adapters for Serial/USB, MQTT, HL7 v2 over MLLP/TCP, UDP syslog, optional IEEE 11073 SDC discovery, plus simulator.
- SQLite offload, per-patient history, snapshots, filtering, CSV export, and localhost REST API.
- Threshold alarms with de-duplication, notification, history, acknowledgement, and silence controls.
- Patient trend plots and a simple local browser dashboard.

## Quick start — Windows

Double-click `run_caregrid.bat`, or manually:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python caregrid_app.py
```

For a functional test, start **Tools → Start Demo Simulator**.

## Device connections

Configure ports/brokers in Settings, then use the Connections panel. Device-specific protocols require appropriate vendor specifications and validation.

## Local REST API

Default bind is **127.0.0.1:8765**. Do not expose it to a hospital LAN or public internet until authentication, TLS, authorization, audit controls, and a formal threat model are implemented.

## Project layout

```text
caregrid_app.py        bootstrap / service wiring
core/                  normalization, storage, alerts, API, settings, snapshots
adapters/              file, serial, MQTT, HL7, SDC, syslog, simulator
ui/                    central dashboard and clinical panels
web_dashboard/         optional localhost browser display
tests/                 unit tests
```

## Real-device deployment roadmap

Before live clinical use, CareGrid needs vendor-specific validated adapters, isolated testing, authentication/roles, encryption, secure key handling, durable audit logs, fail-safe alarm behavior, device/patient association controls, lifecycle/risk/cybersecurity documentation, verification/validation, and appropriate regulatory review.

## Validation

Install the development requirements into an isolated environment, then run the
regression suite:

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m compileall -q caregrid_app.py core adapters ui
python -m pytest -q
```

## Contributing

Community pull requests are welcome. See `CONTRIBUTING.md`. Never commit PHI, credentials, proprietary device specifications, or data you are not authorized to redistribute.

## Support

See `SUPPORT.md` for optional Patreon and PayPal support. Support does not purchase ownership, equity, IP rights, or special licensing rights.

## License

**GPL-3.0-or-later** for repository source code unless a file states otherwise. Third-party device protocols, trademarks, assets, dependencies, and interface specifications remain subject to their respective rights and licenses.
