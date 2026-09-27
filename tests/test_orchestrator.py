"""Unit tests for SceneOrchestrator."""

import pytest
from uuid import uuid4
from src.ai.adapters import MockLLMAdapter
from src.ai.orchestrator import SceneOrchestrator
from src.domain.graph import WorldGraph


@pytest.mark.asyncio
async def test_orchestrator_turn_stream_execution():
    orchestrator = SceneOrchestrator(adapter=MockLLMAdapter())
    graph = WorldGraph.create_default_world()
    timeline_id = uuid4()

    events = []
    async for chunk in orchestrator.execute_turn_stream(
        timeline_id=timeline_id,
        character_id="char_vespera",
        action="Unlock the iron portcullis with the silver key",
        graph=graph,
        sequence_number=1,
    ):
        events.append(chunk)

    event_types = [e["event"] for e in events]
    assert "token" in event_types
    assert "graph_delta" in event_types
    assert "complete" in event_types

    # Verify complete event content
    complete_event = next(e for e in events if e["event"] == "complete")
    data = complete_event["data"]
    assert data["status"] == "COMMITTED"
    assert data["sequence_number"] == 1
    assert "portcullis" in data["prose"].lower() or "key" in data["prose"].lower()

    # Verify graph mutation was applied
    gate = graph.get_node("gate_iron_portcullis")
    assert gate.properties["locked"] is False


@pytest.mark.asyncio
async def test_orchestrator_precondition_rejection():
    orchestrator = SceneOrchestrator(adapter=MockLLMAdapter())
    graph = WorldGraph.create_default_world()
    # Remove key
    graph.remove_edge("char_vespera", "item_silver_key", "possesses")

    with pytest.raises(ValueError) as excinfo:
        async for _ in orchestrator.execute_turn_stream(
            timeline_id=uuid4(),
            character_id="char_vespera",
            action="Unlock the iron portcullis with the silver key",
            graph=graph,
            sequence_number=1,
        ):
            pass

    assert "does not possess required key" in str(excinfo.value)
