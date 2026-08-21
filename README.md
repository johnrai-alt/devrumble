# SadakSathi Backend (Django)

Django/DRF port of the original Node.js/Express backend — live traffic
congestion, crowd-sourced incident reporting, route optimization, and
analytics.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in real values
docker compose up -d    # starts Postgres+PostGIS and Redis locally

python manage.py migrate
python manage.py runserver 0.0.0.0:8000        # HTTP/DRF only

# For WebSockets (traffic tile subscriptions) use an ASGI server instead:
uvicorn sadaksathi.asgi:application --reload --port 8000

# Background jobs (equivalent of the node-cron workers started in server.js):
celery -A sadaksathi worker -l info
celery -A sadaksathi beat -l info
```

## Project structure

```
sadaksathi/          # project config: settings, urls, asgi/wsgi, celery app+beat schedule
accounts/            # auth module — fully ported from src/modules/auth/*
  models.py            # users, otp_codes, refresh_tokens tables
  tokens.py            # JWT access tokens + hashed opaque refresh tokens
  otp.py               # OTP generate/hash/expiry/send
  authentication.py    # DRF auth class — port of middleware/auth.js requireAuth
  permissions.py       # IsVerifiedUser — port of requireVerifiedUser
  throttling.py        # fixed-window throttles — exact port of rateLimiter.js
  exceptions.py        # AppError + handler — port of errorHandler.js
  views.py             # all 9 endpoints, ported line-for-line from auth.service.js
  urls.py
incidents/           # stub — same TODOs as incidents.controller/service/repository.js
  tasks.py              # Celery task — port of workers/incidentExpiryWorker.js
traffic/             # stub — same TODOs as traffic.controller/service/repository.js
  consumers.py          # Channels WebSocket consumer — port of sockets/index.js + trafficNamespace.js
  routing.py            # websocket_urlpatterns for asgi.py
  tasks.py              # Celery task — port of workers/ingestWorker.js
routing/             # stub — same TODOs as routing.controller/service/repository.js
analytics/           # stub — same TODOs as analytics.controller/service/repository.js
  tasks.py              # Celery task — port of workers/aggregationWorker.js
```

## Mapping from the original Express project

| Express (Node)                                  | Django                                              |
|--------------------------------------------------|------------------------------------------------------|
| `src/app.js` route mounting                       | `sadaksathi/urls.py`                                  |
| `src/server.js` (http server + sockets + workers)| `sadaksathi/asgi.py` + `sadaksathi/celery.py`         |
| `src/config/db.js` (pg Pool)                      | `settings.DATABASES` (Django's own connection pooling)|
| `src/config/redis.js`                             | `settings.CACHES` / `CHANNEL_LAYERS` / `CELERY_BROKER_URL` |
| `src/config/env.js`                               | top of `settings.py` (same fail-fast required-vars check) |
| `src/middleware/auth.js`                          | `accounts/authentication.py` + `accounts/permissions.py` |
| `src/middleware/errorHandler.js`                  | `accounts/exceptions.py`                              |
| `src/middleware/rateLimiter.js`                   | `accounts/throttling.py`                              |
| `src/utils/jwt.js`                                 | `accounts/tokens.py`                                  |
| `src/utils/otp.js`                                 | `accounts/otp.py`                                     |
| `*.routes.js` / `*.controller.js` / `*.service.js` | `<app>/urls.py` / `<app>/views.py` (DRF collapses controller+service into class-based views) |
| `*.repository.js` (raw SQL via pg Pool)            | Django ORM (`<app>/models.py`) where implemented; raw SQL via `django.db.connection.cursor()` where the original also used raw SQL (workers) |
| `src/sockets/index.js` + `trafficNamespace.js`     | `traffic/consumers.py` (Django Channels; note: plain WebSocket, not wire-compatible with Socket.io — see file docstring) |
| `src/workers/*.js` (node-cron)                     | `<app>/tasks.py` (Celery tasks) + schedule in `sadaksathi/celery.py` (Celery Beat) |

## Status (updated to match the UI/UX mockup: Main Map View → Blog Feed → User Profile → Past Activity Dashboard)

- [x] **Auth module** — register, login, phone OTP, guest access, upgrade-guest,
      refresh, logout, plus `GET/PATCH /auth/me` (powers the User Profile screen)
- [x] **Incidents module** — powers the Blog Feed ("events" tab). `Incident` model
      (title, description, category, photo, lat/lng, status, credibility score),
      `GET/POST /incidents/`, `GET /incidents/<id>/`, `POST /incidents/<id>/vote`
      (requires a verified, non-guest user), photo upload via `MEDIA_ROOT`.
      `expire_stale_incidents` Celery task now runs against the real model.
- [x] **Traffic module** — powers the Main Map View. `TrafficReading` model,
      `GET /traffic/?min_lat=&min_lng=&max_lat=&max_lng=` returns the latest
      reading per segment for the map viewport. The Channels WebSocket
      consumer (`traffic/consumers.py`) still needs a producer to call
      `group_send` when new readings land — `poll_traffic_provider` is
      still a stub pending a real provider API key.
- [x] **Analytics module** — powers the Past Activity Dashboard ("reports" tab).
      `CongestionHourlyAgg` model (written by the existing `aggregate_past_hour`
      Celery task), single `GET /analytics/dashboard` endpoint combining the
      congestion-breakdown donut, hourly trend line, and recent incident
      report snapshots.
- [x] **Search** — `GET /search?q=` searches incident title/description
      (bottom-nav "search" tab). Assumption: incidents-only for now: extend
      to traffic/routing once those have more queryable data.
- [ ] **Routing module** — still fully stubbed. Not clearly represented in
      the current mockup (no route-planning screen shown) — clarify with
      the team whether it lives inside the Map View or is a separate screen
      before implementing OSRM/Valhalla integration.

## Notes for the team

- **Database schema**: table/column names in `accounts/models.py` match what
  `auth.repository.js` assumed (`users`, `otp_codes`, `refresh_tokens`).
  Any schema changes need a corresponding Django migration.
- **Frontend contract unchanged**: all endpoints still return JSON; auth
  endpoints still return `{ user, accessToken, refreshToken }`. Access
  token still goes in `Authorization: Bearer <token>` on every request.
  WebSocket connections authenticate via a `?token=<access token>` query
  param on `ws://.../ws/traffic/` (same access token as REST calls) —
  the closest equivalent to Socket.io's `socket.handshake.auth.token`
  since raw WebSockets have no handshake payload of their own.
- **PostGIS**: `docker-compose.yml` still uses the `postgis/postgis` image;
  Django's DB engine here is the plain `django.db.backends.postgresql`
  since no module currently does any spatial ORM querying (traffic/routing
  are still stubs). Switch to `django.contrib.gis.db.backends.postgis`
  and add `django.contrib.gis` to `INSTALLED_APPS` once those modules
  need actual geo queries.
