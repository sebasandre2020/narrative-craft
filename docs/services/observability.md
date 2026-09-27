# Subsystem: Observability & Telemetry

## 1. Observability Architecture
Narrative-Craft incorporates full-lifecycle AI observability across three pillars:
1. **Langfuse Tracing**: Tracking LLM prompt versions, input tokens, output tokens, cost, and per-node latency.
2. **Prometheus Metrics**: High-resolution operational metrics for API admission, graph traversal speeds, and rule violation frequencies.
3. **Structured Correlation Logging**: Unified JSON logging stamped with `world_id`, `timeline_id`, and `turn_id`.

## 2. Langfuse Tracing Integration
Each turn initiates a parent trace in Langfuse tagged with the active session metadata:
- **Trace Name**: `narrative_turn_execution`
- **Spans**:
  - `precondition_validation`: Duration and rule results.
  - `subgraph_traversal`: Number of hops, nodes visited.
  - `qdrant_lore_query`: Query embedding latency and top score.
  - `llm_scene_generation`: Model name, temperature, TTFT, token usage.
  - `delta_verification`: Validation pass/fail status and reflection attempt count.
  - `database_commit`: PostgreSQL transaction latency.

## 3. Key Prometheus Metrics Exposed (`/metrics`)

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `narrative_turns_total` | Counter | `status`, `character_class` | Total turns attempted and outcome |
| `narrative_turn_duration_seconds` | Histogram | `quantile` | End-to-end turn duration |
| `narrative_ttft_seconds` | Histogram | `provider`, `model` | Time to first streaming token |
| `narrative_rule_violations_total` | Counter | `rule_name` | Precondition failures caught by guardrails |
| `narrative_reflection_loops_total` | Counter | `reason` | Count of LLM delta self-corrections |
| `narrative_graph_nodes_count` | Gauge | `world_id`, `node_type` | Total active nodes in world projection |
