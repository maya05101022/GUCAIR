# Deployment guide — Render + Neon PostgreSQL

GUCAIR is designed to run on Render's free web-service tier with a Neon PostgreSQL
database. SQLite is used only for local development.

## 1. Prerequisites

- GitHub account with the GUCAIR repository pushed.
- Render account connected to GitHub.
- Neon account with a project and database created.
- Permission to create a Render web service (or the repository owner performs these steps).

## 2. Create the Neon database

1. Sign in to <https://neon.tech> and create a project, for example `gucair`.
2. Copy the **pooled** connection string. It resembles:
   `postgresql://USER:PASSWORD@ep-xxxx-pooler.REGION.aws.neon.tech/neondb?sslmode=require`
3. Keep `sslmode=require` in the URL. `dj-database-url` passes it to psycopg.
4. Do not commit the connection string.

## 3. Create the Render service

### Option A — Blueprint (recommended)

1. In Render, choose **New → Blueprint**.
2. Connect the GitHub repository. Render reads `render.yaml`.
3. Supply the secret environment variables when prompted:
   - `DATABASE_URL` — the Neon connection string.
   - `ADMIN_USERNAME` — production administrator username.
   - `ADMIN_PASSWORD` — strong production password (12+ characters).
   - `ADMIN_EMAIL` — administrator email.
4. Apply the Blueprint and wait for the first deploy.

### Option B — Manual web service

- Runtime: **Python**
- Build command: `./build.sh`
- Start command:
  `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`
- Health check path: `/health/`
- Environment variables:

| Key | Value |
| --- | --- |
| `PYTHON_VERSION` | `3.13.5` |
| `DEBUG` | `False` |
| `SECRET_KEY` | generated long random value |
| `DATABASE_URL` | Neon PostgreSQL URL with `sslmode=require` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
| `ADMIN_USERNAME` | production administrator username |
| `ADMIN_PASSWORD` | strong production password |
| `ADMIN_EMAIL` | administrator email |
| `SEED_DEMO` | `True` for labelled demonstration records, otherwise `False` |

`RENDER_EXTERNAL_HOSTNAME` is supplied by Render. `config/settings.py` automatically adds
it to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

## 4. Build sequence

`build.sh` performs:

1. `pip install -r requirements.txt`
2. `python manage.py collectstatic --noinput`
3. `python manage.py wait_for_db` (retries while Neon wakes)
4. `python manage.py migrate --noinput`
5. `python manage.py seed_data` or `seed_data --demo`
6. `python manage.py create_admin` (skips if admin variables are unset)

The build is idempotent: seeding uses `update_or_create`, and the admin command safely
updates an existing account.

## 5. Post-deployment verification

Replace `<service>` with the actual Render hostname.

1. `https://<service>.onrender.com/health/` returns HTTP 200 with
   `{"status": "ok", "database": "connected", ...}`.
2. Landing page shows consortium statistics from the production database.
3. `https://<service>.onrender.com/analytics/api/summary/` returns JSON.
4. Sign in as the production administrator.
5. Register a test representative, approve the institution, submit an assessment, and
   confirm the result, history and analytics update.
6. Check `/django-admin/` loads and is password-protected.
7. Confirm `http://` redirects to `https://`.
8. Confirm the README live URL exactly matches the verified address.

## 6. Common issues

| Symptom | Check |
| --- | --- |
| DisallowedHost | `ALLOWED_HOSTS` includes `.onrender.com`; redeploy after changing |
| CSRF verification failed | `CSRF_TRUSTED_ORIGINS` includes `https://<service>.onrender.com` |
| 500 on first request | Build logs: migrations, missing env vars, Neon SSL |
| Static files missing | Build ran `collectstatic`; WhiteNoise middleware enabled |
| Database connection error | Neon project active, pooled URL, `sslmode=require` |
| Admin login fails | `ADMIN_USERNAME`/`ADMIN_PASSWORD` set before build; check build log |
| Free instance slow | Render free services spin down after inactivity |

## 7. Security checklist

- [ ] `DEBUG=False`
- [ ] Unique production `SECRET_KEY`
- [ ] `DATABASE_URL` stored only in Render environment settings
- [ ] `ALLOWED_HOSTS` restricted to the deployed hostname
- [ ] `CSRF_TRUSTED_ORIGINS` uses HTTPS only
- [ ] Strong administrator password
- [ ] HTTPS redirect and secure cookies active
- [ ] Local `.env` and `db.sqlite3` not committed
- [ ] Demo institutions labelled if `SEED_DEMO=True`
