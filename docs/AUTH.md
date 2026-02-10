# Authentication API (JWT)

## Overview

- **Login identifier:** email (no username in API)
- **Tokens:** access (short-lived) + refresh (long-lived); refresh can be blacklisted on logout
- **Password reset:** email with signed link/token (no DB token table)

## Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Register; body: `email`, `password`, `password_confirm`, optional `first_name`, `last_name`. Returns user + tokens. |
| POST | `/api/auth/login/` | No | Login; body: `email`, `password`. Returns `access`, `refresh`, `user`. |
| POST | `/api/auth/token/refresh/` | No | Body: `refresh`. Returns new `access` (and new `refresh` if rotation on). |
| POST | `/api/auth/logout/` | No | Body: `refresh`. Blacklists the refresh token. |
| GET | `/api/auth/me/` | Bearer | Current user profile. |
| PATCH | `/api/auth/me/` | Bearer | Update profile (e.g. `first_name`, `last_name`). |
| POST | `/api/auth/password/change/` | Bearer | Body: `old_password`, `new_password`. |
| POST | `/api/auth/password/reset/` | No | Body: `email`. Sends reset email (or no-op if email unknown). |
| POST | `/api/auth/password/reset/confirm/` | No | Body: `token`, `new_password`. Token from reset email. |

## Usage

- **Register:** `POST /api/auth/register/` with JSON body → store `access` and `refresh`.
- **Authenticated requests:** Header `Authorization: Bearer <access>`.
- **When access expires:** `POST /api/auth/token/refresh/` with `{"refresh": "<refresh>"}` → use new `access` (and new `refresh` if returned).
- **Logout:** `POST /api/auth/logout/` with `{"refresh": "<refresh>"}` so that refresh token cannot be used again.

## Settings (in `settings.py` / `local_settings.py`)

- **JWT:** `SIMPLE_JWT` (e.g. `ACCESS_TOKEN_LIFETIME`, `REFRESH_TOKEN_LIFETIME`, `ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`).
- **Email:** For password reset in production set `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, and SMTP settings (e.g. in `local_settings.py`).
- **CORS:** When `DEBUG` is False, set `CORS_ALLOWED_ORIGINS` (e.g. in `local_settings.py`).

## Database (custom User)

If you see a migration error like “admin.0001_initial is applied before its dependency accounts.0001_initial”, the database was created with Django’s default user. To use the custom User (email as login):

1. **PostgreSQL:** Drop and recreate the database, then run:
   ```bash
   py manage.py migrate
   ```
2. Or drop all tables in the DB and run `migrate` again.
