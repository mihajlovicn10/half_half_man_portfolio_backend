# Half Half Man — Portfolio Backend

Backend API for the Half Half Man portfolio site. Built with Django and Django REST Framework, following **API-first** and **Clean / Hexagonal** architecture (Option B).

## Stack

- **Django 5.x** — web framework  
- **Django REST Framework** — API  
- **djangorestframework-simplejwt** — JWT auth (access + refresh, blacklist on logout)  
- **PostgreSQL** — database (config in `local_settings.py`, gitignored)  
- **django-cors-headers** — CORS for frontend

## Architecture

- **Domain** (`domain/accounts/`) — entities and exceptions, no framework deps  
- **Application** (`application/accounts/`) — ports (interfaces) and use cases  
- **Infrastructure** (`accounts/`) — Django app: models, adapters (repositories, JWT, email, reset token), thin views, serializers  

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full plan and layout.

## Implemented

### Authentication (JWT)

- **Register** — `POST /api/auth/register/` (email, password, optional name) → user + tokens  
- **Login** — `POST /api/auth/login/` (email, password) → access, refresh, user  
- **Refresh** — `POST /api/auth/token/refresh/` (refresh token) → new access  
- **Logout** — `POST /api/auth/logout/` (refresh token) → blacklist  
- **Me** — `GET/PATCH /api/auth/me/` (Bearer) — current user profile  
- **Password change** — `POST /api/auth/password/change/` (Bearer, old + new password)  
- **Password reset** — `POST /api/auth/password/reset/` (email) and `POST /api/auth/password/reset/confirm/` (token + new password)

Details and examples: [docs/AUTH.md](docs/AUTH.md).

## Setup

1. **Clone and enter the repo**
   ```bash
   git clone https://github.com/mihajlovicn10/half_half_man_portfolio_backend.git
   cd half_half_man_portfolio_backend
   ```

2. **Create a virtualenv and install dependencies**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. **Configure local settings (gitignored)**  
   Copy `half_half_man_portfolio_backend/local_settings.example.py` to `half_half_man_portfolio_backend/local_settings.py` and set your `SECRET_KEY` and `DATABASES` (PostgreSQL). See the example file for the expected structure.

4. **Run migrations**
   ```bash
   py manage.py migrate
   py manage.py createsuperuser   # optional, for /admin/
   ```

5. **Run the server**
   ```bash
   py manage.py runserver
   ```
   API base: `http://127.0.0.1:8000/api/auth/`.

## Tests

```bash
py manage.py test accounts
```

All auth flows are covered (register, login, refresh, logout, me, password change, password reset).

## Docs

- [docs/AUTH.md](docs/AUTH.md) — Auth API overview and usage  
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Clean/Hexagonal layout and migration path  

## Planned

- Blog, courses, ecommerce, and other features will follow the same domain → application → infrastructure pattern.
