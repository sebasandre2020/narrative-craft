# Turns API Specification: Narrative-Craft

## 1. Execute Narrative Turn
Submits an active character action or narrative prompt. The service runs deterministic rule validations against the current world graph, extracts relevant graph context and semantic lore, generates literary prose with token-by-token SSE streaming, extracts a verified state delta, and commits an immutable event to the database.

- **Method & Path**: `POST /v1/timelines/{timeline_id}/turns`
- **Scope**: `turns:write`
- **Latency SLAs**:
  - Precondition Rule Validation: < 15ms
  - Time to First Token (TTFT): < 750ms
  - Total Turn Completion (p95): < 3200ms

### Request Headers
```http
Authorization: Bearer <TOKEN>
Content-Type: application/json
Accept: text/event-stream
```

### Request Payload Example
```json
{
  "character_id": "char_vespera",
  "action": "I draw the silver key from my satchel, slide it into the rusted mechanism of the iron portcullis, and turn it firmly.",
  "intent": {
    "verb": "unlock",
    "target": "gate_iron_portcullis",
    "item": "item_silver_key"
  },
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

---

## 2. Server-Sent Events (SSE) Execution Trace

When `Accept: text/event-stream` is requested, the endpoint returns HTTP 200 with `Transfer-Encoding: chunked` and emits structured event frames:

```text
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: token
data: {"text": "The"}

event: token
data: {"text": " ancient"}

event: token
data: {"text": " key"}

event: token
data: {"text": " bites into the rusted mechanism with a sharp click."}

event: graph_delta
data: {"mutations": [{"action": "UPDATE_NODE_PROPERTY", "node_id": "gate_iron_portcullis", "key": "locked", "value": false}]}

event: complete
data: {"turn_id": "turn_01HXZ7K8M9NPQR0123456789AB", "event_id": "c3d4e5f6-a7b8-9012-cdef-123456789012", "sequence_number": 15, "status": "COMMITTED"}
```

---

## 3. Failure & Error Modes

### 1. Causality Precondition Failure (`422 Unprocessable Entity`)
Occurs when an action violates physical world constraints (e.g. character not in same room as item):
```json
{
  "type": "https://narrative-craft.internal/errors/causality-violation",
  "title": "Action Precondition Violation",
  "status": 422,
  "detail": "Character 'char_vespera' is located in 'loc_crypt' but target 'item_chest' is in 'loc_throne_room'.",
  "invalid_preconditions": [
    {
      "rule": "SpatialProximityRule",
      "expected_location": "loc_throne_room",
      "actual_location": "loc_crypt"
    }
  ]
}
```

### 2. Concurrent Session Conflict (`409 Conflict`)
Occurs when another turn is currently streaming on the same timeline:
```json
{
  "type": "https://narrative-craft.internal/errors/session-locked",
  "title": "Timeline Locked",
  "status": 409,
  "detail": "Timeline 'b2c3d4e5-f6a7-8901-bcde-f12345678901' has an active executing turn. Please retry after completion."
}
```
