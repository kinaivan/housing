from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Literal
import uuid
import json
import redis.asyncio as redis
import asyncio
import logging
from datetime import datetime

from backend.celery_app import celery_app
from backend.tasks import run_simulation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# FastAPI setup
# ----------------------------------------------------------------------------
app = FastAPI(title="Housing Market Simulation API", version="0.1.0")

# Allow local dev front-end (React/Vite) to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client for pub/sub used by WebSocket endpoint
_redis_url = celery_app.conf.broker_url
redis_client = redis.from_url(_redis_url, decode_responses=True)

# Channel prefixes for Redis pub/sub
CHANNEL_PREFIX = "sim:"
CONTROL_PREFIX = "control:"


# ----------------------------------------------------------------------------
# Pydantic models
# ----------------------------------------------------------------------------
class SimulationParams(BaseModel):
    initial_households: int = 20
    migration_rate: float = 0.1
    years: int = 10
    # Future: scenario, policies, etc.


class SimulationStartResponse(BaseModel):
    simulation_id: str


class SimulationControl(BaseModel):
    action: Literal["pause", "resume", "reset"]


# ----------------------------------------------------------------------------
# REST endpoints
# ----------------------------------------------------------------------------
@app.post("/simulation/start", response_model=SimulationStartResponse)
async def start_simulation(params: SimulationParams):
    """Enqueue a new simulation job and return its identifier."""
    simulation_id = str(uuid.uuid4())
    celery_app.send_task("backend.tasks.run_simulation", args=[simulation_id, params.dict()])
    return {"simulation_id": simulation_id}


@app.post("/simulation/{simulation_id}/control")
async def control_simulation(simulation_id: str, control: SimulationControl):
    """Control a running simulation (pause/resume/reset)."""
    control_channel = f"{CONTROL_PREFIX}{simulation_id}"
    await redis_client.set(control_channel, control.action)
    return {"status": "success", "action": control.action}


@app.get("/simulation/status/{simulation_id}")
async def simulation_status(simulation_id: str):
    """Basic status check based on Celery result backend."""
    async_result = celery_app.AsyncResult(simulation_id)
    return {
        "state": async_result.state,
        "ready": async_result.ready(),
    }


# ----------------------------------------------------------------------------
# WebSocket for live updates
# ----------------------------------------------------------------------------
@app.websocket("/simulation/stream/{simulation_id}")
async def simulation_stream(websocket: WebSocket, simulation_id: str):
    await websocket.accept()
    channel = f"{CHANNEL_PREFIX}{simulation_id}"
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            # The first few messages can be subscription confirmations; we only
            # forward actual data messages.
            if message["type"] != "message":
                continue
            data = message["data"]
            await websocket.send_text(data)
    except WebSocketDisconnect:
        await pubsub.unsubscribe(channel)
    finally:
        await pubsub.close()