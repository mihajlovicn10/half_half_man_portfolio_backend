# RBAC Plan: Roles and Two-Layer Authorization

Role-Based Access Control is a **business concept**: roles influence **use cases** (application layer), not only **endpoints** (transport layer). The application layer is the source of truth for “who can do what”; the transport layer is a first line of defence.

---

## 1. Objectives

| # | Objective | Notes |
|---|-----------|--------|
| O1 | Define four business roles with clear hierarchy | Guest → User → Buyer → Client (increasing privilege) |
| O2 | **Transport layer:** restrict which role can call which endpoint | DRF permission classes / decorators; fast 401/403 at the gate |
| O3 | **Application layer:** restrict which role can execute which use case or action | Inside use cases or a dedicated “authorizer”; business rules live here |
| O4 | Single source of role data | Domain + persistence (e.g. `User.role`); no duplication of role semantics |
| O5 | Easy to extend | New use cases and endpoints get role checks in both layers without scattering logic |

---

## 2. Role Definitions (Business Concept)

Roles are **ordered by privilege**. Higher roles imply the capabilities of lower roles unless we explicitly restrict an action to a specific role.

| Role | Description | Typical state |
|------|-------------|---------------|
| **Guest** | Unauthenticated or anonymous. Can browse public content, register, login, use password reset. | No user record, or special “anonymous” token. |
| **User** | Registered and authenticated. Can manage own profile, change password, access protected content. | Has account; `role = USER`. |
| **Buyer** | User who has made at least one purchase (or explicitly promoted). Can request refunds, see order history, use buyer-only features. | `role = BUYER`. |
| **Client** | Business relationship (e.g. ongoing work, retainer). May have different refund/contract rights than a one-off Buyer. | `role = CLIENT`. |

**Hierarchy (for “at least” checks):**  
`Guest < User < Buyer < Client`

- A **Client** is also a User and can do everything a Buyer can, unless we define an action as “Buyer only” or “Client only”.
- A **Buyer** is also a User.
- **Guest** is the base (unauthenticated or minimal identity).

---

## 3. Two-Layer Model

### 3.1 Transport Layer (Who Can Call the Endpoint)

- **Where:** DRF views (permission classes or custom permission checks).
- **Purpose:** Reject clearly unauthorized requests early (e.g. “only authenticated users”, “only Buyer+”, “only Client”).
- **Mechanism:** Permission classes that resolve the current user’s **business role** (from `request.user` → domain role) and allow/deny access to the **endpoint**.
- **Rule:** This is a **gate**. It does not replace application-layer checks.

**Example (conceptual):**

- `POST /api/auth/register/` → Guest (AllowAny).
- `GET /api/auth/me/` → User (IsAuthenticated + role ≥ User).
- `POST /api/shop/refund/` → Buyer or Client (role ≥ Buyer).
- Some future `POST /api/contracts/sign/` → Client only (role == Client).

### 3.2 Application Layer (Who Can Execute the Use Case / Action)

- **Where:** Inside use cases, or in a small “authorizer” service the use case calls before doing work.
- **Purpose:** Enforce business rules such as “only Buyer can request refund” or “Client has different refund rules”. This is the **authoritative** place for “who can do what”.
- **Mechanism:** Use case (or authorizer) receives **caller role** (and optionally resource ownership). It raises a domain/application exception (e.g. `InsufficientRole`) if the role may not perform the action.
- **Rule:** Even if the transport layer allowed the request, the use case must enforce role and business rules. Never rely only on DRF permissions for business-critical actions.

**Example (conceptual):**

- `RequestRefund` use case: “Only Buyer or Client may request a refund; Client may have different limits.” Check `caller_role` inside the use case (or in an authorizer it uses).
- `SignContract` use case: “Only Client may sign.” Check inside the use case.

---

## 4. Role-by-Role Capability Matrix (Planned)

Below is a **planning** matrix. Rows = actions/use cases (or endpoint groups); columns = roles. “✓” = allowed; “✗” = denied; “—” = not applicable.

### 4.1 Auth (current)

| Action / Endpoint | Guest | User | Buyer | Client |
|-------------------|-------|------|-------|--------|
| Register | ✓ | ✗ (already user) | ✗ | ✗ |
| Login | ✓ | ✓ | ✓ | ✓ |
| Refresh / Logout | — | ✓ | ✓ | ✓ |
| Me (get/update profile) | ✗ | ✓ | ✓ | ✓ |
| Password change | ✗ | ✓ | ✓ | ✓ |
| Password reset (request/confirm) | ✓ | ✓ | ✓ | ✓ |

### 4.2 Future: Commerce (example)

| Action / Use case | Guest | User | Buyer | Client |
|-------------------|-------|------|-------|--------|
| Browse products | ✓ | ✓ | ✓ | ✓ |
| Add to cart | ✗ | ✓ | ✓ | ✓ |
| Place order | ✗ | ✓ | ✓ | ✓ |
| Request refund | ✗ | ✗ | ✓ | ✓ (possibly different rules) |
| View order history | ✗ | ✗ | ✓ | ✓ |

### 4.3 Future: Contracts / Client-only (example)

| Action / Use case | Guest | User | Buyer | Client |
|-------------------|-------|------|-------|--------|
| Sign contract | ✗ | ✗ | ✗ | ✓ |
| View contract | ✗ | ✗ | ✗ | ✓ |

We will fill in more rows as we add blog, courses, etc. The **application layer** will enforce the “✓/✗” for each use case; the **transport layer** will mirror this per endpoint so that we fail fast at the API boundary.

---

## 5. Implementation Order (Objective by Objective)

### Phase 1: Role model and data (O1, O4)

1. **Domain**
   - Add a **role** concept in `domain/accounts/`: e.g. enum or constants `Guest`, `User`, `Buyer`, `Client`.
   - Add `role` to the domain `User` entity (default `User` for existing users).
2. **Persistence**
   - Add `role` field to `accounts.models.User` (CharField with choices, or small int; migration).
   - Default existing users to `User` role.
3. **Mapping**
   - Repository (and any place that builds domain `User` from DB) sets `entity.role` from `model.role`.

Result: Every user has a single, stored role; domain and DB stay in sync.

---

### Phase 2: Application-layer authorization (O3, O5)

1. **Port**
   - Define an **authorizer** port in `application/accounts/ports/` (or a shared `application/common/ports/`): e.g. `def can_request_refund(actor_role: Role) -> bool` or `ensure_can_request_refund(actor_role: Role) -> None` (raises if not allowed).
2. **Use cases**
   - For each use case that is role-sensitive:
     - Accept **caller role** in the input (or resolve it from a passed `user_id` via repository).
     - At the start of `execute`, call the authorizer (or check role) and raise a domain/application exception (e.g. `InsufficientRole`) if not allowed.
3. **Domain exception**
   - Add `InsufficientRole` (or similar) in `domain/accounts/exceptions.py` (or shared domain). Views map it to 403.

Result: Use cases are the single place where “Buyer can request refund”, “Client can sign contract”, etc., are enforced.

---

### Phase 3: Transport-layer authorization (O2, O5)

1. **Resolve role from request**
   - Helper or service: `request.user` → domain role (Guest if anonymous, else from `user.role`).
2. **DRF permission classes**
   - Implement permission classes, e.g.:
     - `IsRoleAtLeast(User)` — allow User, Buyer, Client.
     - `IsRoleAtLeast(Buyer)` — allow Buyer, Client.
     - `IsRole(Client)` — allow only Client.
   - Use them on views/view sets so that only the right roles can call the endpoint.
3. **Apply to existing auth endpoints**
   - Register, login, password reset → Guest (AllowAny or explicit Guest).
   - Me, password change → IsAuthenticated + role ≥ User (or just IsAuthenticated if all authenticated users are at least User).

Result: Unauthorized roles get 401/403 at the HTTP layer; application layer still enforces the same rules for use cases.

---

### Phase 4: Role-by-role completion and docs (O1–O5)

1. **Matrix**
   - For each new use case or endpoint, add a row to the capability matrix and implement:
     - Application layer: role check (or authorizer call) in the use case.
     - Transport layer: permission class on the view.
2. **Documentation**
   - Keep this doc updated with the final matrix and list which permission class (and which use-case check) applies to each endpoint and use case.

---

## 6. Summary

| Layer | What it does | Where it lives |
|-------|----------------|----------------|
| **Transport** | “Can this role call this endpoint?” | DRF permission classes; role resolved from `request.user`. |
| **Application** | “Can this role execute this use case/action?” | Use cases (or authorizer port); caller role in input or resolved from user. |

**Order of implementation:**  
1) Role in domain + DB (O1, O4) → 2) Application-layer checks in use cases (O3) → 3) Transport-layer permission classes (O2) → 4) Complete matrix and docs (O5).

**Important:** The application layer is more important. Even if we add a new endpoint and forget a permission class, the use case must still reject insufficient roles. Transport layer is for defence and early rejection, not the only place where RBAC is enforced.
