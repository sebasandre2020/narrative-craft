# Architecture: Narrative-Craft

**Status**: Proposed service architecture and system design specification. [Index](Index.md) · [Class](Class.md) · [Operations](Operations.md)

---

## 1. Boundaries and Topology

```mermaid
flowchart TB
  subgraph External[External Trust Boundary]
    Client[Web Client / Game UI / MCP Host]
    IdP[OIDC / OAuth2 Identity Provider]
    LLMProviders[Foundation Model Providers - Anthropic / OpenAI / Bedrock]
    LangfuseCloud[Langfuse Tracing Cloud]
  end

  subgraph AWS[AWS Production Environment - us-east-1]
    ALB[Application Load Balancer - HTTPS / WAF]

    subgraph VPC[Virtual Private Cloud - 10.0.0.0/16]
      subgraph PrivateAppSubnets[Private Application Subnets - Multi-AZ]
        API[FastAPI Control Plane - ECS Fargate Service]
        Orchestrator[LangGraph Scene Engine - Task Workers]
      end

      subgraph PrivateDataSubnets[Private Data Subnets - Multi-AZ]
        RDS[(Amazon RDS PostgreSQL 16 - Multi-AZ)]
        Redis[(ElastiCache Redis 7 - Active Graph Cache)]
        QdrantCluster[(Qdrant Vector Cluster - Semantic Lore)]
      end

      S3[(Amazon S3 - World Snapshots & Event Archives)]
      KMS[AWS KMS - Secret & DB Encryption]
      CW[Amazon CloudWatch - Logs & Metrics]
    end
  end

  Client -->|HTTPS / WSS / SSE| ALB
  ALB --> API
  API -->|JWT Scope & Signature Validation| IdP
  API -->|Read/Write Active World Graph| Redis
  API -->|Append-Only Event Store & Graph Sync| RDS
  API --> Orchestrator
  Orchestrator -->|Vector Lore Retrieval| QdrantCluster
  Orchestrator -->|Bounded LLM Generation| LLMProviders
  Orchestrator -.->|Async Redacted Traces| LangfuseCloud
  API --> S3
  API --> KMS
  API --> CW
```

### Architectural Subsystems
1. **API Admission & Control Plane**: FastAPI application responsible for client authentication, request validation (Pydantic v2), rate limiting, and Server-Sent Events (SSE) multiplexing.
2. **Graph Engine & Deterministic Guardrails**: In-memory graph model (NetworkX adapter) backed by PostgreSQL. Evaluates physical causality rules (proximity, containment, accessibility) before and after narrative generation.
3. **LangGraph Scene Orchestrator**: Cyclic state graph that coordinates prompt construction, dynamic LLM generation, structured delta extraction, and reflection loops.
4. **Event-Sourced Multiverse Storage**: PostgreSQL stores an immutable, append-only log of every narrative event. Active world state is materialized into Redis and relational property tables. Snapshots are archived to Amazon S3.

---

## 2. Request & Turn Execution Lifecycle

The following sequence details how a narrative turn is admitted, validated, generated, committed, and streamed to the client:

```mermaid
sequenceDiagram
  autonumber
  participant Client as Client Application
  participant API as FastAPI Control Plane
  participant Redis as Redis Session Cache
  participant Graph as Graph & Rule Engine
  participant Qdrant as Qdrant Lore Store
  participant LG as LangGraph Orchestrator
  participant LLM as Upstream LLM Gateway
  participant PG as PostgreSQL Event Store

  Client->>API: POST /v1/timelines/{id}/turns (Action: "Open iron gate with silver key")
  API->>Redis: Acquire session lock & retrieve cached WorldGraph
  Redis-->>API: Active WorldGraph Snapshot

  API->>Graph: Validate Action Feasibility(Graph, Action)
  alt Rule Violation (e.g. Character does not possess key)
    Graph-->>API: Violation: Insufficient preconditions
    API-->>Client: 422 Unprocessable Entity (Semantic error payload)
  else Preconditions Met
    Graph-->>API: Action Allowed
  end

  API->>Qdrant: Hybrid Lore Query(Action, CurrentLocation)
  Qdrant-->>API: Top-K Relevant Canon Lore Chunks

  API->>LG: Execute Scene Generation Graph(WorldGraph, Lore, Action)
  LG->>LLM: Stream Prompt (System + Graph Context + Lore + User Action)
  
  loop Token Streaming
    LLM-->>LG: Raw Token Chunks
    LG-->>API: Yield Token Event
    API-->>Client: SSE event: token ("The heavy iron gate creaks open...")
  end

  LLM-->>LG: Complete Structured Output (Prose + Pydantic WorldDelta)
  LG->>Graph: Verify WorldDelta(Graph, WorldDelta)
  alt Delta Violates Consistency
    LG->>LG: Reflection Cycle (Refine Delta with Critique)
  end

  LG->>PG: Begin Transaction: Append Event + Apply Graph Mutations
  PG-->>LG: Transaction Committed (event_id: evt_1042)
  LG->>Redis: Update In-Memory WorldGraph & Release Lock

  LG-->>API: Final Turn Receipt
  API-->>Client: SSE event: graph_delta (JSON Mutations)
  API-->>Client: SSE event: complete (turn_id, event_id, status: COMMITTED)
```

---

## 3. Graph RAG & Spatial Neighborhood Extraction

Standard vector retrieval often fails in spatial and relational contexts (e.g. knowing who is in the room, what items are on the table, and who belongs to which hostile faction). Narrative-Craft implements **Graph-Augmented Generation (Graph RAG)**:

```mermaid
flowchart TD
  TargetNode["Current Focus: Character (Lady Vespera)"]
  TargetNode -->|located_in| Loc["Location: Forgotten Crypt"]
  Loc -->|contains| Item1["Item: Ancient Sarcophagus"]
  Loc -->|contains| Item2["Item: Silver Key"]
  Loc -->|adjacent_to| Loc2["Location: Damp Antechamber"]
  TargetNode -->|member_of| Faction["Faction: Order of the Silver Sigil"]
  Faction -->|hostile_to| Enemy["Faction: Cult of the Ashen Dawn"]

  subgraph Neighborhood["1-to-2 Hop Subgraph Extraction"]
    Loc
    Item1
    Item2
    Loc2
    Faction
    Enemy
  end

  Neighborhood --> ContextCompiler[Context Compiler]
  ContextCompiler --> SystemPrompt[LLM System Prompt Context]
```

Before calling the LLM, the Graph Engine executes a bounded $k$-hop traversal ($k=2$) around the acting character. This generates a deterministic relational snapshot formatted as compact YAML in the prompt context, guaranteeing that the model only references entities physically or socially connected to the scene.

---

## 4. Event-Sourced Multiverse Branching Model

Narrative-Craft avoids mutable state corruption by modeling time as an immutable directed acyclic graph (DAG) of narrative events:

```mermaid
gitGraph
   commit id: "evt_001 (Game Start)"
   commit id: "evt_002 (Enter Courtyard)"
   commit id: "evt_003 (Inspect Statue)"
   branch timeline_beta
   checkout timeline_beta
   commit id: "evt_004b (Smash Statue)"
   commit id: "evt_005b (Awaken Guardian)"
   checkout main
   commit id: "evt_004a (Decipher Inscription)"
   commit id: "evt_005a (Unlock Catacombs)"
```

- **Root Timeline**: The canonical primary storyline.
- **Timeline Forking**: Calling `/v1/timelines/{id}/fork` takes an `event_id` snapshot pointer. A new child timeline record is created referencing the parent event without copying historical events.
- **Rollbacks**: Rolling back simply advances the active head pointer to an earlier event in the chain. Replays reconstruct state deterministically from the nearest cached snapshot.

---

## 5. Security, Authorization & Data Isolation

1. **Authentication & Multi-Tenant Isolation**: Every incoming request carries a verified JWT. Worlds and timelines belong to an `organization_id` or `user_id`. PostgreSQL Row-Level Security (RLS) ensures tenant data isolation at the database layer.
2. **Egress Guardrails**: Upstream calls to foundation models (Anthropic Claude, OpenAI GPT-4o, AWS Bedrock) pass through an egress proxy with strict timeout budgets (15s connect, 45s read) and prompt-injection sanitization.
3. **Data Protection**:
   - In-transit: TLS 1.3 enforced across all ALB, Redis, and PostgreSQL connections.
   - At-rest: AES-256 encryption via AWS KMS on RDS volumes, Redis clusters, and S3 snapshot buckets.

---

## 6. Deliberate Architectural Trade-offs

| Decision | Trade-off Benefit | Cost / Revisit Trigger |
| :--- | :--- | :--- |
| **Relational Graph in PostgreSQL vs. Neo4j** | ACID transactions across event log and graph tables; operational simplicity without managing two primary databases. | If graph queries exceed 4-hop depth or traversal latency exceeds 35ms under load, evaluate FalkorDB or Neo4j. |
| **NetworkX In-Memory Cache in Redis** | Sub-millisecond graph traversals and rule validations during active interactive turns. | Requires strict Redis memory budgeting and periodic write-through snapshot synchronization. |
| **Pre-Generation Deterministic Rule Validation** | Prevents invalid LLM hallucinations before spending tokens; guarantees physical causality. | Requires maintaining a deterministic rule registry in code alongside LLM prompts. |
| **Dual SSE Streaming (Tokens + Deltas)** | Allows game clients to animate text while updating 2D/3D visual maps in real time. | Requires client support for custom SSE event types (`token`, `graph_delta`, `complete`). |
