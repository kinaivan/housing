import random
from models.market import RentalMarket
from models.unit import RentalUnit, Landlord
from models.household import Household
from models.policy import RentCapPolicy
from simulation.realtime_sim import RealtimeSimulation

def create_simulation(is_cap_scenario=True):
    """Create a new simulation instance"""
    # Create units first
    units = []
    for i in range(100):
        unit = RentalUnit(
            id=i,
            quality=random.uniform(0.3, 0.9),
            base_rent=random.randint(800, 2000),
            size=random.randint(1, 4),
            location=random.uniform(0, 1)
        )
        units.append(unit)
    
    # Create rental market with units
    market = RentalMarket(units)
    
    # Create households
    households = []
    for i in range(120):
        household = Household(
            id=i,
            age=random.randint(25, 65),
            size=random.randint(1, 4),
            income=random.randint(2000, 8000),
            wealth=random.randint(10000, 100000)
        )
        households.append(household)
    
    # Create landlords
    landlords = []
    for i in range(10):  # 10 landlords
        landlord_units = units[i*10:(i+1)*10]  # Each landlord gets 10 units
        landlord = Landlord(
            id=i,
            units=landlord_units,
            is_compliant=is_cap_scenario
        )
        landlords.append(landlord)
    
    # Create policy
    if is_cap_scenario:
        policy = RentCapPolicy(
            rent_cap_ratio=0.3,
            max_increase_rate=0.05,
            inspection_rate=0.1
        )
    else:
        policy = RentCapPolicy(
            rent_cap_ratio=1.0,  # effectively unlimited
            max_increase_rate=0.2,
            inspection_rate=0.0
        )
    
    # Create simulation with all components
    sim = RealtimeSimulation(
        households=households,
        landlords=landlords,
        rental_market=market,
        policy=policy,
        years=10  # 10 years
    )
    
    # Set periods per year (6-month periods)
    sim.total_periods = 20  # 10 years * 2 periods per year
    sim.current_period = 1
    sim.current_year = 1

    sim.step()  # Advance the simulation once so there is a frame to visualize

    return sim 