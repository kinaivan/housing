from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Literal, List
import uuid
import json
import redis.asyncio as redis
import asyncio
import logging
import random
import time
import numpy as np
from datetime import datetime
from models.household import Household
from models.unit import RentalUnit

from backend.celery_app import celery_app
from backend.tasks import run_simulation
from simulation.factory import initialize_simulation

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
    num_runs: int = 1  # Number of simulation runs to perform
    # Future: scenario, policies, etc.


class SimulationStartResponse(BaseModel):
    simulation_id: str


class SimulationRunResponse(BaseModel):
    frames: list
    metrics: dict
    aggregate_metrics: dict | None = None  # Aggregate metrics when multiple runs are performed


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


def send_progress_update(progress: float, message: str):
    """Helper function to format progress updates"""
    return f"data: {json.dumps({'progress': progress, 'message': message})}\n\n"

def convert_frames_to_serializable(frames):
    """Convert frames containing objects to serializable dictionaries"""
    serializable_frames = []
    
    for frame in frames:
        if isinstance(frame, dict):
            # Create a serializable copy of the frame
            serializable_frame = {}
            for key, value in frame.items():
                if key == 'units':
                    # Convert units to serializable format
                    serializable_units = []
                    for unit in value:
                        if hasattr(unit, '__dict__'):  # It's an object
                            unit_dict = {
                                'id': getattr(unit, 'id', 0),
                                'rent': getattr(unit, 'rent', 0),
                                'occupied': getattr(unit, 'occupied', False),
                                'quality': getattr(unit, 'quality', 1.0),
                                'is_owner_occupied': getattr(unit, 'is_owner_occupied', False),
                            }
                            # Add household info if present
                            if hasattr(unit, 'household') and unit.household:
                                household = unit.household
                                unit_dict['household'] = {
                                    'id': getattr(household, 'id', 0),
                                    'name': getattr(household, 'name', ''),
                                    'income': getattr(household, 'income', 0),
                                    'satisfaction': getattr(household, 'satisfaction', 0),
                                    'size': getattr(household, 'size', 1),
                                    'monthly_payment': getattr(household, 'monthly_payment', 0),
                                }
                            serializable_units.append(unit_dict)
                        else:
                            # Already a dictionary
                            serializable_units.append(value)
                    serializable_frame[key] = serializable_units
                elif key == 'households':
                    # Convert households to serializable format
                    serializable_households = []
                    for household in value:
                        if hasattr(household, '__dict__'):  # It's an object
                            household_dict = {
                                'id': getattr(household, 'id', 0),
                                'name': getattr(household, 'name', ''),
                                'income': getattr(household, 'income', 0),
                                'satisfaction': getattr(household, 'satisfaction', 0),
                                'size': getattr(household, 'size', 1),
                                'housed': getattr(household, 'housed', False),
                                'monthly_payment': getattr(household, 'monthly_payment', 0),
                            }
                            serializable_households.append(household_dict)
                        else:
                            # Already a dictionary
                            serializable_households.append(household)
                    serializable_frame[key] = serializable_households
                else:
                    # For other keys, copy as-is if they're serializable
                    try:
                        json.dumps(value)  # Test if serializable
                        serializable_frame[key] = value
                    except (TypeError, ValueError):
                        # Skip non-serializable values
                        continue
            serializable_frames.append(serializable_frame)
        else:
            # If frame is not a dict, try to convert or skip
            continue
    
    return serializable_frames

async def run_simulation_with_progress(params: SimulationParams):
    """Generator that yields progress updates during simulation"""
    
    yield send_progress_update(0, "Starting simulation...")
    await asyncio.sleep(0.1)  # Small delay to ensure message is sent
    
    yield send_progress_update(5, "Initializing parameters...")
    await asyncio.sleep(0.1)
    
    all_frames = []
    all_metrics = []

    # Ensure we have valid parameters
    if params.initial_households <= 0:
        raise HTTPException(status_code=400, detail="initial_households must be positive")
    
    # Set random seed for reproducibility
    base_seed = 42
    if params.policy == "rent_cap":
        base_seed += 1000  # Offset for rent cap policy
    elif params.policy == "lvt":
        base_seed += 2000  # Offset for LVT policy

    total_runs = params.num_runs
    total_periods = params.years * 2  # 2 periods per year (6 months each)
    
    for run in range(total_runs):
        # Calculate progress for this run start
        run_start_progress = (run / total_runs) * 100
        yield send_progress_update(run_start_progress, f"Starting simulation {run + 1} of {total_runs}...")
        
        # Set a different random seed for each run, but consistently different between policies
        run_seed = base_seed + run
        random.seed(run_seed)
        np.random.seed(run_seed)

        # Use the factory function to initialize the simulation
        sim = initialize_simulation(
            initial_households=params.initial_households,
            migration_rate=params.migration_rate,
            years=params.years,
            rent_cap_enabled=(params.policy == "rent_cap"),
            lvt_enabled=(params.policy == "lvt"),
            lvt_rate=params.lvt_rate
        )

        # Run simulation and collect frames
        frames = []
        
        for step_num in range(total_periods):
            # Calculate progress within this run
            step_progress = run_start_progress + (step_num / total_periods) * (100 / total_runs)
            if step_num % 5 == 0:  # Send progress update every 5 steps
                year = (step_num // 2) + 1
                yield send_progress_update(step_progress, f"Run {run + 1}: Year {year} of {params.years}")
            
            frame = sim.step()
            if frame is None:  # Simulation completed
                break
            frames.append(frame)

        # Calculate final metrics for this run
        final_frame = frames[-1] if frames else {}
        final_metrics = final_frame.get("metrics", {})
        
        metrics = {
            "final_population": final_metrics.get("total_population", len([h for h in sim.simulation.households if h.housed])),
            "final_average_rent": final_metrics.get("average_rent", 0),
            "policy_metrics": final_metrics.get("policy_metrics", {}),
        }

        # Calculate average rent more accurately from actual units
        final_frame = frames[-1] if frames else {}
        units = final_frame.get("units", [])
        occupied_rents = []
        
        for unit in units:
            if hasattr(unit, 'rent') and hasattr(unit, 'occupied'):  # RentalUnit object
                if unit.occupied:
                    occupied_rents.append(unit.rent)
            elif isinstance(unit, dict) and unit.get("is_occupied"):  # Dictionary
                occupied_rents.append(unit.get("rent", 0))
        
        if occupied_rents:
            metrics["final_average_rent"] = np.mean(occupied_rents)
        else:
            # Fallback: calculate from all units
            all_rents = []
            for unit in units:
                if hasattr(unit, 'rent'):  # RentalUnit object
                    all_rents.append(unit.rent)
                elif isinstance(unit, dict):  # Dictionary
                    all_rents.append(unit.get("rent", 0))
            metrics["final_average_rent"] = np.mean(all_rents) if all_rents else 0

        # Calculate satisfaction safely
        final_frame = frames[-1] if frames else {}
        units = final_frame.get("units", [])
        
        # Handle both RentalUnit objects and dictionaries
        housed_units = []
        for unit in units:
            if hasattr(unit, 'household'):  # RentalUnit object
                if unit.household:
                    housed_units.append(unit)
            elif isinstance(unit, dict) and unit.get("household"):  # Dictionary
                housed_units.append(unit)
        
        if housed_units:
            satisfaction_values = []
            for unit in housed_units:
                if hasattr(unit, 'household'):  # RentalUnit object
                    household = unit.household
                    if hasattr(household, 'satisfaction') and household.satisfaction is not None:
                        satisfaction_values.append(household.satisfaction)
                elif isinstance(unit, dict):  # Dictionary
                    household = unit.get("household")
                    if household and household.get("satisfaction") is not None:
                        satisfaction_values.append(household["satisfaction"])
            
            metrics["avg_satisfaction"] = (
                np.mean(satisfaction_values) * 100 if satisfaction_values else 0
            )
        else:
            metrics["avg_satisfaction"] = 0

        # Calculate rent burden safely
        if housed_units:
            rent_burdens = []
            for unit in housed_units:
                if hasattr(unit, 'household'):  # RentalUnit object
                    household = unit.household
                    if hasattr(household, 'income') and household.income > 0:
                        if hasattr(household, 'monthly_payment') and household.monthly_payment > 0:
                            burden = (household.monthly_payment / household.income) * 100
                        else:
                            burden = (unit.rent / household.income) * 100
                        rent_burdens.append(burden)
                elif isinstance(unit, dict):  # Dictionary
                    household = unit.get("household")
                    if household and household.get("income", 0) > 0:
                        if household.get("monthly_payment") and household["monthly_payment"] > 0:
                            burden = (household["monthly_payment"] / household["income"]) * 100
                        else:
                            burden = (unit["rent"] / household["income"]) * 100
                        rent_burdens.append(burden)
            
            metrics["avg_rent_burden"] = np.mean(rent_burdens) if rent_burdens else 0
        else:
            metrics["avg_rent_burden"] = 0

        # Calculate unhoused safely
        metrics["unhoused"] = len(frames[-1].get("unhoused_households", []))
        
        all_metrics.append(metrics)
        if run == 0:  # Only keep frames from first run for visualization
            all_frames = frames

        # Send progress update after completing this run
        run_completion_progress = ((run + 1) / total_runs) * 100
        yield send_progress_update(run_completion_progress, f"Completed simulation {run + 1} of {total_runs} ({run_completion_progress:.1f}%)")

    yield send_progress_update(100, "Calculating aggregate statistics...")

    # Calculate aggregate statistics across all runs
    def safe_stats(values):
        if not values:
            return {"mean": 0, "std": 0, "p25": 0, "p75": 0}
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p75": float(np.percentile(arr, 75))
        }
    
    # Collect metrics by type
    final_populations = [m["final_population"] for m in all_metrics]
    final_rents = [m["final_average_rent"] for m in all_metrics]
    satisfactions = [m["avg_satisfaction"] for m in all_metrics]
    rent_burdens = [m["avg_rent_burden"] for m in all_metrics]
    unhoused_counts = [m["unhoused"] for m in all_metrics]
    
    aggregate_metrics = {
        "final_population": safe_stats(final_populations),
        "rent": safe_stats(final_rents),  # Changed from "final_average_rent" to "rent"
        "satisfaction": safe_stats(satisfactions),  # Changed from "avg_satisfaction" to "satisfaction"
        "rent_burden": safe_stats(rent_burdens),  # Changed from "avg_rent_burden" to "rent_burden"
        "unhoused": safe_stats(unhoused_counts),
    }

    # Prepare final response
    serializable_frames = convert_frames_to_serializable(all_frames)
    
    response_data = {
        "frames": serializable_frames,
        "metrics": all_metrics[0] if all_metrics else {},
        "aggregate_metrics": aggregate_metrics,
        "total_runs": params.num_runs
    }
    
    yield send_progress_update(100, "Simulation complete!")
    yield f"data: {json.dumps({'completed': True, 'result': response_data})}\n\n"

@app.post("/simulation/run")
async def run_simulation_sync(params: SimulationParams):
    """Run a simulation with progress updates via Server-Sent Events"""
    # Check if this is a streaming request (multiple runs)
    if params.num_runs > 1:
        return StreamingResponse(
            run_simulation_with_progress(params),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    else:
        # For single runs, use the original non-streaming approach
        # (Implementation would be similar but return JSON directly)
        async for chunk in run_simulation_with_progress(params):
            if "completed" in chunk:
                # Extract the final result from the last chunk
                import json
                data = json.loads(chunk.split("data: ")[1])
                if data.get("completed"):
                    return data["result"]
        
        # Fallback empty response
        return {
            "frames": [],
            "metrics": {},
            "aggregate_metrics": {},
            "total_runs": 1
        }


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