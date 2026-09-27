"""Scene Orchestrator and Cyclic Agentic State Machine."""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID, uuid4

from src.ai.adapters import BaseLLMAdapter, LLMAdapterFactory
from src.domain.graph import WorldGraph
from src.domain.models import NarrativeEvent, NarrativeTurnResponse, WorldDelta
from src.domain.rules import RuleEngine, RuleValidationResult

logger = logging.getLogger("SceneOrchestrator")


class SceneOrchestrator:
    """Coordinates turn lifecycle, k-hop graph context compilation, and cyclic self-correction."""

    def __init__(self, adapter: Optional[BaseLLMAdapter] = None):
        self.adapter = adapter or LLMAdapterFactory.get_adapter()

    async def execute_turn_stream(
        self,
        timeline_id: UUID,
        character_id: str,
        action: str,
        graph: WorldGraph,
        sequence_number: int,
        lore_service: Optional[Any] = None,
        max_reflection_attempts: int = 2,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Executes a narrative turn, yielding SSE-compatible event dictionaries:
        - {"event": "token", "data": {"text": "..."}}
        - {"event": "graph_delta", "data": {"mutations": [...], "new_facts": [...]}}
        - {"event": "complete", "data": {...}}
        """
        turn_id = f"turn_{uuid4().hex[:12]}"

        # 1. Precondition Validation (Deterministic Guardrail)
        rule_res: RuleValidationResult = RuleEngine.validate_preconditions(character_id, action, graph)
        if not rule_res.is_valid:
            logger.warning("Precondition failed for action '%s': %s", action, rule_res.reason)
            raise ValueError(rule_res.reason)

        # 2. Extract k-hop Subgraph
        subgraph = graph.extract_subgraph(character_id, hops=2)
        graph_yaml = graph.to_yaml(center_id=character_id, hops=2)

        # 3. Retrieve Lore
        retrieved_lore: List[Dict[str, Any]] = []
        if lore_service:
            retrieved_lore = await lore_service.query_lore(action, limit=2)
        else:
            retrieved_lore = [
                {"title": "Crypt of the Iron Citadel", "excerpt": "Constructed in the First Era to imprison the ancient arcana."}
            ]

        lore_context = "\n".join([f"- {item.get('title')}: {item.get('excerpt')}" for item in retrieved_lore])

        # 4. Stream Prose Generation
        system_prompt = (
            "You are the Lead Narrative Simulation Master of a dark fantasy world. "
            "Narrate the immediate scene reaction to the character's action in vivid, literary prose. "
            "Strictly adhere to the provided physical graph entities, locations, and inventories.\n\n"
            f"Relational Graph Context:\n{graph_yaml}\n\n"
            f"Canon Lore:\n{lore_context}"
        )
        user_prompt = f"Character '{character_id}' attempts action: '{action}'."

        accumulated_prose = []
        async for token in self.adapter.stream_prose(system_prompt, user_prompt):
            accumulated_prose.append(token)
            yield {
                "event": "token",
                "data": {"text": token}
            }

        full_prose = "".join(accumulated_prose)

        # 5. Delta Extraction & Cyclic Reflection
        delta: Optional[WorldDelta] = None
        critique: Optional[str] = None
        reflection_count = 0

        while reflection_count <= max_reflection_attempts:
            delta = await self.adapter.generate_delta(
                prose=full_prose,
                graph_yaml=graph_yaml,
                action=action,
                critique=critique,
            )
            verification: RuleValidationResult = RuleEngine.verify_delta(delta, graph)
            if verification.is_valid:
                break
            else:
                reflection_count += 1
                critique = verification.reason
                logger.info("Delta verification failed (attempt %d): %s", reflection_count, critique)

        if not delta:
            delta = WorldDelta(mutations=[])

        # 6. Apply Mutations to in-memory graph
        graph.apply_delta(delta)

        # 7. Yield Delta Event
        yield {
            "event": "graph_delta",
            "data": delta.model_dump()
        }

        # 8. Yield Complete Event
        yield {
            "event": "complete",
            "data": {
                "turn_id": turn_id,
                "timeline_id": str(timeline_id),
                "sequence_number": sequence_number,
                "status": "COMMITTED",
                "prose": full_prose,
                "graph_delta": delta.model_dump(),
                "lore_citations": retrieved_lore,
            }
        }
