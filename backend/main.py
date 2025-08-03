from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Literal
import uuid
import json
import redis.asyncio as redis
import asyncio
import logging
import random
from datetime import datetime
from models.household import Household
from models.unit import RentalUnit

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
    rent_cap_enabled: bool = False
    lvt_enabled: bool = False
    lvt_rate: float = 0.02
    policy: str = "none"  # "none", "rent_cap", or "lvt"
    # Future: scenario, policies, etc.


class SimulationStartResponse(BaseModel):
    simulation_id: str


class SimulationRunResponse(BaseModel):
    frames: list
    metrics: dict


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


@app.post("/simulation/run", response_model=SimulationRunResponse)
async def run_simulation_sync(params: SimulationParams):
    """Run a simulation synchronously and return all frames at once."""
    from simulation.realtime_sim import RealtimeSimulation
    from simulation.runner import Simulation
    from models.market import RentalMarket
    from models.unit import Landlord
    from models.policy import RentCapPolicy, LandValueTaxPolicy

    # Initialize simulation components
    landlords = [Landlord(id=i, units=[]) for i in range(5)]  # Each landlord gets a unique id and empty units list
    
    # Create units and assign to landlords
    units = []
    units_per_landlord = 20  # Each landlord gets 20 units
    for landlord in landlords:
        for _ in range(units_per_landlord):
            unit = RentalUnit(
                id=len(units),
                quality=random.uniform(0.3, 1.0),
                base_rent=random.randint(800, 2000),
                size=random.randint(1, 4),
                location=random.uniform(0, 1.0)
            )
            units.append(unit)
            landlord.units.append(unit)  # Assign unit to landlord's units list
    
    # Initialize market with units
    market = RentalMarket(units=units)
    
    # Set up policy
    if params.policy == "rent_cap":
        policy = RentCapPolicy()
    elif params.policy == "lvt":
        policy = LandValueTaxPolicy(params.lvt_rate)
    else:
        policy = None

    # Create initial households
    households = []
    for _ in range(params.initial_households):
        age = max(18, min(85, random.normalvariate(45, 15)))
        size = random.randint(1, 4)
        income = random.randint(20000, 80000)
        wealth = random.randint(0, 100000)
        households.append(Household(
            id=len(households),
            age=age,
            size=size,
            income=income,
            wealth=wealth
        ))

    # Create and initialize simulation
    runner = Simulation(
        households=households,
        landlords=landlords,
        rental_market=market,
        policy=policy,
        years=params.years
    )

    # Run simulation and collect frames
    frames = []
    for year in range(params.years):
        for period in range(12):  # 12 periods per year
            frame = runner.step(year, period)
            frames.append(frame)

    # Calculate final metrics
    metrics = {
        "final_population": frames[-1]["metrics"]["total_population"],
        "final_average_rent": frames[-1]["metrics"]["average_rent"],
        # "occupancy_rate": frames[-1]["metrics"]["occupied_units"] / frames[-1]["metrics"]["total_units"],  # Removed
        "policy_metrics": frames[-1]["metrics"].get("policy_metrics", {})
    }

    return {"frames": frames, "metrics": metrics}


@app.post("/simulation/{task_id}/control")
async def control_simulation(task_id: str, control: dict):
    action = control.get("action")
    if action not in ["pause", "resume", "reset", "seek"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # Use the existing redis_client instance
    if action == "seek":
        step = control.get("step")
        if step is None:
            raise HTTPException(status_code=400, detail="Step parameter required for seek action")
        await redis_client.set(f"sim:{task_id}:control", f"seek:{step}")
    else:
        await redis_client.set(f"sim:{task_id}:control", action)
    
    return {"status": "ok"}


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