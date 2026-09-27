# Implementation Roadmap: Narrative-Craft

## Current Status: Phase 2 Completed (Architecture & Scaffolding)
All architectural models, OpenAPI 3.1 contracts, JSON schemas, PostgreSQL DDL schemas, Docker Compose configurations, and CI validation workflows are established and verified.

---

## Phase 3: Core Implementation Milestones

### Milestone 1: FastAPI Control Plane & Pydantic Models (Target: Week 1)
- [ ] Implement `app/main.py` with FastAPI lifespan handler and CORS middleware.
- [ ] Implement Pydantic v2 domain schemas (`CreateWorldRequest`, `NarrativeTurnRequest`, `WorldDelta`).
- [ ] Setup JWT authentication dependency with scope extraction.
- [ ] Implement Redis connection pool and distributed locking manager (`lock:timeline:{id}`).

### Milestone 2: Relational Graph & Causality Rule Engine (Target: Week 2)
- [ ] Implement `GraphRepository` using `asyncpg` with connection pooling.
- [ ] Build in-memory `NetworkX` graph wrapper with recursive CTE synchronization.
- [ ] Implement deterministic `RuleEngine` specifications:
  - `SpatialProximityRule`
  - `PossessesItemRule`
  - `BarrierLockedRule`
  - `NoCircularContainmentRule`
- [ ] Unit tests for rule engine verifying 100% rejection of physically impossible actions.

### Milestone 3: LangGraph Scene Orchestrator & SSE Streaming (Target: Week 3)
- [ ] Construct `StateGraph(SceneState)` with nodes: ingest, retrieve, generate, verify, reflect, commit.
- [ ] Implement `LLMProviderStrategy` with Anthropic Claude 3.5 Sonnet and OpenAI GPT-4o adapters.
- [ ] Implement real-time SSE streamer (`sse-starlette`) yielding chunked prose tokens and structured graph deltas.
- [ ] Implement self-correcting reflection loop for invalid proposed state deltas.

### Milestone 4: Event Sourcing & Multiverse Branching (Target: Week 4)
- [ ] Implement `EventStore` with atomic transactional append to `narrative_events`.
- [ ] Implement timeline forking (`/v1/timelines/{id}/fork`) referencing parent event snapshots.
- [ ] Implement rollback and deterministic state reconstruction engine.
- [ ] Benchmark state replay latency across 500-event chains.

### Milestone 5: Qdrant Vector Lore Retrieval (Target: Week 5)
- [ ] Setup Qdrant collection initialization and payload schema indices.
- [ ] Implement hybrid context compiler fusing 2-hop graph neighborhood with semantic lore snippets.
- [ ] Implement Langfuse tracing middleware recording latency, prompt versions, and token costs.

### Milestone 6: Model Context Protocol (MCP) Adapter (Target: Week 6)
- [ ] Implement MCP server layer exposing `inspect_world_graph`, `execute_turn`, and `fork_timeline` tools.
- [ ] Verify local integration with Claude Desktop and Cursor.

### Milestone 7: Cloud Deployment & CI/CD Activation (Target: Week 7)
- [ ] Provision AWS staging environment using Terraform (`infra/terraform`).
- [ ] Activate GitHub Actions deployment workflow with Trivy vulnerability scanning.
- [ ] Execute automated load test verifying p95 turn latency under concurrent load.
