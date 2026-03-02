# API Conventions

Follow these conventions so the frontend, mobile app, and tests all behave consistently.

## URL path rule: no trailing slash

**All API endpoints use no trailing slash.**

| ✅ Correct | ❌ Wrong |
|-----------|----------|
| `/api/devices` | `/api/devices/` |
| `/api/alerts` | `/api/alerts/` |
| `/api/auth/login` | `/api/auth/login/` |

### Why this matters

- When the backend route uses a trailing slash (e.g. `/api/devices/`), requests to `/api/devices` get a **307 Temporary Redirect**.
- Following redirects can drop the `Authorization` header in some clients, causing **403 Forbidden** even when the user is logged in.
- Matching the frontend URL exactly avoids redirects and keeps auth intact.

### Implementation

- Define routes with `@router.get("")` or `@router.get("/path")`, not `@router.get("/")`.
- Frontend and mobile: call `/api/devices`, `/api/alerts`, etc. (no trailing slash).
- Tests verify that `/api/devices` and `/api/alerts` do **not** return 307.

## Adding new API routes

1. Use no trailing slash on the path.
2. Add a test that the path does not redirect (307).
3. Update this doc if you introduce a new pattern.

## References

- `tests/api/test_api_routes.py` – tests for no-redirect behaviour.
- `scripts/release_gate.py` – runs these tests before deploy.
- `docs/LIVE_VERIFICATION_CHECKLIST.md` – includes manual verification steps.
