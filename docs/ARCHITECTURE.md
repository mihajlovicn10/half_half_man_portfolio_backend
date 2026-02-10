# Architecture: Clean / Hexagonal + Domain / Application / Infrastructure

**Chosen approach: Option B** — Django apps stay at repo root; we add `domain/` and `application/` packages. Infrastructure remains inside the existing `accounts` app (persistence + HTTP). This is **code organization only**: API contracts and backend behaviour stay the same.

---

## 1. Target Principles

| Principle | Meaning in this project |
|-----------|-------------------------|
| **Domain** | Business rules and concepts only. No Django, no DB, no HTTP. Pure Python. |
| **Application** | Use cases (orchestration). Depend on domain and on **ports** (interfaces). No framework or I/O details. |
| **Infrastructure** | Concrete implementations: Django ORM, DRF, email, file storage. Implements **ports** defined by the application layer. |
| **Hexagonal** | Core (domain + application) is the “hexagon”; everything else (DB, HTTP, email) are adapters behind ports. |

**Dependency rule:** Dependencies point **inward**. Domain has no dependencies. Application depends only on domain + port interfaces. Infrastructure depends on application (implements ports) and domain (e.g. maps entities to/from persistence).

---

## 2. Package Layout

```
half_half_man_portfolio_backend/
├── domain/
│   └── accounts/
│       ├── entities.py
│       └── exceptions.py
├── application/
│   └── accounts/
│       ├── ports/
│       ├── use_cases/
│       └── dtos.py
├── accounts/                      # Single Django app = persistence + http adapters
│   ├── models.py                  # Adapter: persistence
│   ├── repositories.py            # Implements application.accounts.ports
│   ├── views.py                   # Adapter: HTTP, delegates to use cases
│   ├── serializers.py
│   ├── urls.py
│   └── migrations/
├── half_half_man_portfolio_backend/
├── manage.py
└── ...
```

- **Domain** and **application** are separate packages; no Django or I/O there.
- **Infrastructure** lives entirely in the `accounts` Django app: models, repositories, views, serializers. No separate `infrastructure/` package.

---

## 3. Layer Responsibilities and Examples

### 3.1 Domain (`domain/`)

- **Entities:** Behaviour and identity. Example: `User` with `id`, `email`, `password_hash`, and domain methods (e.g. `change_password(old, new)` that validates and updates hash).
- **Value objects (optional):** e.g. `Email` (validation, normalization).
- **Domain exceptions:** e.g. `UserAlreadyExists`, `InvalidCredentials`.
- **Rule:** No imports from Django, DRF, or any I/O. Only standard library / pure Python.

Example (conceptual):

```python
# domain/accounts/entities.py
class User:
    def __init__(self, id, email, password_hash, first_name="", last_name="", is_active=True):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        ...
```

### 3.2 Application (`application/`)

- **Ports (interfaces):** What the core needs from the outside world, e.g. “save user”, “find user by email”, “issue tokens”, “send email”. Defined as abstract base classes or protocols.
- **Use cases:** One (or a few) use case per file. Each use case:
  - Takes simple inputs (DTOs or primitives).
  - Uses **ports** (injected or resolved) to load/save entities and call side effects.
  - Returns simple outputs or raises domain/application exceptions.
- **Rule:** No Django models, no DRF, no SQL. Only domain + ports.

Example (conceptual):

```python
# application/accounts/ports/user_repository.py
class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...
    def save(self, user: User) -> User: ...

# application/accounts/use_cases/register_user.py
class RegisterUser:
    def __init__(self, user_repo: UserRepository, token_service: TokenService): ...
    def execute(self, email: str, password: str, ...) -> RegisterResult: ...
```

### 3.3 Infrastructure (`accounts/`)

- **Persistence:** Django models (mapping to DB), **repositories** that implement application ports (e.g. `UserRepository` implemented by `DjangoUserRepository` using `accounts.models.User`). Map domain entities ↔ ORM models.
- **HTTP:** DRF views and serializers. Views: parse request → call one use case → map result to response. Serializers: validation + request/response shape only.
- **Other adapters:** Email sender (implements “send email” port), file storage, etc.
- **Rule:** All framework and I/O details stay here. Application and domain stay framework-agnostic.

Example (conceptual):

```python
# accounts/repositories.py
class DjangoUserRepository:
    def get_by_email(self, email: str) -> domain.accounts.entities.User | None:
        model = accounts.models.User.objects.filter(email=email).first()
        return self._to_entity(model) if model else None
```

---

## 4. Migration Path (Incremental)

Goal: reach Clean/Hexagonal + domain/application/infrastructure **without a big-bang rewrite**.

### Phase 1: Introduce domain and application (no Django app move)

1. **Add packages (no Django dependency):**
   - `domain/accounts/` – `entities.py`, `exceptions.py` (and optional `value_objects.py`).
   - `application/accounts/ports/` – e.g. `user_repository.py`, `token_service.py`, `email_sender.py`.
   - `application/accounts/use_cases/` – one module per flow: `register_user`, `login_user`, `change_password`, `reset_password`.

2. **Define domain User (and any value objects)** in `domain/accounts/`. Keep it independent of Django (id, email, password_hash, etc.).

3. **Implement use cases** to depend only on domain and ports. Use cases receive port implementations via constructor (dependency injection) or a small container.

4. **Keep current `accounts` app as-is** for the moment (models, views, serializers). No structural change yet.

### Phase 2: Implement ports in infrastructure (accounts app)

1. **Repositories:** In `accounts/repositories.py` (or `accounts/adapters/`), implement the application ports:
   - `DjangoUserRepository` implementing `UserRepository`: get_by_email, get_by_id, save (map Django User ↔ domain User).
2. **Token service:** Implement port that issues/validates JWT (wrap simplejwt in an adapter).
3. **Email sender:** Implement port that sends email (wrap Django `send_mail`).
4. **Wire use cases** in the app: instantiate use cases with these adapters (e.g. in a small “composition root” or factory inside `accounts`).

### Phase 3: Thin HTTP layer (views call use cases)

1. **Refactor views** so they:
   - Parse and validate input (serializers).
   - Call **one use case** (e.g. `RegisterUser().execute(...)`).
   - Map use case result (or exception) to HTTP response.
2. **Keep serializers** for request/response only; move “business” validation into domain/use cases where appropriate.
3. **Keep Django User model** as the persistence model; repositories do the mapping to/from domain entities.

### Phase 4: New features follow the same pattern

- For each new context (e.g. blog, courses, commerce):
  - Add `domain/<context>/`, `application/<context>/ports/` and `use_cases/`, then infrastructure (Django app).
  - Reuse the same flow: domain → application (ports + use cases) → infrastructure (repositories, HTTP, email, etc.).

---

## 5. Dependency Injection and Wiring

- **Option 1 (simple):** A small “composition root” in the app that creates repositories and use cases once (e.g. in `accounts/services.py` or `accounts/use_cases.py`), and views import and call these instances.
- **Option 2 (explicit):** Per-request or per-view injection (e.g. factory that builds use case with request-scoped DB session). Useful when you need request in an adapter.
- **Option 3 (container):** Use a lightweight container (e.g. `dependency-injector` or custom registry) to resolve ports and use cases. Overkill until you have many contexts.

Starting with **Option 1** is enough: one module in `accounts` that instantiates adapters and use cases; views call into that.

---

## 6. Testing Alignment

- **Domain:** Unit tests with no Django/DB. Test entities and domain logic only.
- **Application:** Unit tests for use cases with **mocked/fake ports** (in-memory repository, fake token service, fake email). No Django.
- **Infrastructure:** Integration tests for repositories (Django DB), and API tests for views (DRF test client) that hit real use cases with test DB or fakes.

This keeps the core fast and framework-independent and still validates the full stack in infrastructure tests.

---

## 7. Summary Checklist

| Decision | Choice |
|----------|--------|
| Repo / API | ✅ Separate repo, API-first (already done) |
| Layout | Option B: Django apps at root; `domain/` and `application/` added; infrastructure in `accounts/` |
| Domain | Pure Python in `domain/<context>/` (entities, value objects, exceptions) |
| Application | Use cases + ports in `application/<context>/` (no framework) |
| Infrastructure | Persistence + HTTP inside `accounts/` (models, repositories, views, serializers) |
| Migration | Phase 1: add domain + application; Phase 2: implement ports in `accounts`; Phase 3: views call use cases |
| Behaviour | Code organization only; API and backend behaviour unchanged |

Next concrete step: implement **Phase 1** for `accounts` (domain entities + ports + one or two use cases), then **Phase 2** (one repository and one use case wired and called from a single view) to validate the flow before refactoring the rest of auth.
