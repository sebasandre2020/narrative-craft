"""Deterministic Rule Engine for Causality & Physical Guardrails."""

import re
from typing import Optional
from pydantic import BaseModel

from src.domain.graph import WorldGraph
from src.domain.models import WorldDelta


class RuleValidationResult(BaseModel):
    is_valid: bool
    reason: Optional[str] = None
    rule_name: Optional[str] = None


class RuleEngine:
    """Evaluates physical causality, inventory, and spatial proximity rules without LLM involvement."""

    @staticmethod
    def validate_preconditions(character_id: str, action: str, graph: WorldGraph) -> RuleValidationResult:
        """Validates that a character's attempted action is physically possible given the active graph."""
        action_lower = action.lower()

        # 1. Existence check
        char_node = graph.get_node(character_id)
        if not char_node:
            return RuleValidationResult(
                is_valid=False,
                reason=f"Character '{character_id}' does not exist in world state.",
                rule_name="CharacterExistsRule",
            )

        # 2. Location proximity check
        loc_edges = graph.get_edges(source=character_id, relation="located_in")
        if not loc_edges:
            return RuleValidationResult(
                is_valid=False,
                reason=f"Character '{character_id}' has no assigned location in world graph.",
                rule_name="LocationProximityRule",
            )
        current_loc_id = loc_edges[0].target

        # 3. Key & Barrier unlock check
        if any(w in action_lower for w in ["unlock", "open", "insert key", "silver key"]):
            # Check if there is an interactable barrier in the current location
            barriers = graph.get_edges(target=current_loc_id, relation="located_in")
            barrier_items = [
                b.source for b in barriers
                if graph.get_node(b.source) and graph.get_node(b.source).properties.get("locked") is not None
            ]

            # If user mentions a specific locked barrier or gate
            for barrier_id in barrier_items:
                barrier_node = graph.get_node(barrier_id)
                if not barrier_node:
                    continue
                req_key = barrier_node.properties.get("key_requirement")
                if req_key:
                    # Check if character possesses the required key
                    has_key = any(
                        e.target == req_key
                        for e in graph.get_edges(source=character_id, relation="possesses")
                    )
                    # If user is trying to unlock and doesn't have the key
                    if not has_key and (req_key.lower() in action_lower or "key" in action_lower or barrier_id.lower() in action_lower or "gate" in action_lower):
                        return RuleValidationResult(
                            is_valid=False,
                            reason=f"Precondition rule violation: Character '{character_id}' does not possess required key '{req_key}'.",
                            rule_name="PossessesItemRule",
                        )

        # 4. Movement / Traversal check
        if any(w in action_lower for w in ["move to", "go to", "travel to", "enter", "step into", "walk to"]):
            # Find candidate target location mentioned in action
            all_loc_nodes = [
                n for n in graph.to_dict()["nodes"] if n["type"] == "location" and n["id"] != current_loc_id
            ]
            for candidate in all_loc_nodes:
                cand_id = candidate["id"]
                cand_label = candidate["label"].lower()
                if cand_id.lower() in action_lower or cand_label in action_lower:
                    # Verify spatial adjacency
                    adj_edges = graph.get_edges(source=current_loc_id, target=cand_id, relation="adjacent_to")
                    if not adj_edges:
                        # Also check reverse adjacency
                        adj_edges = graph.get_edges(source=cand_id, target=current_loc_id, relation="adjacent_to")

                    if not adj_edges:
                        return RuleValidationResult(
                            is_valid=False,
                            reason=f"Precondition rule violation: Location '{cand_id}' is not adjacent to current location '{current_loc_id}'.",
                            rule_name="CanTraverseEdgeRule",
                        )

                    # Check barrier lock status
                    barrier_id = adj_edges[0].properties.get("barrier")
                    if barrier_id:
                        b_node = graph.get_node(barrier_id)
                        if b_node and b_node.properties.get("locked") is True and not any(w in action_lower for w in ["unlock", "open"]):
                            return RuleValidationResult(
                                is_valid=False,
                                reason=f"Precondition rule violation: Barrier '{barrier_id}' is locked.",
                                rule_name="BarrierLockedRule",
                            )

        return RuleValidationResult(is_valid=True)

    @staticmethod
    def verify_delta(delta: WorldDelta, graph: WorldGraph) -> RuleValidationResult:
        """Verifies that an LLM-proposed WorldDelta does not violate world invariants."""
        # 1. Delta mutation validity
        for mutation in delta.mutations:
            act = mutation.action.upper()
            if act in ["UPDATE_NODE_PROPERTY", "REMOVE_NODE"] and mutation.node_id:
                if not graph.get_node(mutation.node_id):
                    # Check if an earlier mutation added it
                    earlier_adds = [
                        m for m in delta.mutations
                        if m.action.upper() == "ADD_NODE" and m.node_id == mutation.node_id
                    ]
                    if not earlier_adds:
                        return RuleValidationResult(
                            is_valid=False,
                            reason=f"Delta consistency violation: Cannot modify non-existent node '{mutation.node_id}'.",
                            rule_name="DeltaNodeIntegrityRule",
                        )

            # Prevent spontaneous key creation without source
            if act == "ADD_EDGE" and mutation.relation == "possesses":
                item_node = graph.get_node(mutation.target)
                if not item_node and not any(m.action == "ADD_NODE" and m.node_id == mutation.target for m in delta.mutations):
                    return RuleValidationResult(
                        is_valid=False,
                        reason=f"Delta consistency violation: Cannot possess non-existent item '{mutation.target}'.",
                        rule_name="DeltaInventoryIntegrityRule",
                    )

        return RuleValidationResult(is_valid=True)
