# Project Brief: Narrative-Craft

## Executive Summary
**Narrative-Craft** is a production-grade, consumable AI engine and headless backend service for interactive storytellers, narrative designers, and tabletop roleplaying creators. It bridges the gap between creative LLM text generation and deterministic physical world consistency through **Graph-Augmented Generation (Graph RAG)**, **deterministic rule guardrails**, and an **event-sourced multiverse state machine**.

Standard conversational AI models suffer from severe narrative entropy: characters teleport across cities, forgotten items materialize from thin air, and established canon lore is rewritten after a dozen conversational turns. Narrative-Craft prevents narrative drift by maintaining an explicit property graph of entities, validating causality before generation, and recording every narrative turn as an immutable state event capable of instant branching and rollback.

## Target Personas & Core Problem
1. **Interactive Fiction & Game Developers**: Building text-based RPGs or narrative dialogue systems that require reliable inventory tracking, relationship dynamics, and world causality without hardcoding every branch.
2. **Tabletop Roleplaying Game Masters (GMs)**: Running complex campaign worlds who need a co-pilot that remembers faction alliances, hidden secrets, and geographic travel times without contradicting campaign canon.
3. **Creative Writers & Worldbuilders**: Exploring branching "what-if" multiverse timelines with full confidence that physical rules and character knowledge states remain consistent across iterations.

## Architectural Pillars & Design Principles
- **Consumable Service Over Monolithic App**: Exposes pure OpenAPI 3.1 REST endpoints, Server-Sent Events (SSE) token and mutation streams, and Model Context Protocol (MCP) tools. Frontends (if any) are strictly minimal testbenches or stream consumers.
- **Graph RAG Over Plain Vector Search**: Narrative state is an evolving property graph (nodes: Characters, Locations, Items, Factions; edges: `located_in`, `possesses`, `allied_with`, `hostile_to`). Semantic lore is retrieved via hybrid dense vector + $k$-hop graph neighborhood extraction.
- **Deterministic State Guardrails**: Before LLM scene synthesis, a deterministic rule validator verifies physical feasibility (e.g., character proximity, inventory possession, locked barriers).
- **Event-Sourced Multiverse Engine**: World state is reconstructed from an immutable event log. Branching timelines ("what-if" alternate realities) are lightweight child branches created without duplicating historical event data.
- **Async & Real-Time Streaming**: Scene descriptions stream token-by-token via SSE, accompanied by structured JSON state deltas consumed by client graph visualizers.

## Target Technology Stack
- **Language & Runtime**: Python 3.12, FastAPI, AsyncIO, Pydantic v2
- **Data Persistence**: PostgreSQL 16 (Relational tables, JSONB event payloads, recursive graph queries), Redis 7 (Active session state, pub/sub, graph snapshot cache)
- **Vector Retrieval**: Qdrant (Semantic lore and historical episodic memory)
- **Agent Orchestration**: LangGraph (Cyclic state machine with reflection and validation nodes)
- **Protocols**: OpenAPI 3.1, Server-Sent Events (SSE), Model Context Protocol (MCP) JSON-RPC 2.0
- **Observability**: Langfuse (LLM tracing, token tracking, prompt versioning), Prometheus (p95 latency, state transition counters)
- **Infrastructure & Delivery**: Docker, Docker Compose, AWS ECS Fargate, AWS RDS PostgreSQL, AWS S3 (World snapshot backups), Terraform, GitHub Actions

## Scope & Non-Goals
### In Scope (Core Service)
- World template initialization and entity seeding
- $k$-hop graph neighborhood extraction and spatial proximity traversal
- LangGraph scene generation and self-correcting delta reconciliation
- Event-sourced timeline branching, checkpointing, and rollbacks
- Dual-channel SSE streaming (text tokens + structured graph mutation deltas)
- Model Context Protocol (MCP) tool integration for external agent runtimes

### Out of Scope (Explicit Non-Goals)
- Heavy monolithic frontend UI or commercial game engine wrappers (Unity/Unreal SDKs)
- Direct text-to-speech or 3D asset generation (pure headless narrative service)
- Unbounded multi-user MMO synchronization (scoped to single-tenant or collaborative table sessions)
- Unverified, non-deterministic graph mutations without schema enforcement
