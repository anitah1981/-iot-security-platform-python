# Naming Conventions (API & Data Contract)

## Canonical choice: `snake_case` for API and storage

- **User identifier**: Use **`user_id`** in new code, API request/response bodies, and database documents where possible.
- **Legacy**: The codebase and some MongoDB documents still use **`userId`** (camelCase). Reads support both via `$or` queries (e.g. `{"$or": [{"user_id": id}, {"userId": id}]}`) for backward compatibility.
- **Migration**: New writes should prefer **`user_id`**. Existing fields can be migrated gradually; until then, queries that need to resolve “owner” or “user” should check both `user_id` and `userId` when reading.

## Other fields

- **API and Pydantic models**: Prefer **snake_case** (e.g. `created_at`, `device_id`, `owner_id`).
- **MongoDB**: Same preference for new fields; existing camelCase (e.g. `createdAt`, `userId`) is kept for compatibility until a deliberate migration.

## Summary

| Context        | Canonical   | Legacy (support in reads) |
|----------------|------------|----------------------------|
| User id field  | `user_id`  | `userId`                   |
| Timestamps     | `created_at` | `createdAt`               |
| New code       | Always `user_id` / snake_case | N/A |
