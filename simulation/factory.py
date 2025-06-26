import random
from typing import List

from models.household import Household
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy
from simulation.realtime_sim import RealtimeSimulation


# -----------------------------------------------------------------------------
# Utility functions to create demo data for a RealtimeSimulation instance.
# These were previously located inside the Dash callback module; they are now
# standalone and contain **no Dash dependencies**, so they can be imported by
# Celery workers or other back-end code without pulling in heavy UI libraries.
# -----------------------------------------------------------------------------

def create_household(id: int) -> Household:
    """Return a Household with a semi-realistic size distribution."""
    age = random.randint(25, 60)
    # Size distribution based on age
    if age < 30:
        size = random.choices([1, 2], weights=[70, 30])[0]
    elif age < 45:
        size = random.choices([1, 2, 3, 4], weights=[20, 40, 25, 15])[0]
    else:
        size = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
    return Household(id=id, age=age, size=size, income=2500, wealth=10000)


def initialize_simulation(
    *,
    initial_households: int = 20,
    migration_rate: float = 0.1,
    years: int = 10,
) -> RealtimeSimulation:
    """Create a fresh `RealtimeSimulation` populated with demo data.

    Parameters
    ----------
    initial_households : int
        Number of starting households.
    migration_rate : float
        Stored on the resulting simulation object for later reference.
    years : int
        Number of years (12 periods each) that the simulation will run.
    """
    # Households / landlords / units ----------------------------------------------------------------
    households: List[Household] = [create_household(i) for i in range(initial_households)]
    landlords: List[Landlord] = [Landlord(id=0, units=[])]

    units: List[RentalUnit] = [RentalUnit(id=i, quality=1.0, base_rent=1200) for i in range(20)]
    landlords[0].units = units

    rental_market = RentalMarket(units=units)
    policy = RentCapPolicy()

    sim = RealtimeSimulation(households, landlords, rental_market, policy, years)

    # Store the parameters on the object for easy inspection
    setattr(sim, "migration_rate", migration_rate)
    sim.last_initial_households = initial_households
    sim.last_migration_rate = migration_rate

    return sim 