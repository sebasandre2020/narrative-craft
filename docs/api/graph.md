# Graph API Specification: Narrative-Craft

## 1. Extract Subgraph Neighborhood ($k$-Hop Traversal)
Extracts a bounded relational neighborhood around a central entity (e.g. the active character or target location). This endpoint is used by external game visualizers, UI maps, and debuggers.

- **Method & Path**: `GET /v1/timelines/{timeline_id}/graph/subgraph`
- **Scope**: `graph:read`
- **Latency SLA**: p95 < 25ms
- **Query Parameters**:
  - `center_id` (string, required): Central node identifier (e.g. `char_vespera`).
  - `hops` (integer, default: 2, min: 1, max: 4): Radius of the traversal.

### Response Payload (`200 OK`)
```json
{
  "center_id": "char_vespera",
  "hops": 2,
  "nodes": [
    {
      "id": "char_vespera",
      "type": "character",
      "label": "Lady Vespera",
      "properties": { "class": "Arcane Inquisitor", "hp": 100 }
    },
    {
      "id": "loc_crypt",
      "type": "location",
      "label": "Crypt of Ancients",
      "properties": { "lighting": "dim" }
    },
    {
      "id": "gate_iron_portcullis",
      "type": "item",
      "label": "Rusted Iron Portcullis",
      "properties": { "locked": false }
    }
  ],
  "edges": [
    {
      "source": "char_vespera",
      "target": "loc_crypt",
      "relation": "located_in",
      "properties": {}
    },
    {
      "source": "gate_iron_portcullis",
      "target": "loc_crypt",
      "relation": "located_in",
      "properties": {}
    }
  ]
}
```

---

## 2. Query Full Active World Graph
Returns the current active graph projection for a timeline. Supports filtering by node type (e.g. `type=character`, `type=location`).

- **Method & Path**: `GET /v1/timelines/{timeline_id}/graph`
- **Scope**: `graph:read`
- **Query Parameters**:
  - `node_type` (string, optional): Filter by entity type (`character`, `location`, `item`, `faction`).
  - `limit` (integer, default: 100).
