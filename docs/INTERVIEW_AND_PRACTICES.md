# TaskFlow — Interview Questions and Production Best Practices

This document collects interview-style questions (with concise answers) and production best practices related to the authentication and authorization work added to TaskFlow.

---

## JWT & Authentication

Q: Why use JWT (JSON Web Tokens) for API authentication instead of session cookies?
- A: JWTs are stateless tokens that carry information and are validated via signature, making them suitable for mobile and SPA clients without server-side session storage. Sessions are stateful and simpler for browser apps but require server-side session stores.

Q: How does SimpleJWT implement token refresh securely?
- A: SimpleJWT issues an `access` (short-lived) token and a `refresh` (longer-lived) token. The refresh endpoint validates the refresh token and issues a new access token. For revocation, enable the token blacklist app to mark refresh tokens as revoked.

Q: Where should server-side ownership be set and why?
- A: Set ownership in server logic (e.g., `perform_create()` in DRF viewsets) after authentication. This prevents clients from forging ownership and avoids privilege escalation.

Q: How do you revoke JWTs?
- A: Use a token blacklist (SimpleJWT's blacklist app) or rotate signing keys. Short-lived access tokens and revokable refresh tokens reduce attack windows.

Q: What HTTP status should token endpoints return on error?
- A: `401 Unauthorized` for invalid credentials or token; `400 Bad Request` if payload is malformed; `200 OK` with tokens on success.

---

## Authentication vs Authorization

Q: What's the difference between authentication and authorization?
- A: Authentication verifies identity (who you are). Authorization determines what an authenticated identity is allowed to do (permissions and access control).

Q: Where does DRF perform authentication and authorization?
- A: DRF authentication happens via authentication classes (e.g., `JWTAuthentication`) which populate `request.user`. Authorization happens via permission classes (`has_permission`, `has_object_permission`) evaluated in views.

---

## Object-level Permissions

Q: What are object-level permissions and why are they important?
- A: Object-level permissions are checks run against specific model instances (e.g., can user X edit Project Y). They are essential to enforce fine-grained security, e.g., team membership, ownership, or role-based restrictions.

Q: How do you implement object-level permissions in DRF?
- A: Implement `BasePermission` subclasses and override `has_object_permission(self, request, view, obj)`. Attach those permission classes to viewsets so DRF will call them for object requests.

---

## Queryset Filtering for Security

Q: Why filter querysets in `get_queryset()` even if you have object-level permissions?
- A: Filtering reduces data exposure (prevents listing others' objects), improves performance, and minimizes accidental leaks. Permissions prevent unauthorized changes, but filtering prevents even seeing records.

Q: How to filter querysets by team membership in DRF viewsets?
- A: Override `get_queryset(self)` and return a queryset scoped to the user, e.g.:

```python
return Project.objects.filter(Q(team__owner=user) | Q(team__members=user)).distinct()
```

Q: What if an admin user needs full access?
- A: Short-circuit in `get_queryset()` using `if request.user.is_superuser: return Model.objects.all()`.

---

## Role-based behavior (owner vs member)

Q: How to implement owner vs member behavior?
- A: Use a combination of queryset scoping, object-level permissions, and different permission logic for safe vs unsafe methods. Example: owners can `PUT/PATCH/DELETE`, members can `GET/POST` (read and create tasks), or other rules depending on business needs.

Q: Where to enforce 'owner-only' updates?
- A: In object-level permissions (`has_object_permission`) check `obj.owner == request.user` or `obj.created_by == request.user` for unsafe methods.

---

## Why hiding data is as important as blocking updates

Q: Why restrict listing/reading data (not just updates)?
- A: Data exposure is a privacy and business risk. Read-only exposure can leak sensitive project info, user emails, or business plans. Hiding data prevents enumeration attacks and reduces blast radius on breaches.

---

## Common production mistakes & best practices

- Do not commit `SECRET_KEY` or set `DEBUG=True` in public repos.
- Keep access tokens short-lived; use refresh tokens and a revocation strategy.
- Do not trust client-provided ownership fields — always set server-side.
- Filter querysets to the requesting user's scope (teams/projects) to prevent data leakage.
- Use HTTPS to transport tokens; never send tokens over plain HTTP.
- Centralize DRF settings (`DEFAULT_AUTHENTICATION_CLASSES`, `DEFAULT_PERMISSION_CLASSES`) to avoid missing protections.
- Prefer explicit service layers for complex business logic rather than overly relying on signals.

---

## Quick interview practice set (short answers)

1. Explain JWT signing and why signature validation matters.
2. How would you implement token revocation in a distributed system?
3. What's the difference between `has_permission` and `has_object_permission` in DRF?
4. Why should list endpoints be filtered by the user scope?
5. Explain a safe migration strategy when adding owner fields to existing data.

Answers (concise):
1. JWTs are signed (HS256/RS256) to prevent tampering; the signature is verified against the known secret/public key.
2. Use a central blacklist store (Redis/DB) for revoked refresh tokens or rotate signing keys and maintain an allowlist for issued tokens.
3. `has_permission` runs before object lookup (e.g., list/create), `has_object_permission` checks per-object after lookup.
4. To avoid exposing other tenants' data and to respect access boundaries.
5. Backfill owner via scripts and run data migration in controlled window; ensure app enforces owner-set after migration.

---

If you'd like, I can add more questions or export this to PDF. I can also keep this file updated automatically as I provide more interview questions.
