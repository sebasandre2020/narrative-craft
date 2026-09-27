# Timelines & Multiverse API Specification: Narrative-Craft

## 1. Fork Alternate Multiverse Timeline
Creates a new child timeline branched from a specific historical event snapshot. This enables non-destructive "what-if" branching without duplicating parent event logs.

- **Method & Path**: `POST /v1/timelines/{timeline_id}/fork`
- **Scope**: `timelines:write`
- **Latency SLA**: p95 < 40ms

### Request Payload Example
```json
{
  "name": "Timeline: Lady Vespera Destroys Portcullis",
  "fork_event_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "description": "Explores consequences of an aggressive arcana breach instead of stealth key entry."
}
```

### Response Payload (`201 Created`)
```json
{
  "timeline_id": "7a8b9c0d-1e2f-3456-7890-abcdef123456",
  "world_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "parent_timeline_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "fork_event_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "name": "Timeline: Lady Vespera Destroys Portcullis",
  "created_at": "2026-09-27T15:45:00.000Z"
}
```

---

## 2. Retrieve Timeline Event Log
Retrieves the append-only history of narrative events for a timeline, ordered by sequence number.

- **Method & Path**: `GET /v1/timelines/{timeline_id}/events`
- **Scope**: `events:read`
- **Parameters**:
  - `limit` (int, default: 50, max: 200)
  - `since_sequence` (int, optional)

### Response Payload (`200 OK`)
```json
{
  "timeline_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "total_events": 15,
  "events": [
    {
      "event_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "sequence_number": 14,
      "action_prompt": "I draw the silver key...",
      "narrative_prose": "The ancient key bites into the tarnished lock...",
      "graph_delta": {
        "mutations": [
          {
            "action": "UPDATE_NODE_PROPERTY",
            "node_id": "gate_iron_portcullis",
            "key": "locked",
            "value": false
          }
        ]
      },
      "committed_at": "2026-09-27T15:45:00.000Z"
    }
  ]
}
```

---

## 3. Rollback Timeline Head
Reverts the active state head of the timeline to a previous event. Subsequent turns will append from that point forward.

- **Method & Path**: `POST /v1/timelines/{timeline_id}/rollback`
- **Scope**: `timelines:write`
- **Request Payload**:
  ```json
  {
    "target_event_id": "c3d4e5f6-a7b8-9012-cdef-123456789012"
  }
  ```
- **Response Payload (`200 OK`)**:
  ```json
  {
    "timeline_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "rolled_back_to_event_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "current_sequence_number": 14,
    "status": "REVERTED_AND_READY"
  }
  ```
