# Production Deployment Guide

Steps to deploy the latest backend changes to production (Supabase Postgres).

---

## What was added in this release

1. **`locations` app** — states, cities, city boundaries, state boundaries tables
2. **`seed_locations` command** — imports data from SQL dump files
3. **Billboard availability API** — dedicated GET/PUT endpoints (no longer via update API)
4. **Public billboard list** — minimal map response (`id`, `latitude`, `longitude`, `count`)
5. **POST response standardization** — most POSTs return `status_code` + `message`
6. **Auth endpoints** — login/register/refresh still return JWT tokens in body

---

## Prerequisites

- SSH or shell access to production server
- Python virtualenv activated (`env` or `.venv`)
- Environment variables set (no `DJANGO_USE_SQLITE=1` on production)
- SQL dump files present in project root:
  - `states-and-cities.sql`
  - `city-and-state-boundries.sql`

---

## Step 1: Pull latest code

```bash
cd /path/to/Reachtolet_backend
git pull origin main
```

---

## Step 2: Install dependencies (if needed)

```bash
source env/bin/activate   # Linux
# or: .\env\Scripts\Activate.ps1   # Windows

pip install -r requirements.txt
```

---

## Step 3: Run migrations

This creates the new `locations` tables (`State`, `City`, `CityBoundary`, `StateBoundary`).

```bash
python manage.py migrate
```

Expected output includes:
```
Applying locations.0001_initial... OK
Applying locations.0002_state_latitude_state_longitude... OK
```

**Note:** Billboard availability uses existing `unavailable_dates` column — no new migration needed for that feature.

---

## Step 4: Seed location data (first time only)

Imports all states, cities, and boundaries from SQL dumps.

```bash
python manage.py seed_locations --flush
```

This will:
1. Clear existing location tables
2. Import **50 states**
3. Import **47,333 cities**
4. Import **1,380 city boundaries**
5. Import **53 state boundaries**
6. Verify counts match SQL dumps

**Expected duration:** ~2–5 minutes on Postgres (large JSON boundaries).

**Seed one dataset at a time (optional):**
```bash
python manage.py seed_locations --only states --flush
python manage.py seed_locations --only cities --flush
python manage.py seed_locations --only city-boundaries --flush
python manage.py seed_locations --only state-boundaries --flush
```

**Re-run without clearing (append — not recommended):**
```bash
python manage.py seed_locations --no-flush
```

---

## Step 5: Restart application server

```bash
# Example with gunicorn + systemd
sudo systemctl restart reachtolet

# Or if using Procfile / manual gunicorn
pkill -f gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

---

## Step 6: Verify deployment

### Health check
```bash
curl https://YOUR_PRODUCTION_URL/api/users/health/
```

### Locations seeded
```bash
python manage.py shell -c "
from locations.models import State, City, CityBoundary, StateBoundary
print('States:', State.objects.count())
print('Cities:', City.objects.count())
print('City boundaries:', CityBoundary.objects.count())
print('State boundaries:', StateBoundary.objects.count())
"
```

Expected:
```
States: 50
Cities: 47333
City boundaries: 1380
State boundaries: 53
```

### New availability API
```bash
curl https://YOUR_PRODUCTION_URL/api/billboards/1/availability/
```

### Public billboard list (minimal)
```bash
curl https://YOUR_PRODUCTION_URL/api/billboards/
```

---

## Step 7: Update Flutter app

Share `BILLBOARD_AVAILABILITY_FLUTTER_GUIDE.md` with the Flutter developer.

Key breaking changes:
- Stop sending `unavailable_dates` in billboard update
- Use `GET/PUT /api/billboards/{id}/availability/`
- Map list returns minimal markers only
- Read `availability.booked_dates` instead of `unavailable_dates`

---

## Production checklist

| Step | Command | Done? |
|------|---------|-------|
| Pull code | `git pull origin main` | ☐ |
| Activate venv | `source env/bin/activate` | ☐ |
| Migrate | `python manage.py migrate` | ☐ |
| Seed locations | `python manage.py seed_locations --flush` | ☐ |
| Restart server | `systemctl restart ...` | ☐ |
| Verify health | `curl .../api/users/health/` | ☐ |
| Verify locations count | Django shell counts | ☐ |
| Deploy Flutter update | See Flutter guide | ☐ |

---

## Troubleshooting

### `statement_timeout` during seed on Supabase

Seed in smaller batches:
```bash
python manage.py seed_locations --only cities --flush --batch-size 500
python manage.py seed_locations --only city-boundaries --flush --batch-size 50
```

### SQL files not found
Ensure these exist in project root:
- `states-and-cities.sql`
- `city-and-state-boundries.sql`

### Seed verification failed
Re-run with flush:
```bash
python manage.py seed_locations --flush
```

### Old Flutter app breaks on map
Flutter must update to use minimal list response + detail fetch by id.

---

## Do NOT run on production

- `DJANGO_USE_SQLITE=1` — production uses Postgres/Supabase
- `python manage.py flush` — deletes all data
- Committing or using local `db.sqlite3`
