import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional

import redis

from backend.celery_app import celery_app
from models.market import RentalMarket
from models.household import Household
from models.unit import RentalUnit
from models.policy import RentCapPolicy
from simulation.factory import initialize_simulation

# Local Redis client used for pub/sub streaming
_redis_url = celery_app.conf.broker_url
redis_client = redis.from_url(_redis_url)

CHANNEL_PREFIX = "sim:"  # Pub/Sub prefix for simulation updates
CONTROL_PREFIX = "control:"  # Prefix for simulation control channels
SIMULATION_PREFIX = "simulation:"


def _serialize_frame(frame: Dict) -> str:
    """Return a JSON-serializable representation of a simulation frame.

    Only lightweight numerical / string data is returned to the client to avoid
    huge payloads and non-serialisable custom objects.
    """
    if frame is None:
        return "{}"

    # Process units data with more detailed information
    units_data = []
    if frame.get("units"):
        for idx, unit in enumerate(frame["units"]):
            # Get household information if unit is occupied
            household_info = {}
            if hasattr(unit, "household") and unit.household:
                household = unit.household
                household_info = {
                    "income": int(household.income) if hasattr(household, "income") else 0,
                    "size": household.size if hasattr(household, "size") else 0,
                    "satisfaction": household.satisfaction if hasattr(household, "satisfaction") else 0,
                }

            units_data.append({
                "id": idx + 1,
                "occupants": unit.get_total_household_size() if hasattr(unit, "get_total_household_size") else 0,
                "rent": int(unit.rent) if hasattr(unit, "rent") else 0,
                "is_occupied": bool(unit.occupied) if hasattr(unit, "occupied") else False,
                "quality": float(unit.quality) if hasattr(unit, "quality") else 0.0,
                "lastRenovation": int(unit.last_renovation) if hasattr(unit, "last_renovation") else 0,
                "household": household_info if household_info else None
            })

    # Calculate additional metrics
    total_units = len(units_data)
    occupied_units = sum(1 for u in units_data if u["is_occupied"])
    total_rent = sum(u["rent"] for u in units_data)
    total_occupants = sum(u["occupants"] for u in units_data)
    
    metrics = {
        "total_units": total_units,
        "occupied_units": occupied_units,
        "vacancy_rate": round((total_units - occupied_units) / total_units * 100, 1) if total_units > 0 else 0,
        "average_rent": round(total_rent / total_units) if total_units > 0 else 0,
        "total_population": total_occupants,
        "unhoused": frame.get("unhoused", 0),
    }

    data = {
        "year": frame.get("year"),
        "period": frame.get("period"),
        "metrics": metrics,
        "units": units_data
    }
    return json.dumps(data)


def _check_control_signal(task_id: str) -> str:
    """Check for control signals (pause/resume/reset) for this simulation."""
    control_channel = f"{CONTROL_PREFIX}{task_id}"
    signal = redis_client.get(control_channel)
    if signal:
        redis_client.delete(control_channel)  # Consume the signal
    return signal.decode('utf-8') if signal else None


@celery_app.task(name="backend.tasks.run_simulation")
def run_simulation(task_id: str, params: Dict):
    """Background task that executes the simulation and streams updates.

    Parameters
    ----------
    task_id: str
        The unique identifier returned to the frontend. Doubles as the Redis
        pub/sub channel so that UI clients can subscribe for updates.
    params: Dict
        Simulation parameters coming from the API (parsed by Pydantic).
    """
    try:
        # Extract parameters with safe defaults.
        init_households = params.get("initial_households", 20)
        migration_rate = params.get("migration_rate", 0.1)
        years = params.get("years", 10)
        rent_cap_enabled = params.get("rent_cap_enabled", False)

        # Initialise the simulation using the existing helper.
        sim = initialize_simulation(
            initial_households=init_households,
            migration_rate=migration_rate,
            years=years,
            rent_cap_enabled=rent_cap_enabled
        )

        channel = f"{CHANNEL_PREFIX}{task_id}"

        # Publish the very first frame (initial state)
        frame = sim.get_current_state()
        redis_client.publish(channel, _serialize_frame(frame))

        # Each step is now 6 months, so we need half as many steps
        total_steps = (years * 12) // 6
        is_paused = False

        for step in range(total_steps):
            # Check for control signals
            signal = _check_control_signal(task_id)
            
            if signal == "reset":
                # Reset simulation
                sim = initialize_simulation(initial_households=init_households, migration_rate=migration_rate)
                frame = sim.get_current_state()
                redis_client.publish(channel, _serialize_frame(frame))
                is_paused = False
                continue
                
            elif signal == "pause":
                is_paused = True
                redis_client.publish(channel, json.dumps({"type": "paused"}))
                
            elif signal == "resume":
                is_paused = False
                redis_client.publish(channel, json.dumps({"type": "resumed"}))

            # If paused, wait for resume signal
            while is_paused:
                time.sleep(0.1)  # Check for signals every 100ms
                signal = _check_control_signal(task_id)
                if signal == "resume":
                    is_paused = False
                    redis_client.publish(channel, json.dumps({"type": "resumed"}))
                elif signal == "reset":
                    sim = initialize_simulation(initial_households=init_households, migration_rate=migration_rate)
                    frame = sim.get_current_state()
                    redis_client.publish(channel, _serialize_frame(frame))
                    is_paused = False
                    break

            # Process next simulation step if not paused
            if not is_paused:
                # Run 6 monthly steps for each frame
                for _ in range(6):
                    frame = sim.step()
                    if frame is None:
                        break
                if frame is not None:
                    redis_client.publish(channel, _serialize_frame(frame))
                    time.sleep(2.0)  # Show each 6-month step for 2 seconds

        # Signal completion explicitly.
        redis_client.publish(channel, json.dumps({"type": "complete"}))
        
    except Exception as e:
        # Handle any errors
        error_msg = {"type": "error", "message": str(e)}
        redis_client.publish(channel, json.dumps(error_msg))
        raise 