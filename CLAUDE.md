# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Koreon Tech — Integrated Monitoring Platform**

A multi-module security and monitoring platform built around Intelbras hardware, designed to evolve into a **multi-tenant SaaS** where multiple companies share the same infrastructure with full data isolation.

**Current state: single-tenant, local deployment. Multitenancy is a planned architectural evolution — every design decision must not block it.**

### Services

| Service | Stack | Port | Status |
|---------|-------|------|--------|
| `frontend/` | Angular 18 (standalone) | 4200 | Active |
| `backend/` | Python FastAPI | 8000 | Active |
| `backendPerm/` | Java Spring Boot 4 / Java 21 | 8001 | Skeleton only |

---

## Running the Project

### Frontend
```bash
cd frontend && npm install && ng serve
```

### Backend Python — local (SQLite)
```bash
cd backend && pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
The alarm TCP server starts automatically on port `9009` (set `ALARM_TCP_PORT` env var to override).

### Backend Python — Docker (PostgreSQL)
```bash
docker-compose up --build    # db on 5432, backend on 8000
```

### Backend Java
```bash
cd backendPerm
./mvnw spring-boot:run       # needs PostgreSQL
./mvnw test
./mvnw package
```

---

## Backend Python — Architecture

### Entry point
`backend/main.py` — registers all routers, mounts static files, starts the alarm TCP thread and the camera polling thread.

### Routing structure (domain-based)
```
backend/
  main.py                      ← FastAPI app, thread startup
  crud.py                      ← all DB operations (one file, grouped by domain)
  schemas.py                   ← all Pydantic schemas (one file, grouped by domain)
  database/
    core.py                    ← SQLAlchemy engine (SQLite local / PostgreSQL via DATABASE_URL)
    models.py                  ← all ORM models
  routes/
    persons.py                 → /persons
    visitors.py                → /visitors
    alarms.py                  → /alarms
    access.py                  → /access
    gates.py                   → /gates
  adapters/
    cameras/                   ← camera protocol adapters
    alarm/                     ← alarm protocol adapters
    gate/                      ← gate/relay adapters
```

### Database models (all in `models.py`)

**Camera module**
- `Camera` — ip_address, camera_type (`bronze`/`onvif`/`intelbras`/`mibo`)
- `Event` — event_type, event_data (JSON text), face_image_path, camera_id

**People & Visitors**
- `Person` — name, cpf, department, access_level, face_encoding (JSON float array), photo_path, is_active
- `Visitor` — name, host, destination, valid_until, status (`pending`/`approved`/`denied`/`expired`), person_id (optional FK)

**Alarms**
- `AlarmCentral` — name, model, ip, port (default 9009), protocol (`contact_id`), password (used as account-number for Contact ID identification)
- `AlarmZone` — central_id, zone_number, name, zone_type, is_bypassed, status
- `AlarmEvent` — central_id, zone_id, event_type, qualifier, raw_data (hex)

**Access Control**
- `AccessDevice` — name, device_type (`catraca`/`leitor_rfid`/`controle_acesso`/`cancela`), ip, location
- `AccessLog` — person_id, device_id, result (`granted`/`denied`/`unknown`), method (`facial`/`rfid`/`pin`/`manual`), confidence (float), direction (`in`/`out`)

**Gates**
- `Gate` — name, brand (`ppa`/`intelbras`/`generic`), ip, pulse_time, status

> **Multitenancy note:** when multitenancy is implemented, every model above gets a `tenant_id` FK. All CRUD functions and all routes will receive `tenant_id` extracted from the JWT. No data ever crosses tenant boundaries.

### Camera adapters (`adapters/`)

| Class | Protocol | `get_events()` behavior |
|-------|----------|------------------------|
| `BronzeCameraAdapter` | ICMP ping | returns `[]` (online check only) |
| `OnvifAdapter` | ONVIF PullPoint | parses FaceRecognition, PeopleCounter topics natively |
| `IntelbrasAdapter` | HTTP CGI `log.cgi` | polls DVR/NVR log API every 10 s |
| `MiboDriver` | HTTP CGI | PTZ + audio only; `get_events()` returns `[]` |

`MiboDriver` does **not** extend `CameraAdapter` (uses `username`/`password` vs base `user`/`password`). This is a known inconsistency — do not "fix" it silently without updating callers.

Camera polling thread in `main.py` runs every 10 s, calls `get_events()` on every registered camera, and writes results to `Event` table.

### Alarm adapters (`adapters/alarm/`)

- `contact_id_decoder.py` — 100+ event codes, ASCII + BCD parsers; covers Intelbras AMT, DSC, Paradox, Bosch, JFL, Honeywell, Ademco
- `tcp_receiver.py` — `AlarmTCPReceiver`: multi-client TCP server (one thread per central). Identifies central by: remote IP → `AlarmCentral.password` as account number → single active central fallback. Persists `AlarmEvent`, updates `AlarmZone.status`. Detects Contact ID vs SIA DC-09 and sends correct ACK.
- `intelbras_http_adapter.py` — for networked AMT models (AMT 8000 IP, AMT 4010 Smart with Ethernet): arm/disarm/bypass via HTTP CGI.

The TCP receiver starts as a daemon thread in `main.py` on `ALARM_TCP_PORT` (default 9009).

### Gate adapters (`adapters/gate/`)

`factory.py` reads `Gate.brand` and returns the right adapter:

| Brand value | Adapter | Strategy |
|-------------|---------|----------|
| `ppa`, `peccinin` | `PPAAdapter` | 3 CGI endpoints + JSON POST fallback |
| `intelbras`, `dahua` | `IntelbrasRelayAdapter` | AlarmOut CGI → PTZ relay → relay.cgi |
| anything else | `GenericHTTPGateAdapter` | 12 known endpoints tried in order (Tasmota, Sonoff, ESP, Control iD, Hikvision ISAPI, …) |

Always call `get_gate_adapter(gate_orm_object)` — never instantiate adapters directly in routes.

---

## AI Pipeline — Design Principle

**The AI must function regardless of camera hardware.** Old analog cameras on DVRs, cheap IP cameras without smart features — all must benefit from the same AI capabilities.

Two paths, same output:

```
Path A — Camera has native AI (Intelbras, Hikvision, ONVIF smart)
  Camera firmware → ONVIF events (FaceDetection, PeopleCounter) → OnvifAdapter.get_events() → Event table

Path B — Camera has no AI (any RTSP source, Bronze cameras, old DVR channels)
  RTSP stream → server-side AI thread (1 FPS) → YOLOv8 + InsightFace + DeepFace → Event table
```

Both paths write identical `Event` records. The frontend and downstream logic are unaware of which path ran.

The server-side AI thread reuses the same RTSP connection logic as the streaming endpoint, but processes at a much lower frame rate to avoid CPU saturation. Camera capability detection: if ONVIF PullPoint returns face/people events, disable the local AI thread for that camera to avoid double-counting.

---

## Access Control + Gate Integration Flow

Access control and gate triggering are part of the **same event-driven flow**, not separate modules. The PPA IoT relay (and equivalent Intelbras/generic relays) is the physical execution layer of an access decision:

```
AI detects face in frame
        │
        ▼
Person identified? ──────────────────────────────────────────────────┐
        │ YES                                                         │ NO
        ▼                                                             ▼
Check AccessDevice rules                                    Check Visitor table
(time window, access_level,                                 (valid_until, approved status)
 is_active)                                                          │
        │                                                    Found? ─┼─ No → alert operators
        │ GRANTED          DENIED                                YES  │
        ▼                    ▼                                        ▼
Trigger Gate via          Log AccessLog              Notify guarita via WebSocket
GateAdapter.trigger()     (denied, method)           → operator approves/denies
        │                                                            │
        ▼                                                    APPROVED ▼
Log AccessLog                                               Trigger Gate
(granted, method,                                           Log AccessLog
 confidence)                                                (granted, visitor)
```

`AccessDevice` will carry an optional `gate_id` FK pointing to the `Gate` to trigger on access granted. This FK is not in the model yet — it is added in Phase 4 when the full flow is implemented.

---

## Frontend (Angular 18)

All components are standalone (no NgModules). `ApiService` (`src/app/api.service.ts`) is the single HTTP client, pointing to `http://localhost:8000`.

| Route | Component | Status |
|-------|-----------|--------|
| `/` | HomeHubComponent | Done |
| `/dashboard` | DashboardComponent | Done — VMS grid, PTZ, polling |
| `/hub` | SecurityHubComponent | Done |
| `/camera/:id` | CameraDetailComponent | Done |
| `/camera-add`, `/camera-edit/:id` | CameraAddComponent | Done |
| `/logs` | LogsComponent | Done |
| `/gestao-acessos` | AccessManagementComponent | **UI done, calls `alert()` — needs real API** |
| `/gestao-portoes` | GateManagementComponent | **UI done, calls `alert()` — needs real API** |
| `/gestao-alarmes` | AlarmManagementComponent | **UI done, calls `alert()` — needs real API** |

---

## Backend Java (Spring Boot — `backendPerm/`)

**Purpose:** authentication, multi-tenant user management, WebSocket event broker.

Already declared in `pom.xml`: Spring Security, Spring Data JPA, Flyway (PostgreSQL migrations), Spring Integration, WebSocket/STOMP, Lombok.

**What exists:** only `IntelbrasKoreonApplication.java` (empty main). No controllers, no entities, no Flyway migrations, no security config.

**Planned port:** 8001.

**Planned responsibilities:**
- JWT issuance with `tenant_id` + `user_id` + `roles` claims
- Tenant provisioning (super-admin only)
- User CRUD per tenant
- Role/permission management per tenant
- WebSocket/STOMP broker for real-time events to the Angular frontend

Keep Java — do not replace with Node. The security/WebSocket stack is the right fit for this service's role.

---

## Key Constraints

- **CORS:** Python backend allows `http://localhost:4200` only. Update for each deployment environment.
- **event_data field:** stores JSON as TEXT string. Always `json.dumps()` before saving, `JSON.parse()` in Angular.
- **face_images/:** served as static files at `/faces/<filename>`. Created automatically on startup.
- **SQLite in dev:** `create_all()` does not add new columns to existing tables. Delete `dashboard_data.db` after adding columns to models and restart.
- **Alarm central identification:** `AlarmCentral.password` field doubles as the Contact ID account number for matching. Document this convention when registering centrals.
