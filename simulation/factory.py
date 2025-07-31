import random
from typing import List

from models.household import Household
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy
from simulation.realtime_sim import RealtimeSimulation
from models.houses_data import HOUSES
from models.people_data import PEOPLE


def create_household_from_data(person_data: dict) -> Household:
    """Create a Household instance from predefined person data."""
    return Household(
        id=person_data["id"],
        age=person_data["age"],
        size=person_data["size"],
        income=person_data["monthly_income"],
        wealth=person_data["wealth"]
    )


def create_unit_from_data(house_data: dict) -> RentalUnit:
    """Create a RentalUnit instance from predefined house data."""
    return RentalUnit(
        id=house_data["id"],
        quality=house_data["quality"],
        base_rent=house_data["base_rent"]
    )


def initialize_simulation(
    *,
    initial_households: int = 20,
    migration_rate: float = 0.1,
    years: int = 10,
    rent_cap_enabled: bool = False,
    lvt_enabled: bool = False,
    lvt_rate: float = 0.10,
) -> RealtimeSimulation:
    """Initialize a new simulation with the given parameters"""
    
    # Create initial households from predefined data
    # If we need more households than we have data for, we'll create random ones
    households = []
    for i in range(initial_households):
        if i < len(PEOPLE):
            households.append(create_household_from_data(PEOPLE[i]))
        else:
            # Fallback to random household creation if we need more
            households.append(Household(
                id=i,
                age=random.randint(25, 60),
                size=random.choices([1, 2, 3, 4], weights=[30, 40, 20, 10])[0],
                income=random.uniform(2000, 8000),
                wealth=random.uniform(5000, 100000)
            ))
    
    # Create rental units from predefined data
    # If we need more units than we have data for, we'll create random ones
    units = []
    for i in range(20):  # Always create exactly 20 units
        if i < len(HOUSES):
            units.append(create_unit_from_data(HOUSES[i]))
        else:
            # Fallback to random unit creation if we need more
            quality = random.uniform(0.3, 1.0)
            base_rent = 1000 + (quality * 500)
            units.append(RentalUnit(id=i, quality=quality, base_rent=base_rent))
    
    # Create landlords (assume 5 units per landlord)
    num_landlords = len(units) // 5
    landlords = []
    units_per_landlord = len(units) // num_landlords
    for i in range(num_landlords):
        start_idx = i * units_per_landlord
        end_idx = start_idx + units_per_landlord if i < num_landlords - 1 else len(units)
        landlord = Landlord(id=i, units=units[start_idx:end_idx])
        landlords.append(landlord)
    
    # Create rental market
    market = RentalMarket(units)

    # Create policy based on parameters
    if lvt_enabled:
        from models.policy import LandValueTaxPolicy
        policy = LandValueTaxPolicy(lvt_rate=lvt_rate)
    elif rent_cap_enabled:
        from models.policy import RentCapPolicy
        policy = RentCapPolicy()
    else:
        policy = None

    # Distribute initial households to units
    available_units = units.copy()
    random.shuffle(available_units)  # Randomize unit order
    
    # Sort households by income (descending) to give higher income households first pick
    households.sort(key=lambda h: h.income, reverse=True)
    
    for household in households:
        if not available_units:  # No more units available
            break
            
        # Find suitable units (rent <= 40% of monthly income)
        suitable_units = [
            unit for unit in available_units
            if unit.base_rent <= household.income * 0.4
        ]
        
        if suitable_units:
            # Choose unit based on quality and affordability
            unit = max(suitable_units, key=lambda u: u.quality - (u.base_rent / household.income))
            # Move in
            household.move_to(unit, year=1, period=1)
            available_units.remove(unit)
    
    # Create simulation
    sim = RealtimeSimulation(
        households=households,
        landlords=landlords,
        rental_market=market,
        policy=policy,
        years=years
    )
    
    return sim 