# Class & State Models: Narrative-Craft

**Status**: Implementation blueprint and component specification. [Index](Index.md) · [Architecture](Architecture.md) · [Operations](Operations.md)

---

## 1. Class Diagram & Component Responsibilities

```mermaid
classDiagram
  class WorldSession {
    +UUID world_id
    +UUID active_timeline_id
    +str title
    +dict config
    +datetime created_at
  }

  class WorldGraph {
    +dict~str, GraphNode~ nodes
    +dict~str, GraphEdge~ edges
    +add_node(node: GraphNode)
    +add_edge(edge: GraphEdge)
    +extract_subgraph(center_id: str, hops: int) Subgraph
    +validate_containment(item_id: str, container_id: str) bool
    +to_yaml() str
  }

  class GraphNode {
    +str id
    +str type
    +str label
    +dict properties
  }

  class GraphEdge {
    +str source_id
    +str target_id
    +str relation
    +dict properties
  }

  class RuleEngine {
    +list~CausalityRule~ rules
    +validate_preconditions(action: UserAction, graph: WorldGraph) RuleValidationResult
    +verify_delta(delta: WorldDelta, graph: WorldGraph) DeltaVerificationResult
  }

  class LangGraphOrchestrator {
    +StateGraph workflow
    +execute_turn(state: SceneState) AsyncIterator~TurnStreamChunk~
    -_node_ingest(state: SceneState) SceneState
    -_node_retrieve_graph(state: SceneState) SceneState
    -_node_generate_scene(state: SceneState) SceneState
    -_node_verify_delta(state: SceneState) SceneState
    -_node_reflection(state: SceneState) SceneState
    -_node_commit(state: SceneState) SceneState
  }

  class SceneState {
    +UUID turn_id
    +str user_action
    +str active_character_id
    +Subgraph local_subgraph
    +list~str~ retrieved_lore
    +str generated_prose
    +WorldDelta proposed_delta
    +int reflection_attempts
    +bool is_valid
  }

  class WorldDelta {
    +list~GraphMutation~ mutations
    +list~FactEntry~ new_facts
    +dict state_changes
  }

  class EventStore {
    +append_event(timeline_id: UUID, delta: WorldDelta, prose: str) NarrativeEvent
    +get_event_stream(timeline_id: UUID, from_event_id: UUID) list~NarrativeEvent~
    +create_branch(parent_timeline_id: UUID, fork_event_id: UUID) UUID
  }

  class NarrativeEvent {
    +UUID event_id
    +UUID timeline_id
    +int sequence_number
    +str action
    +str prose
    +dict graph_delta
    +datetime committed_at
  }

  class LLMProviderStrategy {
    <<interface>>
    +stream_generation(prompt: str, schema: type) AsyncIterator~str~
  }

  class AnthropicAdapter {
    +stream_generation(prompt: str, schema: type) AsyncIterator~str~
  }

  class OpenAIAdapter {
    +stream_generation(prompt: str, schema: type) AsyncIterator~str~
  }

  WorldSession "1" --> "1" WorldGraph
  WorldGraph "1" *-- "*" GraphNode
  WorldGraph "1" *-- "*" GraphEdge
  LangGraphOrchestrator --> RuleEngine
  LangGraphOrchestrator --> SceneState
  LangGraphOrchestrator --> LLMProviderStrategy
  LLMProviderStrategy <|.. AnthropicAdapter
  LLMProviderStrategy <|.. OpenAIAdapter
  SceneState --> WorldDelta
  LangGraphOrchestrator --> EventStore
  EventStore "1" *-- "*" NarrativeEvent
```

---

## 2. Narrative Turn State Machine

The LangGraph orchestration lifecycle models the execution, self-correction, and streaming of each narrative interaction:

```mermaid
stateDiagram-v2
  [*] --> ADMITTED: POST /v1/timelines/{id}/turns
  ADMITTED --> VALIDATING_PRECONDITIONS: Parse User Action
  
  VALIDATING_PRECONDITIONS --> PRECONDITION_FAILED: Causality Violation (e.g. key missing)
  PRECONDITION_FAILED --> [*]: 422 Unprocessable Entity
  
  VALIDATING_PRECONDITIONS --> EXTRACTING_SUBGRAPH: Preconditions Met
  EXTRACTING_SUBGRAPH --> RETRIEVING_LORE: 2-Hop Graph Neighborhood
  RETRIEVING_LORE --> STREAMING_PROSE: Query Qdrant Vector Lore
  
  STREAMING_PROSE --> EXTRACTING_DELTA: LLM Token Stream Emitted
  EXTRACTING_DELTA --> VERIFYING_DELTA: Pydantic WorldDelta Parsed
  
  VERIFYING_DELTA --> COMMITTING_EVENT: Delta Conforms to World Rules
  VERIFYING_DELTA --> REFLECTION_LOOP: Delta Contains Inconsistencies
  
  REFLECTION_LOOP --> EXTRACTING_DELTA: Re-prompt LLM with Critique (max 2 cycles)
  REFLECTION_LOOP --> FALLBACK_REJECTION: Max Cycles Exceeded
  FALLBACK_REJECTION --> [*]: 500 Generation Anomaly
  
  COMMITTING_EVENT --> BROADCASTING_MUTATIONS: Transactional DB & Cache Update
  BROADCASTING_MUTATIONS --> COMPLETE: Final Turn Receipt Dispatched
  COMPLETE --> [*]
```

---

## 3. Core Software Design Patterns Applied

### 1. Strategy Pattern (`LLMProviderStrategy`)
Decouples prompt execution from concrete model vendors (Anthropic Claude 3.5 Sonnet, OpenAI GPT-4o, AWS Bedrock). Enables seamless fallback cascades if a primary provider encounters rate limits or upstream 5xx errors.

### 2. Repository & Unit-of-Work Pattern (`GraphRepository`, `EventStore`)
Isolates PostgreSQL DDL operations, recursive CTE traversals, and transactional outbox commits from domain logic. The Graph Engine interacts with domain entities (`GraphNode`, `GraphEdge`), while repositories handle serialization and SQL dialect details.

### 3. Event Sourcing Pattern (`EventStore`, `NarrativeEvent`)
Instead of directly overwriting database rows to update character locations or inventory counts, every state modification is recorded as an immutable delta event. The current world state is a projection of past events, enabling instantaneous branching and rollbacks.

### 4. Specification / Rule Pattern (`RuleEngine`, `CausalityRule`)
Encapsulates world logic rules (e.g. `CanTraverseEdgeRule`, `PossessesItemRule`, `DoorAccessibilityRule`) as individual, testable specification classes that execute without LLM involvement.
