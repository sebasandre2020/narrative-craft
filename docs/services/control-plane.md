# Subsystem: API Admission & Control Plane

## 1. Overview
The Control Plane is an asynchronous FastAPI service handling client requests, token authorization, Pydantic v2 schema admission, concurrency leasing, and Server-Sent Events (SSE) multiplexing.

## 2. Ingress & Authorization Flow
1. **JWT Verification**: The API extracts the Bearer token from the `Authorization` header. It validates the cryptographic signature against cached JWKS, checks expiration (`exp`), and ensures the token contains required tenant scopes (`turns:write`, `worlds:read`).
2. **Tenant Partitioning**: The extracted `organization_id` or `user_id` is stamped onto request context, ensuring that database queries strictly filter by tenant ID via PostgreSQL Row-Level Security (RLS).
3. **Pydantic v2 Parsing**: Payloads are strictly parsed using Pydantic v2 with `extra='forbid'`, rejecting unmapped or dangerous parameters.

## 3. Concurrency Leasing via Redis Distributed Locks
To ensure that a timeline's event log remains strictly serialized and that two turns do not mutate the same world graph simultaneously, the control plane acquires a distributed Redis lock:

```python
lock_key = f"lock:timeline:{timeline_id}"
# Acquire lock with a 30-second TTL
acquired = await redis.set(lock_key, worker_id, nx=True, ex=30)
if not acquired:
    raise HTTPException(status_code=409, detail="Timeline is actively processing another turn.")
```

If a client terminates an SSE connection prematurely, a background cancellation hook releases the Redis lock and terminates the upstream LLM streaming task.
