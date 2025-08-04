import random
from typing import List

from models.household import Household
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy
from simulation.realtime_sim import RealtimeSimulation
from models.houses_data import HOUSES
from models.people_data import PEOPLE
from models.dutch_names import generate_dutch_name
from models.contract import Contract


def create_household_from_data(person_data: dict) -> Household:
    """Create a Household instance from predefined person data."""
    household = Household(
        id=person_data["id"],
        age=person_data["age"],
        size=person_data["size"],
        income=person_data["monthly_income"],
        wealth=person_data["wealth"]
    )
    return household


def _create_random_household(id: int) -> Household:
    """Create a random household with realistic attributes."""
    # Age distribution: young adults (20-35), middle-aged (35-55), seniors (55+)
    age_group = random.choices(["young", "middle", "senior"], weights=[35, 45, 20])[0]
    
    if age_group == "young":
        age = random.randint(20, 35)
        size = random.choices([1, 2], weights=[70, 30])[0]  # Mostly singles and couples
        income = random.randint(2000, 4000)
        wealth = random.randint(5000, 30000)
    elif age_group == "middle":
        age = random.randint(35, 55)
        size = random.choices([1, 2, 3, 4], weights=[20, 30, 30, 20])[0]  # More families
        income = random.randint(3000, 8000)
        wealth = random.randint(20000, 100000)
    else:  # senior
        age = random.randint(55, 80)
        size = random.choices([1, 2], weights=[40, 60])[0]  # Mostly singles and couples
        income = random.randint(2000, 6000)
        wealth = random.randint(50000, 200000)

    household = Household(
        id=id,
        age=age,
        size=size,
        income=income,
        wealth=wealth
    )
    
    # The Household class will automatically generate a Dutch name and set life stage
    return household


def create_unit_from_data(house_data: dict) -> RentalUnit:
    """Create a RentalUnit instance from predefined house data."""
    return RentalUnit(
        id=house_data["id"],
        quality=house_data["quality"],
        base_rent=house_data["base_rent"]
    )


def reset_logging_flags():
    """Reset the logging flags for a fresh start"""
    for attr in ['_large_sim_logged', '_housing_logged', '_owner_logged', '_renter_logged', 
                 '_renter_assignment_logged', '_final_logged']:
        if hasattr(initialize_simulation, attr):
            delattr(initialize_simulation, attr)

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
    
    # Reset logging flags for large simulations to show info once per comparison
    if initial_households > 20:
        reset_logging_flags()
    
    # Create initial households from predefined data
    # If we need more households than we have data for, we'll create random ones
    households = []
    for i in range(initial_households):
        if i < len(PEOPLE):
            households.append(create_household_from_data(PEOPLE[i]))
        else:
            # Create random household with realistic attributes
            households.append(_create_random_household(i))
    
    # Create rental units from predefined data
    # If we need more units than we have data for, we'll create random ones
    units = []
    
    # For the normal simulation frontend, always create exactly 20 units
    # For policy comparison (large simulations), scale units based on households
    if initial_households > 100:  # Policy comparison uses 1000 households
        # Large simulation: more units to accommodate more households
        num_units = max(initial_households + 200, 1000)  # Extra units for market dynamics
        units_per_landlord = random.randint(10, 20)
        # Only print once for large simulations to reduce noise
        if not hasattr(initialize_simulation, '_large_sim_logged'):
            print(f"Large simulation: Creating {num_units} units for {initial_households} households")
            initialize_simulation._large_sim_logged = True
    else:
        # Normal simulation: always 20 units regardless of household count
        num_units = 20
        units_per_landlord = 5
        print(f"Normal simulation: Creating {num_units} units for {initial_households} households")
    
    for i in range(num_units):
        if i < len(HOUSES):
            units.append(create_unit_from_data(HOUSES[i]))
        else:
            # Fallback to random unit creation if we need more
            quality = random.uniform(0.3, 1.0)
            base_rent = random.uniform(800, 3000)  # More varied rent range
            units.append(RentalUnit(id=i, quality=quality, base_rent=base_rent))
    
    print(f"Created {len(units)} units")
    
    # Create landlords
    num_landlords = max(1, len(units) // units_per_landlord)
    landlords = []
    
    # Distribute units among landlords
    for i in range(num_landlords):
        start_idx = i * units_per_landlord
        end_idx = min(start_idx + units_per_landlord, len(units))
        if start_idx < len(units):
            landlord_units = units[start_idx:end_idx]
            landlord = Landlord(id=i, units=landlord_units)
            landlords.append(landlord)
    
    # Handle any remaining units (give to last landlord)
    remaining_units = len(units) % units_per_landlord
    if remaining_units > 0 and landlords:
        remaining_start = (num_landlords - 1) * units_per_landlord + units_per_landlord
        for i in range(remaining_start, len(units)):
            landlords[-1].add_unit(units[i])
    
    print(f"Created {len(landlords)} landlords")
    
    # Create rental market
    market = RentalMarket(units)

    # Assign initial households to units
    # Try to house about 80% of households initially, but not more than available units
    num_to_house = min(int(len(households) * 0.8), len(units))
    print(f"Planning to house {num_to_house} out of {len(households)} households")
    
    random.shuffle(households)  # Randomize order
    housed_households = households[:num_to_house]
    unhoused_households = households[num_to_house:]

    # Determine which households will be owner-occupiers (about half)
    num_owners = len(housed_households) // 2
    owner_households = housed_households[:num_owners]
    renter_households = housed_households[num_owners:]
    
    if initial_households > 20:
        # Only print debug info once for large simulations
        if not hasattr(initialize_simulation, '_housing_logged'):
            print(f"Planning to house {len(housed_households)} out of {len(households)} households")
            print(f"Owner households: {len(owner_households)}, Renter households: {len(renter_households)}")
            initialize_simulation._housing_logged = True

    # Assign owner-occupiers first
    available_units = [u for u in units if not u.occupied]
    if initial_households > 20 and not hasattr(initialize_simulation, '_owner_logged'):
        print(f"Available units before owner assignment: {len(available_units)}")
        initialize_simulation._owner_logged = True
    
    successfully_housed_owners = 0
    for household in owner_households:
        if available_units:
            unit = random.choice(available_units)
            # Calculate property value and mortgage
            property_value = unit._calculate_market_value()
            down_payment = min(household.wealth, property_value * 0.2)  # 20% down payment if possible
            mortgage_balance = property_value - down_payment
            
            # Update household wealth to reflect down payment
            household.wealth -= down_payment
            
            # Set up household as owner-occupier
            household.is_owner_occupier = True
            household.mortgage_balance = mortgage_balance
            household.mortgage_interest_rate = 0.03  # 3% interest rate
            household.mortgage_term = 30  # 30-year mortgage
            
            # Calculate monthly payment
            r = household.mortgage_interest_rate / 12  # Monthly interest rate
            n = household.mortgage_term * 12  # Total number of payments
            household.monthly_payment = mortgage_balance * (r * (1 + r)**n) / ((1 + r)**n - 1)
            
            # Use proper assign_owner method
            unit.assign_owner(household)
            available_units.remove(unit)
            
            # Set up ownership relationship (no rental contract needed)
            household.owned_unit = unit
            household.housed = True
            household.calculate_satisfaction_owner()
            successfully_housed_owners += 1

    if initial_households > 20 and not hasattr(initialize_simulation, '_renter_logged'):
        print(f"Successfully housed {successfully_housed_owners} owner-occupiers")
        initialize_simulation._renter_logged = True

    # Assign remaining households as renters
    available_units = [u for u in units if not u.occupied]
    if initial_households > 20 and not hasattr(initialize_simulation, '_renter_assignment_logged'):
        print(f"Available units before renter assignment: {len(available_units)}")
        initialize_simulation._renter_assignment_logged = True
    
    successfully_housed_renters = 0
    for household in renter_households:
        if available_units:
            unit = random.choice(available_units)
            unit.assign(household)
            available_units.remove(unit)
            # Set initial contract
            household.contract = Contract(household, unit)
            household.housed = True
            # Calculate initial satisfaction
            household.calculate_satisfaction()
            successfully_housed_renters += 1

    if initial_households > 20 and not hasattr(initialize_simulation, '_final_logged'):
        print(f"Successfully housed {successfully_housed_renters} renters")
        print(f"Total housed: {successfully_housed_owners + successfully_housed_renters}")
        print(f"Units still available: {len([u for u in units if not u.occupied])}")
        print(f"Occupied units: {len([u for u in units if u.occupied])}")
        print(f"Units with household property: {len([u for u in units if u.household])}")
        initialize_simulation._final_logged = True

    # Create policy based on parameters
    if lvt_enabled:
        from models.policy import LandValueTaxPolicy
        policy = LandValueTaxPolicy(lvt_rate=lvt_rate)
    elif rent_cap_enabled:
        from models.policy import RentCapPolicy
        policy = RentCapPolicy()
    else:
        policy = None

    # Create simulation
    sim = RealtimeSimulation(
        households=households,
        landlords=landlords,
        rental_market=market,
        policy=policy,
        years=years,
        migration_rate=migration_rate
    )
    
    return sim 