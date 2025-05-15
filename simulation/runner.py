# simulation/runner.py
import random
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from visualization.animated_sim import HousingVisualization
import copy
from models.household import Household
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy

class Simulation:
    def __init__(self, households, landlords, rental_market, policy, years=1):
        self.households = households
        self.landlords = landlords
        self.rental_market = rental_market
        self.policy = policy
        self.years = years
        self.metrics = []
        self.property_tax_rate = 0.02  # 2% per year
        self.wealth_tax_rate = 0.012   # 1.2% per year
        self.wealth_tax_threshold = 50000
        self.total_property_tax_paid = 0
        self.total_wealth_tax_paid = 0
        
        # Initialize detailed metrics tracking
        self.detailed_metrics = {
            'life_stage_distribution': defaultdict(int),
            'income_distribution': defaultdict(int),
            'wealth_distribution': defaultdict(int),
            'mobility_events': [],
            'renovation_events': [],
            'market_conditions': []
        }
        self.occupancy_history = []  # NEW: list of lists of (unit_id, household_id, household_size)

    def step(self, year, month):
        # Update market conditions
        self.rental_market.update_market_conditions()
        market_conditions = self.rental_market.market_conditions

        # Update households
        for household in self.households:
            household.update_month(year, month)
            household.consider_moving(self.rental_market, self.policy, year, month)

            # Force eviction if rent burden is too high (only for renters with a contract)
            if (
                household.housed
                and not getattr(household, 'is_owner_occupier', False)
                and household.contract is not None
                and household.current_rent_burden() > 0.6
            ):
                household.contract.unit.vacate()
                household.contract = None
                household.housed = False
                household.satisfaction = 0

        # Update landlords and their units
        for landlord in self.landlords:
            landlord.update(market_conditions)
            landlord.update_rents(self.policy, market_conditions)

        # Government inspects units
        for landlord in self.landlords:
            for unit in landlord.units:
                if unit.occupied and random.random() < self.policy.inspection_rate:
                    self.policy.inspect(unit)

        # Landlords collect rent
        for landlord in self.landlords:
            landlord.collect_rent()

        # Property tax (monthly, pro-rated)
        property_tax_this_month = 0
        for landlord in self.landlords:
            for unit in landlord.units:
                property_value = unit.base_rent * 12 * 20  # proxy for property value
                tax = (self.property_tax_rate / 12) * property_value
                landlord.total_profit -= tax
                property_tax_this_month += tax
        self.total_property_tax_paid += property_tax_this_month

        # Wealth tax (annually, at end of year)
        wealth_tax_this_month = 0
        if month == 12:
            for household in self.households:
                taxable_wealth = max(0, household.wealth - self.wealth_tax_threshold)
                tax = self.wealth_tax_rate * taxable_wealth  # full year
                household.wealth -= tax
                wealth_tax_this_month += tax
        self.total_wealth_tax_paid += wealth_tax_this_month

        # Ownership transitions (owner-occupiers may sell, renters may buy)
        # 1. Owner-occupiers: If satisfaction < 0.5 (was 0.3), or with 10% random chance, sell and become renter
        for household in self.households:
            if getattr(household, 'is_owner_occupier', False) and (
                household.satisfaction < 0.5 or random.random() < 0.1):
                unit = getattr(household, 'owned_unit', None)
                if unit is not None:
                    # Sell house: add property value to wealth, clear mortgage
                    property_value = unit.base_rent * 12 * 20
                    equity = max(0, property_value - getattr(household, 'mortgage_balance', 0))
                    household.wealth += equity
                    household.mortgage_balance = 0
                    household.monthly_payment = 0
                    household.is_owner_occupier = False
                    household.owned_unit = None
                    unit.remove_owner()
                    household.housed = False
                    household.contract = None
                    # Assign the now-vacant unit to a random landlord
                    if self.landlords:
                        random.choice(self.landlords).add_unit(unit)
        # 2. Renters: If wealth > 20000 (was 40000), or with 10% random chance, may buy a vacant unit
        for household in self.households:
            if not getattr(household, 'is_owner_occupier', False) and household.housed and (
                household.wealth > 20000 or random.random() < 0.1):
                # Find a vacant, non-owner-occupied unit
                vacant_units = [u for u in self.rental_market.units if not u.occupied and not getattr(u, 'is_owner_occupied', False)]
                if vacant_units:
                    unit = random.choice(vacant_units)
                    # Buy house: pay 20% down, get mortgage for 80%
                    property_value = unit.base_rent * 12 * 20
                    down_payment = 0.2 * property_value
                    if household.wealth >= down_payment:
                        household.buy_home(unit)

        # Lower the wealth tax threshold for demonstration
        self.wealth_tax_threshold = 10000

        # Record metrics
        self._record_detailed_metrics(year, month)
        self._record_basic_metrics(year, month)

        # NEW: Record occupancy for this step
        step_occupancy = []
        for unit in self.rental_market.units:
            if unit.occupied and unit.tenant:
                step_occupancy.append((unit.id, unit.tenant.id, unit.tenant.size))
            else:
                step_occupancy.append((unit.id, None, 0))
        self.occupancy_history.append(step_occupancy)

    def _record_detailed_metrics(self, year, month):
        # Record life stage distribution
        life_stages = defaultdict(int)
        for h in self.households:
            life_stages[h.life_stage] += 1
        self.detailed_metrics['life_stage_distribution'][f"{year}-{month:02}"] = dict(life_stages)

        # Record income distribution
        income_bins = [0, 1000, 2000, 3000, 4000, float('inf')]
        income_dist = defaultdict(int)
        for h in self.households:
            for i in range(len(income_bins)-1):
                if income_bins[i] <= h.income < income_bins[i+1]:
                    income_dist[f"{income_bins[i]}-{income_bins[i+1]}"] += 1
                    break
        self.detailed_metrics['income_distribution'][f"{year}-{month:02}"] = dict(income_dist)

        # Record wealth distribution
        wealth_bins = [0, 5000, 10000, 20000, 50000, float('inf')]
        wealth_dist = defaultdict(int)
        for h in self.households:
            for i in range(len(wealth_bins)-1):
                if wealth_bins[i] <= h.wealth < wealth_bins[i+1]:
                    wealth_dist[f"{wealth_bins[i]}-{wealth_bins[i+1]}"] += 1
                    break
        self.detailed_metrics['wealth_distribution'][f"{year}-{month:02}"] = dict(wealth_dist)

        # Record market conditions
        self.detailed_metrics['market_conditions'].append({
            'year': year,
            'month': month,
            'conditions': self.rental_market.market_conditions.copy()
        })

    def _record_basic_metrics(self, year, month):
        # Calculate basic metrics
        housed = sum(h.housed for h in self.households)
        avg_burden = sum(h.current_rent_burden() or 0 for h in self.households if h.housed) / housed if housed else 0
        avg_satisfaction = sum(h.satisfaction for h in self.households) / len(self.households)
        total_profit = sum(l.total_profit for l in self.landlords)
        
        # Calculate additional metrics
        avg_income = np.mean([h.income for h in self.households])
        avg_wealth = np.mean([h.wealth for h in self.households])
        avg_quality = np.mean([u.quality for u in self.rental_market.units])
        avg_rent = np.mean([u.rent for u in self.rental_market.units])
        vacancy_rate = len([u for u in self.rental_market.units if not u.occupied]) / len(self.rental_market.units)
        
        # Calculate mobility metrics
        mobility_rate = sum(1 for h in self.households if h.months_in_current_unit == 0) / len(self.households)
        
        # Calculate renovation metrics
        renovation_count = sum(1 for u in self.rental_market.units if u.last_renovation == 0)

        self.metrics.append({
            "year": year,
            "month": month,
            "housed": housed,
            "avg_burden": avg_burden,
            "satisfaction": avg_satisfaction,
            "profit": total_profit,
            "violations": self.policy.violations_found,
            "avg_income": avg_income,
            "avg_wealth": avg_wealth,
            "avg_quality": avg_quality,
            "avg_rent": avg_rent,
            "vacancy_rate": vacancy_rate,
            "mobility_rate": mobility_rate,
            "renovation_count": renovation_count,
            "property_tax": self.total_property_tax_paid,
            "wealth_tax": self.total_wealth_tax_paid
        })

    def run(self):
        for year in range(1, self.years + 1):
            for month in range(1, 13):
                self.step(year, month)

    def report(self):
        print("\nBasic Metrics:")
        for m in self.metrics:
            print(f"{m['year']:>4}-{m['month']:>02} | "
                  f"Housed: {m['housed']:>3} | "
                  f"Burden: {m['avg_burden']:.2f} | "
                  f"Satisfaction: {m['satisfaction']:.2f} | "
                  f"Profit: {m['profit']:.0f} | "
                  f"Violations: {m['violations']}")

        print("\nSummary Statistics:")
        final_metrics = self.metrics[-1]
        print(f"Final Average Income: ${final_metrics['avg_income']:.2f}")
        print(f"Final Average Wealth: ${final_metrics['avg_wealth']:.2f}")
        print(f"Final Average Rent: ${final_metrics['avg_rent']:.2f}")
        print(f"Final Vacancy Rate: {final_metrics['vacancy_rate']:.2%}")
        print(f"Final Mobility Rate: {final_metrics['mobility_rate']:.2%}")
        print(f"Total Renovations: {final_metrics['renovation_count']}")

        print("\nFinal Life Stage Distribution:")
        life_stages = self.detailed_metrics['life_stage_distribution'][f"{self.years}-12"]
        for stage, count in life_stages.items():
            print(f"{stage}: {count} households")

    def get_detailed_metrics(self):
        return self.detailed_metrics

    def get_market_trends(self):
        return self.rental_market.get_historical_trends()

random.seed(123)
base_households = []
base_units = []
num_households = 100
num_owner_occupiers = int(0.3 * num_households)
owner_indices = random.sample(range(num_households), num_owner_occupiers)

for i in range(num_households):
    age = max(18, min(85, random.normalvariate(45, 15)))
    if age < 30:       size = random.randint(1,2)
    elif age < 45:     size = random.randint(2,4)
    else:              size = random.randint(1,3)
    income = random.randint(1000,3000)
    wealth = random.randint(0,10000)
    is_owner_occupier = i in owner_indices
    base_households.append(
        Household(id=i, age=age, size=size, income=income, wealth=wealth, is_owner_occupier=is_owner_occupier)
    )

for i in range(num_households):
    quality   = random.uniform(0.3,0.9)
    base_rent = random.randint(500,1500)
    base_units.append(
        RentalUnit(id=i, quality=quality, base_rent=base_rent)
    )

# Assign owner-occupiers to units and set up mortgage
for idx in owner_indices:
    hh = base_households[idx]
    unit = base_units[idx]  # 1-to-1 mapping for simplicity
    unit.assign_owner(hh)
    # Set up mortgage: assume 80% LTV, 30-year term, 3% rate
    property_value = unit.base_rent * 12 * 20
    mortgage_balance = 0.8 * property_value
    hh.is_owner_occupier = True
    hh.mortgage_balance = mortgage_balance
    hh.mortgage_interest_rate = 0.03
    hh.mortgage_term = 30
    r = hh.mortgage_interest_rate / 12
    n = hh.mortgage_term * 12
    hh.monthly_payment = (mortgage_balance * r * (1 + r) ** n) / ((1 + r) ** n - 1)
    hh.contract = None  # Not a rental contract
    hh.housed = True
    hh.owned_unit = unit  # Reference to owned unit

# Remove owner-occupied units from rental pool for landlords
rental_units = [u for u in base_units if not u.is_owner_occupied]

def make_landlords(units, compliant_rate=0.7):
    L = []
    n_landlords = len(units)//10
    for j in range(n_landlords):
        chunk = units[j*10:(j+1)*10]
        L.append(
            Landlord(
                id=j,
                units=chunk,
                is_compliant=(random.random() < compliant_rate)
            )
        )
    return L

# 2. Scenario A: With Rent Cap
hh_cap = copy.deepcopy(base_households)
u_cap  = copy.deepcopy(base_units)
rental_units_cap = [u for u in u_cap if not u.is_owner_occupied]
ll_cap = make_landlords(rental_units_cap)
market_cap = RentalMarket(u_cap)
policy_cap = RentCapPolicy(
    rent_cap_ratio=0.3,
    max_increase_rate=0.05,
    inspection_rate=0.1
)
sim_cap = Simulation(hh_cap, ll_cap, market_cap, policy_cap, years=2)
sim_cap.run()

# 3. Scenario B: No Rent Cap
hh_nocap = copy.deepcopy(base_households)
u_nocap  = copy.deepcopy(base_units)
rental_units_nocap = [u for u in u_nocap if not u.is_owner_occupied]
ll_nocap = make_landlords(rental_units_nocap)
market_nocap = RentalMarket(u_nocap)
policy_nocap = RentCapPolicy(
    rent_cap_ratio=1.0,    # effectively unlimited
    max_increase_rate=0.2,
    inspection_rate=0.0
)
sim_nocap = Simulation(hh_nocap, ll_nocap, market_nocap, policy_nocap, years=2)
sim_nocap.run()

# 4. Now do your visualization (your code here)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(36, 15))
vis_cap = HousingVisualization(sim_cap, ax=ax1)
vis_nocap = HousingVisualization(sim_nocap, ax=ax2)
ani1 = vis_cap.animate_on_existing_axis()
ani2 = vis_nocap.animate_on_existing_axis()
plt.show()
