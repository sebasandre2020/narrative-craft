"""Unit tests for Deterministic Causality and Precondition Rule Engine."""

import pytest
from src.domain.graph import WorldGraph
from src.domain.models import GraphMutation, WorldDelta
from src.domain.rules import RuleEngine, RuleValidationResult


def test_character_existence_rule():
    graph = WorldGraph.create_default_world()
    res = RuleEngine.validate_preconditions("non_existent_character", "explore crypt", graph)
    assert res.is_valid is False
    assert "does not exist" in res.reason


def test_key_possession_rule_success():
    graph = WorldGraph.create_default_world()
    # Lady Vespera has the silver key in the default seed
    res = RuleEngine.validate_preconditions(
        "char_vespera",
        "Insert the silver key into the rusted lock of the gate",
        graph,
    )
    assert res.is_valid is True


def test_key_possession_rule_failure():
    graph = WorldGraph.create_default_world()
    # Remove key from Vespera's possession
    graph.remove_edge("char_vespera", "item_silver_key", "possesses")

    res = RuleEngine.validate_preconditions(
        "char_vespera",
        "Unlock the gate using the silver key",
        graph,
    )
    assert res.is_valid is False
    assert "does not possess required key" in res.reason


def test_barrier_locked_traversal_failure():
    graph = WorldGraph.create_default_world()
    # Attempting to move into antechamber while portcullis is locked
    res = RuleEngine.validate_preconditions(
        "char_vespera",
        "Move to Damp Antechamber",
        graph,
    )
    assert res.is_valid is False
    assert "locked" in res.reason.lower()


def test_barrier_traversal_success_after_unlock():
    graph = WorldGraph.create_default_world()
    # Unlock the portcullis
    graph.update_node_property("gate_iron_portcullis", "locked", False)

    res = RuleEngine.validate_preconditions(
        "char_vespera",
        "Move to Damp Antechamber",
        graph,
    )
    assert res.is_valid is True


def test_non_adjacent_traversal_failure():
    graph = WorldGraph.create_default_world()
    # Add a distant room with no edge
    from src.domain.models import GraphNode
    graph.add_node(GraphNode(id="loc_sky_castle", type="location", label="Sky Castle"))

    res = RuleEngine.validate_preconditions(
        "char_vespera",
        "Walk to Sky Castle",
        graph,
    )
    assert res.is_valid is False
    assert "not adjacent" in res.reason.lower()


def test_verify_delta_integrity():
    graph = WorldGraph.create_default_world()

    # Valid delta
    valid_delta = WorldDelta(
        mutations=[
            GraphMutation(action="UPDATE_NODE_PROPERTY", node_id="gate_iron_portcullis", key="locked", value=False)
        ]
    )
    assert RuleEngine.verify_delta(valid_delta, graph).is_valid is True

    # Invalid delta: modifying phantom node
    invalid_delta = WorldDelta(
        mutations=[
            GraphMutation(action="UPDATE_NODE_PROPERTY", node_id="phantom_dragon", key="hp", value=500)
        ]
    )
    inv_res = RuleEngine.verify_delta(invalid_delta, graph)
    assert inv_res.is_valid is False
    assert "non-existent node" in inv_res.reason
