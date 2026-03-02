# API Conventions

## URL Shape

- All JSON API endpoints use **no trailing slash**.
  - **Good**: `/api/devices`, `/api/alerts`, `/api/auth/login`
  - **Avoid**: `/api/devices/`, `/api/alerts/`

### Routers

- When mounting routers with a prefix (for example `app.include_router(devices_router, prefix="/api/devices")`):
  - Use `@router.get("")` / `@router.post("")` for the root resource.
  - Do **not** use `@router.get("/")` / `@router.post("/")`, as that introduces an automatic redirect.

Example:

```python
router = APIRouter()

@router.get("", ...)
async def list_devices(...):
    ...

@router.post("", ...)
async def create_device(...):
    ...

@router.get("/{device_id}", ...)
async def get_device(...):
    ...
```

## Auth and Redirects

- JSON API endpoints should return:
  - **401** when authentication is missing or invalid.
  - **403** when authentication is valid but access is forbidden.
- Avoid 3xx redirects on authenticated JSON APIs; redirects can drop headers or cookies and cause confusing 403s.

## Clients

- Web, mobile, and tests must all call the same URLs:
  - Always call `/api/devices`, **not** `/api/devices/`.
  - Always call `/api/alerts`, **not** `/api/alerts/`.

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
