# Subsystem: Graph Engine & Causality Validator

## 1. Relational Property Graph Model
Narrative-Craft models the narrative universe as a directed, attributed multigraph $G = (V, E)$ where:
- $V$: Entities partitioned by type (`character`, `location`, `item`, `faction`, `concept`).
- $E$: Directed relationships (`located_in`, `possesses`, `adjacent_to`, `hostile_to`, `knows_secret`).
- Both vertices and edges carry arbitrary JSONB attributes (e.g. `hp: 100`, `locked: true`, `weight_kg: 0.5`).

## 2. In-Memory Graph with PostgreSQL Sync
- **Active Memory Model**: An in-process `NetworkX` graph is maintained in the worker for sub-millisecond neighborhood searches and cycle checks.
- **Relational Backing**: PostgreSQL tables `graph_nodes` and `graph_edges` store the durable projection. State updates are executed inside transactions alongside the `narrative_events` insert.

### Recursive CTE for $k$-Hop Spatial Neighborhood Extraction
```sql
WITH RECURSIVE neighborhood AS (
    -- Anchor: Base Entity
    SELECT source_id, target_id, relation, 1 AS depth
    FROM graph_edges
    WHERE world_id = $1 AND (source_id = $2 OR target_id = $2)
    
    UNION ALL
    
    -- Recursive Step: Expand 1 hop outwards
    SELECT e.source_id, e.target_id, e.relation, n.depth + 1
    FROM graph_edges e
    INNER JOIN neighborhood n ON (e.source_id = n.target_id OR e.target_id = n.source_id)
    WHERE e.world_id = $1 AND n.depth < $3
)
SELECT DISTINCT * FROM neighborhood;
```

---

## 3. Causality Rule Validation Engine

Before any prompt is sent to the LLM, the `RuleEngine` evaluates deterministic causality specifications:

1. **Spatial Proximity Rule**: A character can only interact with physical items located in the same location node or directly in their inventory:
   $$\text{loc}(C) = \text{loc}(I) \quad \lor \quad (C, I) \in E_{\text{possesses}}$$
2. **Door Barrier & Accessibility Rule**: A character cannot move between locations if an intervening `adjacent_to` edge carries a barrier with `locked: true` unless an unlocking mutation occurs simultaneously.
3. **No Circular Containment**: Prevent invalid topological states (e.g. Box A placed inside Box B which is inside Box A) using directed cycle detection algorithms in NetworkX.
