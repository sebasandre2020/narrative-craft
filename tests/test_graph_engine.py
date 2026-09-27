"""Unit tests for NetworkX WorldGraph Engine."""

import pytest
from src.domain.graph import WorldGraph
from src.domain.models import GraphEdge, GraphMutation, GraphNode, WorldDelta


def test_graph_initialization_and_nodes():
    graph = WorldGraph()
    node = GraphNode(
        id="char_elena",
        type="character",
        label="Elena Vance",
        properties={"hp": 100, "mana": 50},
    )
    graph.add_node(node)

    retrieved = graph.get_node("char_elena")
    assert retrieved is not None
    assert retrieved.id == "char_elena"
    assert retrieved.properties["hp"] == 100

    # Update property
    graph.update_node_property("char_elena", "hp", 85)
    assert graph.get_node("char_elena").properties["hp"] == 85

    # Remove node
    assert graph.remove_node("char_elena") is True
    assert graph.get_node("char_elena") is None


def test_graph_edges_and_relations():
    graph = WorldGraph()
    graph.add_node(GraphNode(id="char_elena", type="character", label="Elena"))
    graph.add_node(GraphNode(id="loc_tower", type="location", label="Clock Tower"))

    edge = GraphEdge(
        source="char_elena",
        target="loc_tower",
        relation="located_in",
        properties={"status": "sneaking"},
    )
    graph.add_edge(edge)

    edges = graph.get_edges(source="char_elena", relation="located_in")
    assert len(edges) == 1
    assert edges[0].target == "loc_tower"
    assert edges[0].properties["status"] == "sneaking"

    # Remove edge
    assert graph.remove_edge("char_elena", "loc_tower", "located_in") is True
    assert len(graph.get_edges(source="char_elena")) == 0


def test_subgraph_extraction():
    graph = WorldGraph.create_default_world()

    # 1-hop extraction around char_vespera
    sub1 = graph.extract_subgraph("char_vespera", hops=1)
    node_ids_1 = [n["id"] for n in sub1["nodes"]]
    assert "char_vespera" in node_ids_1
    assert "loc_crypt" in node_ids_1
    assert "item_silver_key" in node_ids_1

    # 2-hop extraction should reach adjacent locations and barriers
    sub2 = graph.extract_subgraph("char_vespera", hops=2)
    node_ids_2 = [n["id"] for n in sub2["nodes"]]
    assert "loc_antechamber" in node_ids_2
    assert "gate_iron_portcullis" in node_ids_2


def test_apply_world_delta():
    graph = WorldGraph.create_default_world()
    delta = WorldDelta(
        mutations=[
            GraphMutation(
                action="UPDATE_NODE_PROPERTY",
                node_id="gate_iron_portcullis",
                key="locked",
                value=False,
            ),
            GraphMutation(
                action="ADD_NODE",
                node_id="item_golden_chalice",
                value={"material": "gold"},
            ),
            GraphMutation(
                action="ADD_EDGE",
                source="item_golden_chalice",
                target="loc_crypt",
                relation="located_in",
            ),
        ]
    )
    graph.apply_delta(delta)

    # Check portcullis unlocked
    gate = graph.get_node("gate_iron_portcullis")
    assert gate.properties["locked"] is False

    # Check chalice added and placed
    chalice = graph.get_node("item_golden_chalice")
    assert chalice is not None
    assert len(graph.get_edges(source="item_golden_chalice", relation="located_in")) == 1


def test_yaml_export():
    graph = WorldGraph.create_default_world()
    yaml_str = graph.to_yaml(center_id="char_vespera", hops=1)
    assert "char_vespera" in yaml_str
    assert "loc_crypt" in yaml_str
