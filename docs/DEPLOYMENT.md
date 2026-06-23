# Backend Deployment — Railway

> Compute: **Railway** · Database: **Neon** (recommended) or Railway Postgres · TLS/proxy: Railway + Cloudflare
> Public API host: `https://api.half-half-man.com`

## 0. Prereqs (already in repo)
- `requirements.txt` (gunicorn, whitenoise, pinned)
- `railway.toml` (pre-deploy migrate+collectstatic, gunicorn start, healthcheck)
- `.python-version` = 3.12
- `settings.py` reads config from env (`DJANGO_*`, `DATABASE_URL`)

## 1. Database
**Neon (recommended — persistent free tier, decoupled from compute):**
1. Create a Neon project → copy the connection string or individual fields.
2. Neon requires TLS → set `DJANGO_DB_SSLMODE=require` (or include `?sslmode=require` in `DATABASE_URL`).

**Railway Postgres (one-vendor alternative):**
1. In the Railway project: **New → Database → PostgreSQL**.
2. Link the DB service to the web service — Railway injects `DATABASE_URL` automatically.
3. Use the **internal** host (`*.railway.internal`) when setting vars manually → omit `DJANGO_DB_SSLMODE`.

## 2. Create the Railway service
1. **New Project → Deploy from GitHub repo** → select the backend repo.
2. Railway auto-detects Python, reads `.python-version`, installs `requirements.txt`, and applies `railway.toml`.
3. **Settings → Networking → Generate Domain** → note the `*.up.railway.app` URL.
4. Healthcheck is configured in `railway.toml` → `/api/health/`.

## 3. Environment variables (Railway → service → Variables)

**With Railway Postgres (simplest):** link the database service — `DATABASE_URL` is set for you. Only add the Django vars below.

**With Neon or manual DB config:** set either `DATABASE_URL` *or* the `DJANGO_DB_*` block.

| Variable | Value |
|----------|-------|
| `DJANGO_SECRET_KEY` | generate: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `api.half-half-man.com,<your>.up.railway.app` |
| `DATABASE_URL` | *(auto when Railway Postgres is linked)* or Neon connection string |
| `DJANGO_DB_ENGINE` | `django.db.backends.postgresql` *(only if not using DATABASE_URL)* |
| `DJANGO_DB_NAME` | from DB provider |
| `DJANGO_DB_USER` | from DB provider |
| `DJANGO_DB_PASSWORD` | from DB provider |
| `DJANGO_DB_HOST` | from DB provider |
| `DJANGO_DB_PORT` | `5432` |
| `DJANGO_DB_SSLMODE` | `require` (Neon) / omit (Railway internal) |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `https://half-half-man.com,https://www.half-half-man.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://api.half-half-man.com` |

## 4. Deploy
- Push to the connected branch → Railway builds.
- Pre-deploy runs `migrate` + `collectstatic` (see `railway.toml`).
- Watch logs for a clean pre-deploy, then gunicorn boot.

## 5. Custom domain
1. Railway → Settings → Networking → **Custom Domain** → `api.half-half-man.com`.
2. Railway shows a CNAME target → in Cloudflare DNS add:
   `CNAME  api  → <target>.up.railway.app` (proxied **off** / grey-cloud first to validate TLS, then optionally on).

## 6. Verify
- `GET https://api.half-half-man.com/api/health/` → `{"status":"ok"}`
- `POST /api/auth/register/`, `/api/auth/login/` → tokens
- Django admin loads with static CSS (confirms WhiteNoise/collectstatic).
- Create admin: Railway shell → `python manage.py createsuperuser`

## 7. Post-deploy hardening (deliberate, not blocking)
- Flip `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES` to `IsAuthenticated`; confirm every public view (register/login/reset/health, future likes/comments) declares its own permission. Do this once likes/comments endpoints exist.
- `pip freeze > requirements.txt` inside the build env to lock exact versions.
- Configure SMTP for password-reset email (currently console backend).
