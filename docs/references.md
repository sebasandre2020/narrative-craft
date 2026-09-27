# Technical References & Foundations: Narrative-Craft

## 1. Graph RAG & Knowledge Representation
- **Edge, D. et al. (2024)**: *"From Local to Global: A Graph RAG Approach to Query-Focused Summarization"*. Microsoft Research. Demonstrates that combining structured entity property graphs with dense vector embeddings significantly outperforms pure vector search on thematic and relational queries.
- **Hogan, A. et al. (2021)**: *"Knowledge Graphs"*. ACM Computing Surveys. Establishes the formal definitions of directed property graphs, node attribution, and multigraph schema modeling utilized by Narrative-Craft.

## 2. Event Sourcing & Distributed State Systems
- **Fowler, M. (2005)**: *"Event Sourcing"*. martinfowler.com. Defines the core pattern of capturing all changes to application state as a sequence of immutable events.
- **Young, G. (2010)**: *"CQRS Documents by Greg Young"*. Establishes the separation between write-side command appending and read-side graph projection querying.
- **Kleppmann, M. (2017)**: *"Designing Data-Intensive Applications"*. O'Reilly Media. In-depth analysis of append-only logs, idempotency, and linearized state reconstruction.

## 3. Agentic State Machines & Protocols
- **LangChain / LangGraph Documentation (2024)**: Cyclic state machine design, conditional edge routing, and Human-in-the-Loop checkpointing patterns.
- **Anthropic Model Context Protocol (MCP) Specification (2024)**: Standardized JSON-RPC 2.0 protocol for exposing dynamic tools, resources, and prompt context to AI client runtimes.
- **IETF RFC 7807 (2016)**: *"Problem Details for HTTP APIs"*. Standardized format for delivering semantic machine-readable error responses.
- **OpenAPI Specification v3.1.0 (2021)**: Full JSON Schema 2020-12 alignment for strict RESTful contract definition.
