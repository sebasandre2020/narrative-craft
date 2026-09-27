# Worlds API Specification: Narrative-Craft

## 1. Create World Session
Initializes a new persistent world session, creates the root (prime) canonical timeline, and optionally seeds initial graph nodes and edges.

- **Method & Path**: `POST /v1/worlds`
- **Scope**: `worlds:write`
- **Latency SLA**: p95 < 60ms

### Request Headers
```http
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

### Request Payload Example
```json
{
  "title": "Citadel of Ashen Wings",
  "description": "A high-altitude mountain stronghold besieged by storm elementals.",
  "template": "mountain_citadel",
  "config": {
    "max_reflection_attempts": 2,
    "temporal_decay_lambda": 0.05,
    "subgraph_hops": 2
  }
}
```

### Response Payload (`201 Created`)
```json
{
  "world_id": "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "title": "Citadel of Ashen Wings",
  "description": "A high-altitude mountain stronghold besieged by storm elementals.",
  "active_timeline_id": "1a2b3c4d-5e6f-7890-abcd-ef0123456789",
  "created_at": "2026-09-27T15:40:00.000Z"
}
```

---

## 2. Get World Session
Retrieves world metadata, configuration flags, and list of associated timelines (branches).

- **Method & Path**: `GET /v1/worlds/{world_id}`
- **Scope**: `worlds:read`
- **Latency SLA**: p95 < 20ms

### Response Payload (`200 OK`)
```json
{
  "world_id": "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "title": "Citadel of Ashen Wings",
  "description": "A high-altitude mountain stronghold besieged by storm elementals.",
  "config": {
    "max_reflection_attempts": 2,
    "temporal_decay_lambda": 0.05,
    "subgraph_hops": 2
  },
  "timelines": [
    {
      "timeline_id": "1a2b3c4d-5e6f-7890-abcd-ef0123456789",
      "name": "Canonical Timeline (Prime)",
      "is_active": true
    }
  ],
  "created_at": "2026-09-27T15:40:00.000Z"
}
```
