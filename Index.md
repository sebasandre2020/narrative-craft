# Documentation Index: Narrative-Craft

**Status**: Technical blueprint index and navigation schema.

---

## 1. Core Documentation Map

| Area | Documentation Entry Point | Description |
| :--- | :--- | :--- |
| **Recruiter Introduction & Pitch** | [README.md](README.md) | Fast 30-second read, architecture overview, sample curl requests |
| **System Architecture** | [Architecture.md](Architecture.md) | Topology diagrams, request lifecycles, Graph RAG, security layers |
| **Classes & State Machines** | [Class.md](Class.md) | Component responsibilities, LangGraph state transitions, design patterns |
| **Operational Runbook** | [Operations.md](Operations.md) | Local runbook, docker-compose commands, telemetry, disaster recovery |
| **Project Brief & Vision** | [PROJECT_BRIEF.md](PROJECT_BRIEF.md) | Problem statement, user personas, in-scope/out-of-scope boundaries |
| **Phase 3 Roadmap** | [docs/roadmap.md](docs/roadmap.md) | Implementation milestones, acceptance criteria, and rollout phases |
| **Scaffold Verification** | [docs/validation.md](docs/validation.md) | Empirical test records and scaffold integrity checks |
| **Academic & Industry References** | [docs/references.md](docs/references.md) | Graph RAG literature, Event Sourcing, and standards citations |

---

## 2. API Contract & Endpoint Map

| Method & Path | Authorization Scope | Contract Specification | Description |
| :--- | :--- | :--- | :--- |
| `POST /v1/worlds` | `worlds:write` | [Worlds API](docs/api/worlds.md) | Initialize new narrative world session from template |
| `GET /v1/worlds/{world_id}` | `worlds:read` | [Worlds API](docs/api/worlds.md) | Retrieve world configuration and active timelines |
| `POST /v1/timelines/{id}/turns` | `turns:write` | [Turns API](docs/api/turns.md) | Execute narrative turn with token and delta SSE streaming |
| `GET /v1/timelines/{id}/events` | `events:read` | [Timelines API](docs/api/timelines.md) | Retrieve paginated immutable event log for timeline |
| `POST /v1/timelines/{id}/fork` | `timelines:write` | [Timelines API](docs/api/timelines.md) | Fork alternate multiverse timeline from an event snapshot |
| `POST /v1/timelines/{id}/rollback`| `timelines:write` | [Timelines API](docs/api/timelines.md) | Roll back timeline active head to a historical event |
| `GET /v1/timelines/{id}/graph` | `graph:read` | [Graph API](docs/api/graph.md) | Query full or filtered property graph of active state |
| `GET /v1/timelines/{id}/graph/subgraph`| `graph:read`| [Graph API](docs/api/graph.md) | Extract $k$-hop neighborhood around target entity |
| `GET /health/live` | Public Probe | [Conventions](docs/api/conventions.md) | Liveness probe for ALB and container monitors |
| `GET /health/ready` | Public Probe | [Conventions](docs/api/conventions.md) | Readiness probe verifying DB, Redis, and Qdrant links |

*Detailed Schema Files:* [OpenAPI 3.1 Contract](contracts/openapi.json) · [JSON Schemas](contracts/schemas.json) · [API Conventions](docs/api/conventions.md)

---

## 3. Subsystem & Service Specifications

| Subsystem | Core Responsibilities | Architectural Specification |
| :--- | :--- | :--- |
| **API Admission & Control Plane** | Auth verification, Pydantic validation, SSE streaming | [Control Plane](docs/services/control-plane.md) |
| **Graph Engine & Rule Validator** | In-memory graph model, causality verification | [Graph Engine](docs/services/graph-engine.md) |
| **LangGraph Scene Orchestrator** | Cyclic scene generation, self-correcting delta loops | [Orchestration](docs/services/orchestration.md) |
| **Event Sourcing & Multiverse Engine**| Append-only event store, branching DAG, replay engine | [Event Sourcing](docs/services/event-sourcing.md) |
| **Vector Lore Retrieval** | Hybrid dense vector retrieval, Qdrant index tuning | [Lore Retrieval](docs/services/retrieval.md) |
| **Telemetry & Observability** | Langfuse LLM traces, Prometheus metrics, structured logs | [Observability](docs/services/observability.md) |
| **Cloud Infrastructure (AWS)** | ECS Fargate, RDS PostgreSQL, ElastiCache, S3 snapshots | [Deployment Blueprint](docs/delivery/deployment.md) |
| **Continuous Integration & Delivery** | GitHub Actions CI/CD pipeline, container builds | [CI/CD Blueprint](docs/delivery/ci-cd.md) |

---

## 4. Scaffolding Artifacts & Configuration

- **Docker Environment**: [compose.yaml](compose.yaml) · [infra/docker/Dockerfile.blueprint](infra/docker/Dockerfile.blueprint)
- **Database Schema**: [infra/postgres/001_init_schema.sql](infra/postgres/001_init_schema.sql)
- **Terraform IaC**: [infra/terraform/main.tf](infra/terraform/main.tf) · [infra/terraform/variables.tf](infra/terraform/variables.tf) · [infra/terraform/outputs.tf](infra/terraform/outputs.tf)
- **Validation & Scripts**: [scripts/validate_scaffold.py](scripts/validate_scaffold.py) · [requirements-dev.txt](requirements-dev.txt)
- **Sample Payloads**: [examples/create_world.json](examples/create_world.json) · [examples/narrative_turn_request.json](examples/narrative_turn_request.json) · [examples/narrative_turn_response.json](examples/narrative_turn_response.json) · [examples/graph_delta_sample.json](examples/graph_delta_sample.json) · [examples/branch_timeline.json](examples/branch_timeline.json)
