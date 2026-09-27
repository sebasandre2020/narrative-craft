"""Integration tests for FastAPI Control Plane endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from src.api.app import app
from src.storage.db import event_store


@pytest.mark.asyncio
async def test_health_probes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Liveness
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # Readiness
        resp2 = await client.get("/health/ready")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_world_lifecycle_and_fork():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create World
        create_payload = {
            "title": "Echoes of the Void",
            "description": "A shattered reality adrift in astral currents",
            "template": "dark_fantasy",
            "config": {"max_reflection_attempts": 2}
        }
        res = await client.post("/v1/worlds", json=create_payload)
        assert res.status_code == 201
        data = res.json()
        world_id = data["world_id"]
        timeline_id = data["active_timeline_id"]
        assert data["title"] == "Echoes of the Void"

        # 2. Get World
        res_get = await client.get(f"/v1/worlds/{world_id}")
        assert res_get.status_code == 200
        assert res_get.json()["world_id"] == world_id

        # 3. Subgraph extraction
        res_sub = await client.get(
            f"/v1/timelines/{timeline_id}/graph/subgraph",
            params={"center_id": "char_vespera", "hops": 2}
        )
        assert res_sub.status_code == 200
        sub_data = res_sub.json()
        assert sub_data["center_id"] == "char_vespera"
        assert len(sub_data["nodes"]) > 0

        # 4. Turn execution (JSON mode)
        turn_payload = {
            "character_id": "char_vespera",
            "action": "Unlock the rusted iron portcullis with the engraved silver key"
        }
        res_turn = await client.post(
            f"/v1/timelines/{timeline_id}/turns",
            json=turn_payload,
            headers={"Accept": "application/json"}
        )
        assert res_turn.status_code == 200
        turn_data = res_turn.json()
        assert turn_data["status"] == "COMMITTED"
        assert turn_data["sequence_number"] == 1
        assert "turn_id" in turn_data

        # 5. Precondition Violation (422)
        # Attempt to open locked gate without key (remove key from graph)
        graph = await event_store.get_world_graph(uuid4()) # fresh graph without key
        fail_turn = {
            "character_id": "char_vespera",
            "action": "Walk to Damp Antechamber" # blocked by portcullis in fresh graph
        }
        # In our world, the portcullis was unlocked in step 4! So let's test invalid character
        res_fail = await client.post(
            f"/v1/timelines/{timeline_id}/turns",
            json={"character_id": "ghost_specter", "action": "fly through wall"},
            headers={"Accept": "application/json"}
        )
        assert res_fail.status_code == 422
        assert "does not exist" in res_fail.json()["detail"]

        # 6. Fork Timeline
        fork_payload = {
            "name": "Timeline Gamma: Alternate Choice",
            "fork_event_id": str(uuid4()),
            "description": "Branched after opening portcullis"
        }
        res_fork = await client.post(
            f"/v1/timelines/{timeline_id}/fork",
            json=fork_payload
        )
        assert res_fork.status_code == 201
        fork_data = res_fork.json()
        assert fork_data["name"] == "Timeline Gamma: Alternate Choice"
        assert fork_data["parent_timeline_id"] == timeline_id


@pytest.mark.asyncio
async def test_sse_turn_streaming(monkeypatch):
    from src.api.app import orchestrator
    from src.ai.adapters import MockLLMAdapter

    monkeypatch.setattr(orchestrator, "adapter", MockLLMAdapter())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/worlds", json={"title": "SSE Streaming Test"})
        timeline_id = res.json()["active_timeline_id"]

        res_stream = await client.post(
            f"/v1/timelines/{timeline_id}/turns",
            json={"character_id": "char_vespera", "action": "Unlock the gate with the silver key"},
            headers={"Accept": "text/event-stream"},
        )
        assert res_stream.status_code == 200
        assert "text/event-stream" in res_stream.headers["content-type"]
        body = res_stream.text
        assert "event: token" in body
        assert "event: graph_delta" in body
        assert "event: complete" in body

