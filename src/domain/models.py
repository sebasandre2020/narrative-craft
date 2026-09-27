"""Domain models and Pydantic schemas for Narrative-Craft."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class NodeType(str, Enum):
    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    FACTION = "faction"
    CONCEPT = "concept"


class MutationAction(str, Enum):
    ADD_NODE = "ADD_NODE"
    REMOVE_NODE = "REMOVE_NODE"
    UPDATE_NODE_PROPERTY = "UPDATE_NODE_PROPERTY"
    ADD_EDGE = "ADD_EDGE"
    REMOVE_EDGE = "REMOVE_EDGE"
    UPDATE_EDGE_PROPERTY = "UPDATE_EDGE_PROPERTY"


class GraphNode(BaseModel):
    id: str
    type: str = Field(description="character, location, item, faction, or concept")
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class GraphMutation(BaseModel):
    action: str = Field(description="ADD_NODE, REMOVE_NODE, UPDATE_NODE_PROPERTY, ADD_EDGE, REMOVE_EDGE, UPDATE_EDGE_PROPERTY")
    node_id: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None
    relation: Optional[str] = None
    key: Optional[str] = None
    value: Optional[Any] = None

    model_config = ConfigDict(extra="ignore")


class FactEntry(BaseModel):
    entity_id: str
    fact: str


class WorldDelta(BaseModel):
    mutations: List[GraphMutation] = Field(default_factory=list)
    new_facts: List[FactEntry] = Field(default_factory=list)
    state_changes: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class NarrativeEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    timeline_id: UUID
    sequence_number: int = Field(ge=1)
    action_prompt: str
    narrative_prose: str
    graph_delta: WorldDelta
    lore_citations: List[Dict[str, Any]] = Field(default_factory=list)
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt": 0, "completion": 0})
    committed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="ignore")


# Request & Response Contracts for REST API

class HealthStatus(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    components: Dict[str, str] = Field(default_factory=dict)


class CreateWorldRequest(BaseModel):
    title: str
    description: Optional[str] = None
    template: Optional[str] = "dark_fantasy"
    config: Optional[Dict[str, Any]] = None


class WorldResponse(BaseModel):
    world_id: UUID
    title: str
    description: Optional[str] = None
    active_timeline_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NarrativeTurnRequest(BaseModel):
    character_id: str
    action: str
    intent: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


class NarrativeTurnResponse(BaseModel):
    turn_id: str
    timeline_id: UUID
    sequence_number: int
    status: str
    prose: str
    graph_delta: Optional[Dict[str, Any]] = None
    lore_citations: List[Dict[str, Any]] = Field(default_factory=list)
    committed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ForkTimelineRequest(BaseModel):
    name: str
    fork_event_id: UUID
    description: Optional[str] = None


class TimelineResponse(BaseModel):
    timeline_id: UUID
    world_id: UUID
    parent_timeline_id: Optional[UUID] = None
    fork_event_id: Optional[UUID] = None
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubgraphResponse(BaseModel):
    center_id: str
    hops: int
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
