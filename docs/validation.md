# Validation Records & Empirical Verification: Narrative-Craft

## 1. Summary of Scaffolding Validation
This document logs the empirical checks executed to verify that Narrative-Craft satisfies all Phase 2 architectural, structural, and contract requirements.

## 2. Automated Scaffold Execution Record

```text
Command: python scripts/validate_scaffold.py
Working Directory: C:\Repositories\GHProjects\narrative-craft
Result: SUCCESS (Exit Code 0)
Output:
[+] Validating Narrative-Craft scaffold at: C:\Repositories\GHProjects\narrative-craft

[OK] Scaffold Validation Succeeded! All contracts, schemas, files, and fixtures verified.
```

### Verified Checks:
1. **File System Integrity**: All required core files (`README.md`, `Architecture.md`, `Class.md`, `Index.md`, `Operations.md`, `PROJECT_BRIEF.md`, `compose.yaml`, `pyproject.toml`, `requirements-dev.txt`, `.env.example`, `.gitignore`) exist and are non-empty.
2. **OpenAPI 3.1.0 Contract**: `contracts/openapi.json` parsed successfully as valid JSON and conforms to OpenAPI 3.1.0 structure with all critical endpoints mapped (`/v1/worlds`, `/v1/timelines/{timeline_id}/turns`, `/v1/timelines/{timeline_id}/fork`, `/v1/timelines/{timeline_id}/graph/subgraph`, `/health/live`, `/health/ready`).
3. **JSON Schema Registry**: `contracts/schemas.json` validated as valid JSON Schema Draft 2020-12 defining `GraphNode`, `GraphEdge`, `GraphMutation`, `WorldDelta`, and `NarrativeEvent`.
4. **Relational Graph DDL**: `infra/postgres/001_init_schema.sql` verified for table definitions (`worlds`, `timelines`, `narrative_events`, `graph_nodes`, `graph_edges`, `timeline_snapshots`) and seed fixtures.
5. **Sample Payloads**: Validated JSON integrity for:
   - `examples/create_world.json`
   - `examples/narrative_turn_request.json`
   - `examples/narrative_turn_response.json`
   - `examples/graph_delta_sample.json`
   - `examples/branch_timeline.json`

## 3. Phase 3 Implementation & Empirical Verification Record

Phase 3 implementation has been completed and empirically verified across all architectural layers.

### Verified Checks:
1. **Automated Unit & Integration Test Suite**:
   ```text
   Command: .venv\Scripts\pytest tests/ -v
   Result: SUCCESS (17 passed in 21.74s)
   - tests\test_api_endpoints.py: Health probes, World lifecycle, fork, and SSE stream verification (3 passed)
   - tests\test_graph_engine.py: Node/Edge CRUD, k-hop neighborhood extraction, WorldDelta application, YAML export (5 passed)
   - tests\test_orchestrator.py: Turn stream coordination, cyclic reflection, precondition error rejection (2 passed)
   - tests\test_rule_engine.py: Character existence, key possession, locked barrier traversals, delta verification (7 passed)
   ```

2. **Docker Port Isolation**:
   - `narrative-craft-postgres`: Bound to host port `5434` (healthy).
   - `narrative-craft-redis`: Bound to host port `6380` (healthy).
   - `narrative-craft-qdrant`: Bound to host port `6333` (healthy).
   - Preserved full operational integrity of `multi-account-finance-agent` on ports `5432`, `6379`, `8000`, `3000`, `3001`.

3. **Live Foundation Model Integration (MiniMax-M3)**:
   - Configured MiniMax OpenAI-compatible chat completions gateway (`https://api.minimax.io/v1`).
   - Added automated reasoning tag (`<think>...</think>`) filtering to stream pure literary prose to client consumers.
   - Tested real-time dual-channel SSE token streaming (`event: token`) and structured delta extraction (`event: graph_delta`).

4. **Event Sourcing & Graph Persistence**:
   - Created world sessions and committed narrative turns to PostgreSQL table `narrative_events`.
   - Verified that physical lock state mutations (`UPDATE_NODE_PROPERTY: gate_iron_portcullis.locked = false`) update active world state and persist across turns.

