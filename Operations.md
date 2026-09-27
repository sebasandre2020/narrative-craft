# Operations & Production Runbook: Narrative-Craft

**Status**: Operational guide and local engineering runbook. [Index](Index.md) · [Architecture](Architecture.md)

---

## 1. Local Development Runbook

### Prerequisites
- Python 3.12+ installed
- Docker & Docker Compose v2+
- Git

### Quickstart Execution Steps
```powershell
# 1. Initialize Python environment
cd C:\Repositories\GHProjects\narrative-craft
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# 2. Run automated scaffold and integrity checks
python scripts/validate_scaffold.py

# 3. Environment configuration
Copy-Item .env.example .env

# 4. Launch dependent infrastructure
docker compose config --quiet
docker compose up -d postgres redis qdrant

# 5. Verify database initialization
docker compose exec postgres psql -U narrative -d narrative_craft -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"

# 6. Verify Qdrant Vector Engine
curl http://localhost:6333/collections

# 7. Teardown
docker compose down
```

---

## 2. Environment Configuration Matrix

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Deployment tier: `development`, `staging`, `production` |
| `PORT` | `8000` | Application HTTP listening port |
| `DATABASE_URL` | `postgresql+asyncpg://narrative:narrative_secret@localhost:5432/narrative_craft` | Primary relational & event store DSN |
| `REDIS_URL` | `redis://localhost:6379/0` | Active session & graph cache DSN |
| `QDRANT_HOST` | `localhost` | Qdrant vector database hostname |
| `QDRANT_PORT` | `6333` | Qdrant REST API port |
| `LLM_PRIMARY_PROVIDER`| `anthropic` | Primary foundation model: `anthropic`, `openai`, `bedrock` |
| `ANTHROPIC_API_KEY` | `sk-ant-test...` | Secret API key for Claude 3.5 Sonnet |
| `OPENAI_API_KEY` | `sk-test...` | Fallback API key for GPT-4o |
| `LANGFUSE_PUBLIC_KEY` | `pk-lf-...` | Langfuse tracing telemetry public key |
| `LANGFUSE_SECRET_KEY` | `sk-lf-...` | Langfuse tracing telemetry secret key |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse observability endpoint |

---

## 3. Observability & Diagnostic Metrics

Narrative-Craft exposes standard Prometheus metrics at `/metrics`:

- `narrative_turn_duration_seconds{quantile="0.95"}`: p95 turn latency from request admission to final complete SSE event.
- `narrative_rule_violations_total{rule="proximity"}`: Counter tracking actions blocked by deterministic pre-conditions.
- `narrative_graph_hop_traversal_duration_ms`: Latency of $k$-hop neighborhood extractions.
- `narrative_reflection_cycles_total`: Counter tracking how often LLM-generated deltas require self-correction.
- `narrative_events_committed_total`: Total count of immutable narrative events written to the append-only log.

### Health Probes
- **Liveness (`GET /health/live`)**: Returns `200 {"status": "alive"}` if FastAPI process is responsive.
- **Readiness (`GET /health/ready`)**: Performs active ping checks to PostgreSQL (`SELECT 1`), Redis (`PING`), and Qdrant cluster health. Returns `503 Service Unavailable` if any dependency is down.

---

## 4. Disaster Recovery & Incident Runbooks

### Runbook A: Stale Session Lock in Redis
*Symptom*: Client receives `409 Conflict: Session locked by another active turn` indefinitely after an aborted client connection.
*Resolution*:
```bash
# Query active session lock key
docker compose exec redis redis-cli KEYS "lock:timeline:*"
# Delete specific stuck timeline lock (TTL is normally 30s)
docker compose exec redis redis-cli DEL "lock:timeline:<TIMELINE_ID>"
```

### Runbook B: Reconstructing World State from Event Log
*Symptom*: In-memory or cached world graph is suspected of desynchronization or corruption.
*Resolution*:
Execute the deterministic state replay command to wipe the Redis active projection and re-apply all events from `sequence_number = 1` up to the latest committed event:
```bash
# Triggers replay worker without downtime
curl -X POST "$NARRATIVE_URL/v1/timelines/$TIMELINE_ID/rebuild-state" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Runbook C: Database Vacuum & Event Log Partitioning
In high-throughput worlds generating millions of events, the `narrative_events` table utilizes PostgreSQL declarative partitioning by `world_id`. Ensure monthly autovacuum execution:
```sql
VACUUM (ANALYZE, VERBOSE) narrative_events;
```
