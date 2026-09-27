"""FastAPI application entrypoint for Narrative-Craft."""

from contextlib import asynccontextmanager
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from src.ai.orchestrator import SceneOrchestrator
from src.core.config import settings
from src.domain.graph import WorldGraph
from src.domain.models import (
    CreateWorldRequest,
    ForkTimelineRequest,
    HealthStatus,
    NarrativeTurnRequest,
    NarrativeTurnResponse,
    ProblemDetails,
    SubgraphResponse,
    TimelineResponse,
    WorldDelta,
    WorldResponse,
)
from src.storage.db import event_store
from src.storage.redis_cache import session_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("NarrativeAPI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Narrative-Craft Engine on port %d...", settings.PORT)
    await event_store.initialize()
    await session_cache.connect()
    yield
    # Shutdown
    logger.info("Shutting down Narrative-Craft Engine...")
    await event_store.close()
    await session_cache.close()


app = FastAPI(
    title="Narrative-Craft Headless Engine API",
    description="Graph-augmented stateful narrative engine and multiverse simulation service",
    version="0.1.0",
    lifespan=lifespan,
)

orchestrator = SceneOrchestrator()


@app.get("/health/live", response_model=HealthStatus, tags=["Health"])
async def get_liveness():
    """Liveness probe verifying the API process is alive."""
    return HealthStatus(status="healthy", version="0.1.0")


@app.get("/health/ready", response_model=HealthStatus, tags=["Health"])
async def get_readiness():
    """Readiness probe checking storage and provider connectivity."""
    components = {
        "postgres": "ready" if event_store._pool else "in_memory_fallback",
        "redis": "ready" if session_cache._redis else "in_memory_fallback",
        "llm_provider": settings.LLM_PROVIDER,
    }
    return HealthStatus(status="healthy", version="0.1.0", components=components)


@app.post("/v1/worlds", response_model=WorldResponse, status_code=status.HTTP_201_CREATED, tags=["Worlds"])
async def create_world(req: CreateWorldRequest):
    """Initializes a new narrative world session and prime timeline."""
    try:
        world_resp = await event_store.create_world(
            title=req.title,
            description=req.description,
            config=req.config,
        )
        return world_resp
    except Exception as e:
        logger.error("Error creating world: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )


@app.get("/v1/worlds/{world_id}", response_model=WorldResponse, tags=["Worlds"])
async def get_world(world_id: UUID):
    """Retrieves world session configuration."""
    world = await event_store.get_world(world_id)
    if not world:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ProblemDetails(
                title="World Not Found",
                status=404,
                detail=f"World with id '{world_id}' does not exist.",
            ).model_dump(),
        )
    return world


@app.post("/v1/timelines/{timeline_id}/turns", tags=["Turns"])
async def execute_turn(timeline_id: UUID, req: NarrativeTurnRequest, request: Request):
    """Submits a character action, validates physical rules, and streams or returns turn output."""
    timeline = await event_store.get_timeline(timeline_id)
    world_id = timeline.world_id if timeline else timeline_id
    graph: WorldGraph = await event_store.get_world_graph(world_id)

    # Determine existing event count to compute sequence number
    existing_events = event_store._events.get(timeline_id, [])
    sequence_number = len(existing_events) + 1

    accept_header = request.headers.get("accept", "")
    stream_requested = "text/event-stream" in accept_header

    try:
        # Pre-validate to return 422 synchronously if rule fails before streaming
        async def event_generator() -> AsyncIterator[Dict[str, str]]:
            full_prose = ""
            delta_dict = {}
            turn_id = ""

            try:
                async for event in orchestrator.execute_turn_stream(
                    timeline_id=timeline_id,
                    character_id=req.character_id,
                    action=req.action,
                    graph=graph,
                    sequence_number=sequence_number,
                ):
                    event_type = event["event"]
                    event_data = event["data"]

                    if event_type == "complete":
                        full_prose = event_data["prose"]
                        delta_dict = event_data["graph_delta"]
                        turn_id = event_data["turn_id"]

                    yield {
                        "event": event_type,
                        "data": json.dumps(event_data),
                    }

                # Commit event to store
                delta_obj = WorldDelta.model_validate(delta_dict)
                await event_store.append_event(
                    timeline_id=timeline_id,
                    action=req.action,
                    prose=full_prose,
                    delta=delta_obj,
                    lore_citations=[],
                )
            except ValueError as val_err:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(val_err)}),
                }

        if stream_requested:
            # First check preconditions so we return 422 HTTP code if invalid
            from src.domain.rules import RuleEngine
            rule_check = RuleEngine.validate_preconditions(req.character_id, req.action, graph)
            if not rule_check.is_valid:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    content=ProblemDetails(
                        title="Precondition Rule Violation",
                        status=422,
                        detail=rule_check.reason,
                    ).model_dump(),
                )

            return EventSourceResponse(event_generator())
        else:
            # Synchronous JSON response
            from src.domain.rules import RuleEngine
            rule_check = RuleEngine.validate_preconditions(req.character_id, req.action, graph)
            if not rule_check.is_valid:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    content=ProblemDetails(
                        title="Precondition Rule Violation",
                        status=422,
                        detail=rule_check.reason,
                    ).model_dump(),
                )

            complete_event_data = None
            async for ev in orchestrator.execute_turn_stream(
                timeline_id=timeline_id,
                character_id=req.character_id,
                action=req.action,
                graph=graph,
                sequence_number=sequence_number,
            ):
                if ev["event"] == "complete":
                    complete_event_data = ev["data"]

            if not complete_event_data:
                raise HTTPException(status_code=500, detail="Turn execution failed")

            delta_obj = WorldDelta.model_validate(complete_event_data["graph_delta"])
            await event_store.append_event(
                timeline_id=timeline_id,
                action=req.action,
                prose=complete_event_data["prose"],
                delta=delta_obj,
                lore_citations=complete_event_data["lore_citations"],
            )

            return NarrativeTurnResponse(
                turn_id=complete_event_data["turn_id"],
                timeline_id=timeline_id,
                sequence_number=sequence_number,
                status="COMMITTED",
                prose=complete_event_data["prose"],
                graph_delta=complete_event_data["graph_delta"],
                lore_citations=complete_event_data["lore_citations"],
            )

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=ProblemDetails(
                title="Precondition Rule Violation",
                status=422,
                detail=str(e),
            ).model_dump(),
        )


@app.post(
    "/v1/timelines/{timeline_id}/fork",
    response_model=TimelineResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Timelines"],
)
async def fork_timeline(timeline_id: UUID, req: ForkTimelineRequest):
    """Branches an alternate multiverse timeline from an event snapshot."""
    try:
        timeline = await event_store.fork_timeline(
            parent_timeline_id=timeline_id,
            fork_event_id=req.fork_event_id,
            name=req.name,
            description=req.description,
        )
        return timeline
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ProblemDetails(
                title="Timeline Not Found",
                status=404,
                detail=str(e),
            ).model_dump(),
        )


@app.get(
    "/v1/timelines/{timeline_id}/graph/subgraph",
    response_model=SubgraphResponse,
    tags=["Graph"],
)
async def get_subgraph(timeline_id: UUID, center_id: str, hops: int = 2):
    """Extracts k-hop neighborhood around target character or entity."""
    timeline = await event_store.get_timeline(timeline_id)
    world_id = timeline.world_id if timeline else timeline_id
    graph: WorldGraph = await event_store.get_world_graph(world_id)

    subgraph = graph.extract_subgraph(center_id=center_id, hops=hops)
    return SubgraphResponse(
        center_id=center_id,
        hops=hops,
        nodes=subgraph["nodes"],
        edges=subgraph["edges"],
    )
