"""Database and Event Store Repositories supporting asyncpg and in-memory fallback."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import asyncpg

from src.core.config import settings
from src.domain.graph import WorldGraph
from src.domain.models import NarrativeEvent, TimelineResponse, WorldResponse, WorldDelta

logger = logging.getLogger("StorageDB")


class EventStore:
    """Manages immutable narrative event stream and state projections."""

    def __init__(self):
        # In-memory storage structures for fast tests and fallback
        self._worlds: Dict[UUID, Dict[str, Any]] = {}
        self._timelines: Dict[UUID, Dict[str, Any]] = {}
        self._events: Dict[UUID, List[Dict[str, Any]]] = {}
        self._graphs: Dict[UUID, WorldGraph] = {}
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initializes PostgreSQL connection pool if available."""
        try:
            dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            self._pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=1,
                max_size=5,
                timeout=5.0,
            )
            logger.info("Connected to PostgreSQL at %s", dsn)
        except Exception as e:
            logger.warning("Could not connect to PostgreSQL (%s). Using In-Memory Repository.", e)
            self._pool = None

    async def close(self):
        """Closes connection pool."""
        if self._pool:
            await self._pool.close()

    async def create_world(
        self,
        title: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> WorldResponse:
        """Creates a new world and its root canonical timeline."""
        world_id = uuid4()
        timeline_id = uuid4()
        now = datetime.now(timezone.utc)

        world_data = {
            "id": world_id,
            "title": title,
            "description": description or "",
            "config": config or {"max_reflection_attempts": 2},
            "created_at": now,
        }
        timeline_data = {
            "id": timeline_id,
            "world_id": world_id,
            "parent_timeline_id": None,
            "fork_event_id": None,
            "name": "Canonical Timeline (Prime)",
            "created_at": now,
        }

        # Seed graph for world
        graph = WorldGraph.create_default_world()

        if self._pool:
            try:
                async with self._pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute(
                            "INSERT INTO worlds (id, title, description, config, created_at) VALUES ($1, $2, $3, $4, $5)",
                            world_id, title, description or "", json.dumps(world_data["config"]), now,
                        )
                        await conn.execute(
                            "INSERT INTO timelines (id, world_id, name, created_at) VALUES ($1, $2, $3, $4)",
                            timeline_id, world_id, timeline_data["name"], now,
                        )
                        # Save seed graph
                        for node in graph.to_dict()["nodes"]:
                            await conn.execute(
                                "INSERT INTO graph_nodes (world_id, node_id, node_type, label, properties) VALUES ($1, $2, $3, $4, $5)",
                                world_id, node["id"], node["type"], node["label"], json.dumps(node["properties"]),
                            )
                        for edge in graph.to_dict()["edges"]:
                            await conn.execute(
                                "INSERT INTO graph_edges (world_id, source_id, target_id, relation, properties) VALUES ($1, $2, $3, $4, $5)",
                                world_id, edge["source"], edge["target"], edge["relation"], json.dumps(edge["properties"]),
                            )
            except Exception as e:
                logger.error("DB error creating world: %s. Storing in-memory.", e)

        # Store in-memory
        self._worlds[world_id] = world_data
        self._timelines[timeline_id] = timeline_data
        self._graphs[world_id] = graph
        self._events[timeline_id] = []

        return WorldResponse(
            world_id=world_id,
            title=title,
            description=description,
            active_timeline_id=timeline_id,
            created_at=now,
        )

    async def get_world(self, world_id: UUID) -> Optional[WorldResponse]:
        """Retrieves world by ID."""
        if world_id in self._worlds:
            data = self._worlds[world_id]
            # find first timeline
            timeline_id = next(
                (t["id"] for t in self._timelines.values() if t["world_id"] == world_id),
                world_id,
            )
            return WorldResponse(
                world_id=data["id"],
                title=data["title"],
                description=data.get("description"),
                active_timeline_id=timeline_id,
                created_at=data["created_at"],
            )

        if self._pool:
            try:
                async with self._pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT * FROM worlds WHERE id = $1", world_id)
                    if row:
                        t_row = await conn.fetchrow("SELECT id FROM timelines WHERE world_id = $1 LIMIT 1", world_id)
                        t_id = t_row["id"] if t_row else world_id
                        return WorldResponse(
                            world_id=row["id"],
                            title=row["title"],
                            description=row["description"],
                            active_timeline_id=t_id,
                            created_at=row["created_at"],
                        )
            except Exception as e:
                logger.error("DB error fetching world: %s", e)

        return None

    async def get_world_graph(self, world_id: UUID) -> WorldGraph:
        """Retrieves or creates active WorldGraph for given world."""
        if world_id not in self._graphs:
            self._graphs[world_id] = WorldGraph.create_default_world()
        return self._graphs[world_id]

    async def get_timeline(self, timeline_id: UUID) -> Optional[TimelineResponse]:
        """Retrieves timeline metadata."""
        if timeline_id in self._timelines:
            t = self._timelines[timeline_id]
            return TimelineResponse(
                timeline_id=t["id"],
                world_id=t["world_id"],
                parent_timeline_id=t.get("parent_timeline_id"),
                fork_event_id=t.get("fork_event_id"),
                name=t["name"],
                created_at=t["created_at"],
            )
        return None

    async def append_event(
        self,
        timeline_id: UUID,
        action: str,
        prose: str,
        delta: WorldDelta,
        lore_citations: List[Dict[str, Any]],
    ) -> NarrativeEvent:
        """Appends an immutable narrative event to the timeline stream."""
        if timeline_id not in self._events:
            self._events[timeline_id] = []

        seq = len(self._events[timeline_id]) + 1
        event = NarrativeEvent(
            event_id=uuid4(),
            timeline_id=timeline_id,
            sequence_number=seq,
            action_prompt=action,
            narrative_prose=prose,
            graph_delta=delta,
            lore_citations=lore_citations,
            committed_at=datetime.now(timezone.utc),
        )

        self._events[timeline_id].append(event.model_dump())

        if self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO narrative_events 
                        (id, timeline_id, sequence_number, action_prompt, narrative_prose, graph_delta, lore_citations, committed_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        event.event_id,
                        timeline_id,
                        seq,
                        action,
                        prose,
                        json.dumps(delta.model_dump()),
                        json.dumps(lore_citations),
                        event.committed_at,
                    )
            except Exception as e:
                logger.error("DB error appending narrative event: %s", e)

        return event

    async def fork_timeline(
        self,
        parent_timeline_id: UUID,
        fork_event_id: UUID,
        name: str,
        description: Optional[str] = None,
    ) -> TimelineResponse:
        """Forks a new child timeline branching from an exact historical event snapshot."""
        parent_timeline = await self.get_timeline(parent_timeline_id)
        if not parent_timeline:
            raise ValueError(f"Parent timeline '{parent_timeline_id}' not found.")

        child_timeline_id = uuid4()
        now = datetime.now(timezone.utc)

        child_data = {
            "id": child_timeline_id,
            "world_id": parent_timeline.world_id,
            "parent_timeline_id": parent_timeline_id,
            "fork_event_id": fork_event_id,
            "name": name,
            "created_at": now,
        }

        self._timelines[child_timeline_id] = child_data
        self._events[child_timeline_id] = []

        if self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO timelines (id, world_id, parent_timeline_id, fork_event_id, name, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        child_timeline_id,
                        parent_timeline.world_id,
                        parent_timeline_id,
                        fork_event_id,
                        name,
                        now,
                    )
            except Exception as e:
                logger.error("DB error forking timeline: %s", e)

        return TimelineResponse(
            timeline_id=child_timeline_id,
            world_id=parent_timeline.world_id,
            parent_timeline_id=parent_timeline_id,
            fork_event_id=fork_event_id,
            name=name,
            created_at=now,
        )


event_store = EventStore()
