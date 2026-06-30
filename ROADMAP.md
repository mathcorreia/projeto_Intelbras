# Koreon Tech — Product Roadmap

## Vision

Integrated security and monitoring platform that starts as a single-tenant on-premises system and evolves into a **multi-tenant SaaS** — multiple companies sharing the same infrastructure with complete data isolation, accessible from any browser with no local installation required.

**Core differentiator:** the AI layer must function with any camera hardware, from IP cameras bought yesterday to analog cameras connected to a DVR bought a decade ago. The intelligence lives in the platform, not in the device.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Angular Frontend                      │
│   Dashboard · Alarmes · Acesso · Portões · Guarita · Admin  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP / WebSocket
         ┌───────────┴──────────────┐
         │                          │
┌────────▼────────┐      ┌──────────▼─────────┐
│  Python FastAPI  │      │  Java Spring Boot   │
│  (port 8000)     │      │  (port 8001)        │
│                  │      │                     │
│  - Cameras       │      │  - Auth / JWT       │
│  - Streaming     │      │  - Tenants          │
│  - AI Pipeline   │◄────►│  - Users / Roles    │
│  - Alarms        │      │  - WebSocket broker  │
│  - Access        │      │  - Audit log        │
│  - Gates         │      │                     │
│  - Guarita       │      └─────────────────────┘
└────────┬─────────┘
         │
┌────────▼──────────────────────────────────────┐
│               Hardware Layer                   │
│  Cameras RTSP · Intelbras AMT · PPA IoT relay  │
│  DSC · Paradox · JFL · Hikvision · Control iD  │
└────────────────────────────────────────────────┘
```

---

## Completed

### Phase 0 — Camera Base
- RTSP video streaming (MJPEG over HTTP, sub-stream → main-stream fallback)
- Camera CRUD + event polling thread (every 10 s)
- Adapters: Bronze (ping), ONVIF PullPoint, Intelbras CGI, Mibo CGI
- PTZ control, bidirectional audio, night vision (Mibo/Intelbras)
- Dashboard VMS grid (1/4/9/16/25/36/49/64 cameras), fullscreen mode

### Phase 1 — Data Foundation
New models: `Person`, `Visitor`, `AlarmCentral`, `AlarmZone`, `AlarmEvent`, `AccessDevice`, `AccessLog`, `Gate`

Domain-based routing: `/persons`, `/visitors`, `/alarms`, `/access`, `/gates`

Full CRUD for all 8 new entities. SQLite local / PostgreSQL via Docker.

### Phase 2 — Hardware Integration
**Alarms (any brand, any model):**
- Contact ID decoder: 100+ event codes, ASCII + BCD parsers
- Multi-client TCP receiver on port 9009 — handles Intelbras AMT, DSC, Paradox, JFL, Bosch, Honeywell, Ademco simultaneously
- Intelbras HTTP adapter for networked AMT models (arm/disarm/bypass via CGI)
- Persists events and updates zone statuses automatically

**Gates (any brand, any model):**
- PPA adapter (Contatto Wi-Fi / Peccinin) — 3 fallback strategies
- Intelbras relay adapter (XAL modules, cameras with relay output) — 3 fallback strategies
- Generic HTTP adapter (Tasmota, Sonoff, ESP, Control iD, Hikvision ISAPI) — 12 endpoints tried in order
- Factory pattern: `brand` field determines adapter at runtime

---

## Planned

### Phase 3 — AI Pipeline (server-side, hardware-agnostic)
**Goal:** every camera in the system benefits from the same AI regardless of age or model.

**People counting**
- Background thread per camera, pulls RTSP frames at ~1 FPS
- YOLOv8 (`ultralytics`) detects and counts persons in configurable zones
- Suppressed for cameras that already report native ONVIF PeopleCounter events

**Facial recognition**
- InsightFace generates embeddings; stored as JSON in `Person.face_encoding`
- Per-frame comparison against all active persons with face encodings
- Threshold: configurable confidence (default 0.6)
- Suppressed for cameras that already report native ONVIF FaceRecognition events

**Emotion / behavior analysis**
- DeepFace infers dominant emotion (neutral, happy, angry, fearful, surprised, disgusted, sad)
- Stored as `event_data` JSON on the resulting `Event` record
- Used as a soft signal in the access control flow (e.g., distressed person flagged)

**Unknown person flow**
- Face not matched to any `Person` → check `Visitor` table by time validity
- Not a visitor → push WebSocket alert to guarita operators
- Guarita approves → trigger gate; denies → log + optional alarm

**New libs to add to `requirements.txt`:**
```
ultralytics        # YOLOv8
insightface        # facial recognition (replaces face_recognition for performance)
deepface           # emotion detection
onnxruntime        # InsightFace inference backend
```

**Server-side AI is always the fallback. Camera native AI is always preferred when available.**

---

### Phase 4 — Access Control + Gate Integration
**Goal:** face/RFID recognition directly triggers the physical gate/door.

**Model change:** `AccessDevice` gains `gate_id` (FK → `Gate`, nullable). This links a reader/controller to the physical actuator it controls.

**Access flow:**
```
AI identifies person → check AccessDevice rules → GRANTED → trigger Gate → log AccessLog
                                                → DENIED  → log AccessLog → alert
AI sees unknown face → check Visitor → VISITOR  → notify guarita → await → trigger Gate
                                     → UNKNOWN  → alert operators
```

**Rule engine (in `AccessDevice`):**
- `access_level` filter: person's level must meet device's minimum level
- Time window: allowed hours/days (stored as JSON rule in `AccessDevice`)
- `Person.is_active` must be true
- `Visitor.valid_until` must be in the future and status must be `approved`

**Frontend:** connect `AccessManagementComponent` to real API; add facial enrollment screen (capture photo from live camera stream → generate embedding → save to `Person`).

---

### Phase 5 — Guarita Module
**Goal:** a dedicated operator view for managing visitors and responding to unknown person alerts.

**New route:** `/guarita`

**Features:**
- Real-time feed of unknown person detections (face photo + camera + timestamp)
- Visitor pre-registration (name, CPF, photo, host, destination, valid window)
- Operator approve/deny flow → triggers gate or triggers alarm
- Visitor check-in / check-out log
- Pre-scheduled visitors automatically approved on arrival without operator action

**WebSocket:** guarita page subscribes to a WebSocket channel for real-time alerts (implemented in Java Spring Boot WebSocket broker).

---

### Phase 6 — Java backendPerm — Auth & Tenant Management
**Goal:** production-grade authentication and the foundation for multitenancy.

**Entities:**
- `Tenant` — id, name, slug, plan (`starter`/`pro`/`enterprise`), is_active, created_at
- `User` — id, tenant_id, name, email, password_hash, role, is_active
- `Role` — `SUPER_ADMIN` (Koreon internal), `TENANT_ADMIN`, `OPERATOR`, `GUARD`, `VIEWER`

**Flyway migrations** for all entities.

**JWT claims:** `{ sub: user_id, tenant_id, roles[], exp }`

**Spring Security config:**
- `/auth/login` → returns JWT
- `/auth/refresh` → refresh token rotation
- All other routes require valid JWT
- `SUPER_ADMIN` can impersonate any tenant
- Each role maps to endpoint-level `@PreAuthorize` annotations

**Python FastAPI integration:**
- FastAPI middleware validates JWT from `Authorization: Bearer` header
- Extracts `tenant_id` and injects it into every request context
- All CRUD functions receive `tenant_id` as a mandatory parameter
- Row-level filtering on every query: `WHERE tenant_id = :tenant_id`

---

### Phase 7 — Multitenancy Foundation
**Goal:** full data isolation. Each company sees only its own cameras, persons, alarms, gates, visitors, access logs.

**Database changes:** add `tenant_id` column to all models:
`Camera`, `Event`, `Person`, `Visitor`, `AlarmCentral`, `AlarmZone`, `AlarmEvent`, `AccessDevice`, `AccessLog`, `Gate`

**Python middleware:**
```python
# Dependency injected into every route
async def get_tenant(token: str = Depends(oauth2_scheme)) -> int:
    payload = verify_jwt(token)          # validates with Java backendPerm public key
    return payload["tenant_id"]
```

All CRUD functions signature changes from:
```python
def get_cameras(db: Session) → list[Camera]
```
to:
```python
def get_cameras(db: Session, tenant_id: int) → list[Camera]
```

**PostgreSQL Row Level Security** as a second layer of protection (belt and suspenders):
```sql
ALTER TABLE cameras ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON cameras
    USING (tenant_id = current_setting('app.current_tenant')::int);
```

**Alarm TCP receiver:** each frame decoded includes the Contact ID account number. Account numbers are registered per tenant in `AlarmCentral.password`. The receiver queries `get_alarm_centrals()` across all tenants but always writes events scoped to the matching central's `tenant_id`.

**AI threads:** one thread pool per tenant's cameras — events are always tagged with `tenant_id`.

---

### Phase 8 — WebSocket Real-Time Events
**Goal:** eliminate the 2-second polling loop in the Angular dashboard. Push events instantly.

**Java Spring Boot WebSocket/STOMP broker:**
- Topic `/topic/tenant/{tenant_id}/events` — all events for a tenant
- Topic `/topic/tenant/{tenant_id}/alarms` — alarm events only
- Topic `/topic/tenant/{tenant_id}/access` — access log events
- Topic `/topic/tenant/{tenant_id}/guarita` — unknown person alerts

**Python backend** publishes to the Java broker via HTTP POST or internal queue whenever a new `Event`, `AlarmEvent`, or `AccessLog` is created.

**Angular** subscribes to STOMP topics on connect. Polling subscriptions in `DashboardComponent` and `LogsComponent` are removed.

---

### Phase 9 — Frontend Completion
**Goal:** all pages connected to real APIs and real-time data.

| Page | What to connect |
|------|-----------------|
| `AlarmManagementComponent` | Real `AlarmCentral` + `AlarmZone` CRUD; `AlarmEvent` feed via WebSocket; arm/disarm buttons |
| `AccessManagementComponent` | Real `Person` + `AccessLog`; facial enrollment (capture from camera stream); `AccessDevice` CRUD |
| `GateManagementComponent` | Real `Gate` CRUD; `POST /gates/{id}/trigger`; status polling |
| New: `GuaritaComponent` | Visitor queue; approve/deny; real-time unknown face alerts |
| New: `TenantAdminComponent` | User management, roles, API keys (SUPER_ADMIN only) |
| `DashboardComponent` | Switch polling → WebSocket; AI overlay (person count, face tags, emotion badges) |

---

### Phase 10 — Production Hardening
- Complete `docker-compose.yml` with all three services + PostgreSQL + Redis (for WebSocket scaling)
- SSL/TLS termination (Nginx reverse proxy)
- Backup strategy for face images and SQLite migration to PostgreSQL
- Horizontal scaling consideration: AI threads are CPU-bound — separate `ai-worker` container
- Monitoring: health endpoints (`/health`) on both backends, Prometheus metrics
- Rate limiting on auth endpoints (Spring Security + Bucket4j)
- Audit log: every action that changes data is logged with user_id + tenant_id + timestamp

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Camera AI — new cameras | Use native ONVIF events | Zero CPU cost on server; most accurate (runs in dedicated DSP) |
| Camera AI — old cameras | Server-side YOLOv8 + InsightFace | Any RTSP source works; models run on CPU (no GPU required for small deployments) |
| Face embeddings storage | JSON in DB (`Person.face_encoding`) | Simple; searchable; easily replaced with a vector DB (pgvector) when scale demands |
| Alarm protocol | Contact ID TCP (primary) + HTTP CGI (secondary) | Contact ID covers 95%+ of Brazilian market; HTTP CGI covers Intelbras networked models |
| Gate protocol | Brand-specific CGI + generic HTTP fallback | PPA and Intelbras dominate Brazilian market; generic fallback covers everything else |
| Auth service | Java Spring Boot | Enterprise-grade security stack; WebSocket/STOMP broker built-in; Flyway for migrations |
| Multitenancy isolation | App-level `tenant_id` filter + PostgreSQL RLS | Defense in depth; RLS is the last line |
| Deployment | Docker Compose (dev/small) → Kubernetes (scale) | Start simple; migrate when tenant count justifies it |

---

## Folder Structure (target state)

```
projeto_Intelbras/
├── frontend/                    # Angular 18
├── backend/                     # Python FastAPI
│   ├── main.py
│   ├── crud.py
│   ├── schemas.py
│   ├── database/
│   │   ├── core.py
│   │   └── models.py
│   ├── routes/
│   │   ├── persons.py
│   │   ├── visitors.py
│   │   ├── alarms.py
│   │   ├── access.py
│   │   ├── gates.py
│   │   └── guarita.py          ← Phase 5
│   ├── adapters/
│   │   ├── alarm/
│   │   │   ├── contact_id_decoder.py
│   │   │   ├── tcp_receiver.py
│   │   │   └── intelbras_http_adapter.py
│   │   └── gate/
│   │       ├── factory.py
│   │       ├── ppa_adapter.py
│   │       ├── intelbras_relay_adapter.py
│   │       └── generic_adapter.py
│   └── ai/                     ← Phase 3
│       ├── pipeline.py          # orchestrates threads per camera
│       ├── people_counter.py    # YOLOv8
│       ├── face_recognizer.py   # InsightFace
│       └── emotion_detector.py  # DeepFace
├── backendPerm/                 # Java Spring Boot 4
│   └── src/main/java/com/intelbrasKoreon/
│       ├── config/              # SecurityConfig, WebSocketConfig
│       ├── auth/                # JwtService, AuthController
│       ├── tenant/              # Tenant entity + controller
│       ├── user/                # User entity + controller
│       └── websocket/           # EventBroker
├── docker-compose.yml
├── CLAUDE.md
└── ROADMAP.md
```
