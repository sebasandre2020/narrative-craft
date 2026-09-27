"""In-memory Graph Engine backed by NetworkX."""

from typing import Any, Dict, List, Optional
import networkx as nx
import yaml

from src.domain.models import GraphEdge, GraphMutation, GraphNode, WorldDelta


class WorldGraph:
    """Relational Property Graph representing active world narrative state."""

    def __init__(self):
        # We use MultiDiGraph to allow multiple relations between the same pair of nodes
        self.g = nx.MultiDiGraph()

    def add_node(self, node: GraphNode) -> None:
        """Adds or updates a node in the graph."""
        self.g.add_node(
            node.id,
            id=node.id,
            type=node.type,
            label=node.label,
            properties=dict(node.properties),
        )

    def remove_node(self, node_id: str) -> bool:
        """Removes a node and its incident edges."""
        if self.g.has_node(node_id):
            self.g.remove_node(node_id)
            return True
        return False

    def add_edge(self, edge: GraphEdge) -> None:
        """Adds a directed relation edge between source and target."""
        if not self.g.has_node(edge.source):
            self.g.add_node(edge.source, id=edge.source, type="concept", label=edge.source, properties={})
        if not self.g.has_node(edge.target):
            self.g.add_node(edge.target, id=edge.target, type="concept", label=edge.target, properties={})

        self.g.add_edge(
            edge.source,
            edge.target,
            key=edge.relation,
            relation=edge.relation,
            properties=dict(edge.properties),
        )

    def remove_edge(self, source: str, target: str, relation: str) -> bool:
        """Removes a specific relation edge between source and target."""
        if self.g.has_edge(source, target, key=relation):
            self.g.remove_edge(source, target, key=relation)
            return True
        return False

    def update_node_property(self, node_id: str, key: str, value: Any) -> bool:
        """Updates a property on a node."""
        if self.g.has_node(node_id):
            self.g.nodes[node_id]["properties"][key] = value
            return True
        return False

    def update_edge_property(self, source: str, target: str, relation: str, key: str, value: Any) -> bool:
        """Updates a property on an edge."""
        if self.g.has_edge(source, target, key=relation):
            self.g.edges[source, target, relation]["properties"][key] = value
            return True
        return False

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieves a node by ID."""
        if self.g.has_node(node_id):
            data = self.g.nodes[node_id]
            return GraphNode(
                id=node_id,
                type=data.get("type", "concept"),
                label=data.get("label", node_id),
                properties=data.get("properties", {}),
            )
        return None

    def get_edges(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        relation: Optional[str] = None,
    ) -> List[GraphEdge]:
        """Queries edges matching optional filter criteria."""
        results = []
        for u, v, k, data in self.g.edges(keys=True, data=True):
            if source is not None and u != source:
                continue
            if target is not None and v != target:
                continue
            if relation is not None and k != relation:
                continue
            results.append(
                GraphEdge(
                    source=u,
                    target=v,
                    relation=k,
                    properties=data.get("properties", {}),
                )
            )
        return results

    def apply_mutation(self, mutation: GraphMutation) -> bool:
        """Applies a single discrete state mutation."""
        action = mutation.action.upper()
        if action == "ADD_NODE" and mutation.node_id:
            node = GraphNode(
                id=mutation.node_id,
                type="concept",
                label=mutation.node_id,
                properties=mutation.value if isinstance(mutation.value, dict) else {},
            )
            self.add_node(node)
            return True
        elif action == "REMOVE_NODE" and mutation.node_id:
            return self.remove_node(mutation.node_id)
        elif action == "UPDATE_NODE_PROPERTY" and mutation.node_id and mutation.key:
            return self.update_node_property(mutation.node_id, mutation.key, mutation.value)
        elif action == "ADD_EDGE" and mutation.source and mutation.target and mutation.relation:
            edge = GraphEdge(
                source=mutation.source,
                target=mutation.target,
                relation=mutation.relation,
                properties=mutation.value if isinstance(mutation.value, dict) else {},
            )
            self.add_edge(edge)
            return True
        elif action == "REMOVE_EDGE" and mutation.source and mutation.target and mutation.relation:
            return self.remove_edge(mutation.source, mutation.target, mutation.relation)
        elif action == "UPDATE_EDGE_PROPERTY" and mutation.source and mutation.target and mutation.relation and mutation.key:
            return self.update_edge_property(mutation.source, mutation.target, mutation.relation, mutation.key, mutation.value)
        return False

    def apply_delta(self, delta: WorldDelta) -> None:
        """Applies a full WorldDelta containing multiple mutations."""
        for mut in delta.mutations:
            self.apply_mutation(mut)

    def extract_subgraph(self, center_id: str, hops: int = 2) -> Dict[str, Any]:
        """Extracts k-hop neighborhood around a center node."""
        if not self.g.has_node(center_id):
            return {"center_id": center_id, "hops": hops, "nodes": [], "edges": []}

        # Convert to undirected view for radial traversal
        undirected = self.g.to_undirected()
        lengths = nx.single_source_shortest_path_length(undirected, center_id, cutoff=hops)
        sub_nodes_ids = set(lengths.keys())

        nodes_list = []
        for n in sub_nodes_ids:
            data = self.g.nodes[n]
            nodes_list.append({
                "id": n,
                "type": data.get("type", "concept"),
                "label": data.get("label", n),
                "properties": data.get("properties", {}),
            })

        edges_list = []
        for u, v, k, data in self.g.edges(sub_nodes_ids, keys=True, data=True):
            if v in sub_nodes_ids:
                edges_list.append({
                    "source": u,
                    "target": v,
                    "relation": k,
                    "properties": data.get("properties", {}),
                })

        return {
            "center_id": center_id,
            "hops": hops,
            "nodes": nodes_list,
            "edges": edges_list,
        }

    def to_yaml(self, center_id: Optional[str] = None, hops: int = 2) -> str:
        """Serializes current graph or k-hop neighborhood to clean YAML for prompt context."""
        if center_id:
            data = self.extract_subgraph(center_id, hops)
        else:
            data = self.to_dict()
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes complete graph to dictionary."""
        nodes = []
        for n, data in self.g.nodes(data=True):
            nodes.append({
                "id": n,
                "type": data.get("type", "concept"),
                "label": data.get("label", n),
                "properties": data.get("properties", {}),
            })
        edges = []
        for u, v, k, data in self.g.edges(keys=True, data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": k,
                "properties": data.get("properties", {}),
            })
        return {"nodes": nodes, "edges": edges}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldGraph":
        """Reconstructs WorldGraph from dictionary."""
        graph = cls()
        for n in data.get("nodes", []):
            graph.add_node(GraphNode(
                id=n["id"],
                type=n.get("type", "concept"),
                label=n.get("label", n["id"]),
                properties=n.get("properties", {}),
            ))
        for e in data.get("edges", []):
            graph.add_edge(GraphEdge(
                source=e["source"],
                target=e["target"],
                relation=e["relation"],
                properties=e.get("properties", {}),
            ))
        return graph

    @classmethod
    def create_default_world(cls) -> "WorldGraph":
        """Seeds the default dark fantasy world as defined in 001_init_schema.sql."""
        graph = cls()
        # Seed nodes
        graph.add_node(GraphNode(
            id="char_vespera",
            type="character",
            label="Lady Vespera",
            properties={"class": "Arcane Inquisitor", "hp": 100, "status": "alert"},
        ))
        graph.add_node(GraphNode(
            id="loc_crypt",
            type="location",
            label="Crypt of Ancients",
            properties={"lighting": "dim", "terrain": "stone_catacombs"},
        ))
        graph.add_node(GraphNode(
            id="loc_antechamber",
            type="location",
            label="Damp Antechamber",
            properties={"lighting": "dark", "terrain": "collapsed_tunnel"},
        ))
        graph.add_node(GraphNode(
            id="item_silver_key",
            type="item",
            label="Engraved Silver Key",
            properties={"weight_kg": 0.1, "material": "silver", "magical": False},
        ))
        graph.add_node(GraphNode(
            id="gate_iron_portcullis",
            type="item",
            label="Rusted Iron Portcullis",
            properties={"locked": True, "key_requirement": "item_silver_key"},
        ))

        # Seed edges
        graph.add_edge(GraphEdge(source="char_vespera", target="loc_crypt", relation="located_in"))
        graph.add_edge(GraphEdge(source="char_vespera", target="item_silver_key", relation="possesses", properties={"equipped": True}))
        graph.add_edge(GraphEdge(source="gate_iron_portcullis", target="loc_crypt", relation="located_in"))
        graph.add_edge(GraphEdge(source="loc_crypt", target="loc_antechamber", relation="adjacent_to", properties={"barrier": "gate_iron_portcullis"}))

        return graph
