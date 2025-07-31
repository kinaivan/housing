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
                    "id": household.id if hasattr(household, "id") else None,
                    "name": household.name if hasattr(household, "name") else None,
                    "income": int(household.income) if hasattr(household, "income") else 0,
                    "size": int(household.size) if hasattr(household, "size") else 0,
                    "satisfaction": float(household.satisfaction) if hasattr(household, "satisfaction") else 0,
                    "wealth": float(household.wealth) if hasattr(household, "wealth") else 0,
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
        "unhoused": frame.get("unhoused", 0),
    }

    # Include policy metrics if available
    if "policy_metrics" in frame:
        metrics["policy_metrics"] = frame["policy_metrics"]

    data = {
        "year": frame.get("year"),
        "period": frame.get("period"),
        "metrics": metrics,
        "units": units_data
    }

    # Include events if they exist (with logging)
    if "events" in frame and isinstance(frame["events"], list):
        logging.info(f"Sending {len(frame['events'])} events")
        # Take only the last 50 events if there are more
        events = frame["events"][-50:] if len(frame["events"]) > 50 else frame["events"]
        # Ensure all event data is serializable
        serialized_events = []
        for event in events:
            serialized_event = {}
            for key, value in event.items():
                if isinstance(value, (int, float, str, bool, type(None))):
                    serialized_event[key] = value
                elif isinstance(value, (list, tuple)):
                    serialized_event[key] = list(value)
                elif isinstance(value, dict):
                    serialized_event[key] = value  # Assume nested dicts are already serializable
                else:
                    serialized_event[key] = str(value)  # Convert any other types to string
            serialized_events.append(serialized_event)
        data["events"] = serialized_events

    # Include moves if they exist
    if "moves" in frame and isinstance(frame["moves"], list):
        logging.info(f"Sending {len(frame['moves'])} moves")
        # Ensure all move data is serializable
        serialized_moves = []
        for move in frame["moves"]:
            serialized_move = {}
            for key, value in move.items():
                if isinstance(value, (int, float, str, bool, type(None))):
                    serialized_move[key] = value
                elif isinstance(value, (list, tuple)):
                    serialized_move[key] = list(value)
                elif isinstance(value, dict):
                    serialized_move[key] = value  # Assume nested dicts are already serializable
                else:
                    serialized_move[key] = str(value)  # Convert any other types to string
            serialized_moves.append(serialized_move)
        data["moves"] = serialized_moves

    # Include unhoused households if they exist
    if "unhoused_households" in frame and isinstance(frame["unhoused_households"], list):
        logging.info(f"Sending {len(frame['unhoused_households'])} unhoused households")
        # Ensure all household data is serializable
        serialized_households = []
        for household in frame["unhoused_households"]:
            # Handle both dictionary and Household object cases
            if hasattr(household, 'items'):  # It's a dictionary
                household_data = household
            else:  # It's a Household object
                household_data = {
                    "id": household.id if hasattr(household, "id") else None,
                    "name": household.name if hasattr(household, "name") else None,
                    "size": int(household.size) if hasattr(household, "size") else 0,
                    "income": float(household.income) if hasattr(household, "income") else 0,
                    "wealth": float(household.wealth) if hasattr(household, "wealth") else 0,
                    "months_unhoused": int(household.months_unhoused) if hasattr(household, "months_unhoused") else 0,
                    "satisfaction": float(household.satisfaction) if hasattr(household, "satisfaction") else 0,
                    "housed": bool(household.housed) if hasattr(household, "housed") else False,
                }

            # Further ensure all values are serializable
            serialized_household = {}
            for key, value in household_data.items():
                if isinstance(value, (int, float, str, bool, type(None))):
                    serialized_household[key] = value
                elif isinstance(value, (list, tuple)):
                    serialized_household[key] = list(value)
                elif isinstance(value, dict):
                    serialized_household[key] = value  # Assume nested dicts are already serializable
                else:
                    serialized_household[key] = str(value)  # Convert any other types to string
            serialized_households.append(serialized_household)
        data["unhoused_households"] = serialized_households

    return json.dumps(data)


def _check_control_signal(task_id: str) -> str:
    """Check for control signals (pause/resume/reset) for this simulation."""
    control_channel = f"sim:{task_id}:control"  # Match the channel name used in main.py
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
            
            elif signal is not None and signal.startswith("seek:"):
                target_step = int(signal.split(":")[1])
                # Get current step from the simulation
                current_step = getattr(sim, 'current_step', 0) if hasattr(sim, 'current_step') else step
                
                if target_step < current_step:
                    # If seeking backwards, we need to reset and replay
                    sim = initialize_simulation(initial_households=init_households, migration_rate=migration_rate)
                    current_sim_step = 0
                else:
                    # If seeking forwards, we can continue from current position
                    current_sim_step = current_step
                
                # Run simulation to target step
                while current_sim_step < target_step:
                    frame = sim.step()
                    if frame is None:
                        break
                    current_sim_step += 1
                
                if frame is not None:
                    redis_client.publish(channel, _serialize_frame(frame))
                is_paused = True
                redis_client.publish(channel, json.dumps({"type": "paused"}))
                break

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
                elif signal is not None and signal.startswith("seek:"):
                    target_step = int(signal.split(":")[1])
                    # Get current step from the simulation
                    current_step = getattr(sim, 'current_step', 0) if hasattr(sim, 'current_step') else step
                    
                    if target_step < current_step:
                        # If seeking backwards, we need to reset and replay
                        sim = initialize_simulation(initial_households=init_households, migration_rate=migration_rate)
                        current_sim_step = 0
                    else:
                        # If seeking forwards, we can continue from current position
                        current_sim_step = current_step
                    
                    # Run simulation to target step
                    while current_sim_step < target_step:
                        frame = sim.step()
                        if frame is None:
                            break
                        current_sim_step += 1
                    
                    if frame is not None:
                        redis_client.publish(channel, _serialize_frame(frame))
                    is_paused = True
                    redis_client.publish(channel, json.dumps({"type": "paused"}))
                    break

            # Process next simulation step if not paused
            if not is_paused:
                # Run one 6-month step for each frame (not 6 monthly steps)
                frame = sim.step()
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