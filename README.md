# CareGrid

**CareGrid - Unified Patient Signal Intelligence** is a lightweight desktop platform for normalizing, reviewing, and visualizing heterogeneous medical-device telemetry and log data.

> **Important:** CareGrid is currently prototype/research software. It is **not an FDA-cleared medical device**, not validated for primary clinical alarm annunciation, and must not replace approved bedside monitoring, nurse-call, or life-safety systems. Use de-identified/synthetic data for development unless your deployment has appropriate privacy, security, validation, and institutional approvals.

## What this release does

- Central nurse-station-style dashboard with live patient/bed rows, persistent side panels, alerts, device connections, and recent logs.
- Universal ingest for CSV, JSON/FHIR, HL7 text, EDF metadata, ODS/ODT, RTF/XML, DAT, SQLite DBs, TXT/LOG, and EDF.QRS/QRS-style text.
- Live adapters for Serial/USB, MQTT, HL7 v2 over MLLP/TCP, UDP syslog, optional IEEE 11073 SDC discovery, plus a built-in simulator.
- Append-only in-memory ingest with SQLite offload, per-patient history, snapshots, filtering, CSV export, and a localhost REST API.
- Threshold alarms with transition-based de-duplication, audible notification, alert history, acknowledge-all, and temporary silence controls.
- Patient detail trend plots and a simple browser dashboard powered by the local API.

## Quick start — Windows

Double-click `run_caregrid.bat`. It creates `.venv`, installs dependencies once, and starts CareGrid.

Manual setup:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python caregrid_app.py
```

For a fast functional test, start **Tools → Start Demo Simulator**. Six synthetic ICU rows will begin updating; one periodically transitions into a critical state so you can verify alerting.

## Device connections

Open the **Connections** panel and start/stop adapters. Configure ports/brokers in **Settings** first.

- **Serial/USB:** line-oriented device output via `pyserial`. Actual vendor framing/protocol must be configured per device manual.
- **MQTT:** JSON telemetry. Default subscription: `caregrid/+/+/vitals`.
- **HL7 v2:** MLLP/TCP listener, localhost by default, with basic PID/OBX vital extraction.
- **Syslog:** UDP listener, localhost by default.
- **IEEE 11073 SDC:** optional discovery layer; install `sdc11073` separately. Device-specific metric subscription still requires vendor/conformance testing.

## Local REST API

Default bind is **127.0.0.1:8765** for safety.

- `GET /health`
- `GET /patients`
- `GET /alerts`
- `GET /data?limit=200`

Do not expose this API to a hospital LAN or the public internet until authentication, TLS, authorization, audit controls, and a formal threat model are implemented.

## Browser dashboard

`web_dashboard/index.html` is a small optional display that queries the local REST API. Open it on the same workstation after CareGrid starts.

## Project layout

```text
caregrid_app.py        bootstrap / service wiring
core/                  normalization, storage, alerts, API, settings, snapshots
adapters/              file, serial, MQTT, HL7, SDC, syslog, simulator
ui/                    central dashboard and clinical panels
web_dashboard/         optional localhost browser display
tests/                  unit tests
```

## Real-device deployment roadmap

Before connecting CareGrid to live clinical workflows: build vendor-specific adapters from published/licensed interface specifications; test against simulators and isolated lab networks; implement authenticated users/roles, encryption, secure key handling, durable audit logs, fail-safe alarm behavior, device identity and patient association controls; perform IEC 62304-style software lifecycle documentation, risk management, cybersecurity assessment, verification/validation, and determine regulatory status with qualified clinical/regulatory counsel.

## License

MIT for the prototype source unless changed by the repository owner. Third-party device protocols, trademarks, and interface specifications remain subject to their respective licenses and contracts.
