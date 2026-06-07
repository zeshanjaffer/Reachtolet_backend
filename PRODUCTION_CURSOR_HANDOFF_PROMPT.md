# Production Cursor Handoff Prompt

Copy everything below the line and paste into Cursor on the production server/environment.

---

```
You are deploying the latest Reachtolet_backend changes to production. Here is what was added and modified in this release:

## NEW FEATURES ADDED

### 1. Locations app (`locations/`)
- New Django app with 4 models:
  - `State` (from states_capitals SQL — 50 US states with lat/long)
  - `City` (from states_cities SQL — 47,333 cities with coordinates)
  - `CityBoundary` (polygon JSON per city — 1,380 records)
  - `StateBoundary` (polygon JSON per state — 53 records)
- Registered in `core/settings.py` INSTALLED_APPS as `locations`
- Migrations: `locations/migrations/0001_initial.py`, `0002_state_latitude_state_longitude.py`

### 2. Location seeder command
- Command: `python manage.py seed_locations`
- Reads SQL dumps from project root:
  - `states-and-cities.sql`
  - `city-and-state-boundries.sql`
- Options:
  - `--flush` (default) — clear tables before import
  - `--only states|cities|city-boundaries|state-boundaries|all`
  - `--batch-size 1000` (chunk size, not a row limit)
  - `--no-flush` — append without clearing
- Verifies SQL dump counts match DB counts at end

### 3. Billboard availability API (NEW dedicated endpoints)
- `GET /api/billboards/{billboard_id}/availability/` — public, returns booked_dates
- `PUT /api/billboards/{billboard_id}/availability/` — media owner only, sets booked_dates
- Query params on GET: `?from=YYYY-MM-DD&to=YYYY-MM-DD` for month filter
- `unavailable_dates` removed from read responses — replaced with:
  ```json
  "availability": {
    "booked_dates": ["2026-10-05", "2026-10-06"],
    "total_booked": 2
  }
  ```
- `PUT/POST /api/billboards/{id}/` now IGNORES `unavailable_dates`, `booked_dates`, `availability` fields
- New files: `billboards/availability_utils.py`, route in `billboards/urls.py`

### 4. Public billboard list API changed (BREAKING for Flutter)
- `GET /api/billboards/` now returns MINIMAL data per item:
  ```json
  { "id": 1, "latitude": 40.71, "longitude": -74.0, "count": 1 }
  ```
- Full billboard data only via `GET /api/billboards/{id}/`
- Map clustering response also minimal (no nested full billboard in clusters)

### 5. POST response standardization
- New helper: `core/responses.py`
  - `action_response(message, status_code)` — minimal POST response
  - `auth_response(message, status_code, access, refresh, user)` — auth with tokens
- Most POST endpoints now return:
  ```json
  { "status_code": 200, "message": "Action completed successfully" }
  ```
- EXCEPTION — auth endpoints still return JWT tokens:
  - `POST /api/users/login/`
  - `POST /api/users/register/`
  - `POST /api/users/token/refresh/`
  - `POST /api/users/google-login/`

## FILES MODIFIED

- `core/settings.py` — added `locations` app
- `core/responses.py` — NEW standard response helpers
- `billboards/views.py` — availability view, minimal list, POST responses, strip dates from update
- `billboards/serializers.py` — `availability` object, removed `unavailable_dates` from fields
- `billboards/urls.py` — added availability route
- `billboards/clustering.py` — minimal cluster/marker response
- `users/views.py` — auth responses with tokens, minimal POST responses
- `users/urls.py` — CustomTokenRefreshView
- `notifications/views.py` — minimal POST responses

## NEW DOCUMENTATION FILES

- `BILLBOARD_AVAILABILITY_FLUTTER_GUIDE.md` — Flutter migration guide (share with mobile dev)
- `PRODUCTION_DEPLOYMENT_GUIDE.md` — step-by-step production deploy instructions
- `states-and-cities.sql` — location data dump (~9.5MB)
- `city-and-state-boundries.sql` — boundary data dump (~9.3MB)

## PRODUCTION DEPLOYMENT STEPS (run in order)

1. Pull latest: `git pull origin main`
2. Activate venv: `source env/bin/activate`
3. Install deps if needed: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Seed locations (first time): `python manage.py seed_locations --flush`
6. Restart app server (gunicorn/systemd)
7. Verify:
   - `curl https://PROD_URL/api/users/health/`
   - `curl https://PROD_URL/api/billboards/1/availability/`
   - Django shell: State=50, City=47333, CityBoundary=1380, StateBoundary=53

## IMPORTANT NOTES

- Do NOT set `DJANGO_USE_SQLITE=1` on production
- SQL dump files MUST be in project root for seeder to work
- Seeding may take 2-5 min on Supabase due to large boundary JSON
- If statement_timeout occurs, use smaller batch: `--batch-size 500` for cities, `--batch-size 50` for boundaries
- Flutter app MUST be updated — see BILLBOARD_AVAILABILITY_FLUTTER_GUIDE.md

Please execute the production deployment steps above and report any errors.
```
