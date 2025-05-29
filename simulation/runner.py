# simulation/runner.py
import random
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from visualization.animated_sim import HousingVisualization
import copy
from models.household import Household, Contract
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
        self.next_household_id = max(h.id for h in households) + 1 if households else 0
        
        # Initialize detailed metrics tracking
        self.detailed_metrics = {
            'life_stage_distribution': defaultdict(int),
            'income_distribution': defaultdict(int),
            'wealth_distribution': defaultdict(int),
            'mobility_events': [],
            'renovation_events': [],
            'market_conditions': []
        }
        self.occupancy_history = []

    def _create_new_household(self):
        # Create a new household with random characteristics
        age = max(18, min(85, random.normalvariate(45, 15)))
        if age < 30:
            size = random.randint(1,2)
        elif age < 45:
            size = random.randint(2,4)
        else:
            size = random.randint(1,3)
        income = random.randint(1000,3000)
        wealth = random.randint(0,10000)
        
        new_household = Household(
            id=self.next_household_id,
            age=age,
            size=size,
            income=income,
            wealth=wealth
        )
        self.next_household_id += 1
        return new_household

    def _process_population_changes(self, year, period):
        # Track actions for this step
        actions_this_step = 0
        
        # Process household departures and lifecycle events
        households_to_remove = []
        new_households = []

        # 1. Household departures (leaving the neighborhood) - increased rate
        for household in self.households:
            if household not in households_to_remove:
                # Increased departure rates for dynamic behavior
                leave_chance = 0.05  # Base 5% chance per period (increased from 0.1%)
                
                # Increase chance if household is struggling
                if household.current_rent_burden() > 0.5:
                    leave_chance += 0.1  # Strong incentive to leave if struggling
                if not household.housed:
                    leave_chance += 0.15  # Very high chance for unhoused to leave
                if household.satisfaction < 0.3:
                    leave_chance += 0.08
                
                # Age-based factors
                if household.age > 75:
                    leave_chance += 0.1  # Retirement/moving away
                
                if random.random() < leave_chance:
                    # If leaving, properly handle their current housing
                    if household.housed:
                        if household.contract and household.contract.unit:
                            household.contract.unit.remove_tenant(household)
                    households_to_remove.append(household)
                    actions_this_step += 1

        # 2. Household breakups (more common now) - people splitting up
        for household in self.households:
            if household not in households_to_remove and household.size > 1:
                breakup_chance = 0.08  # Base 8% chance per period (much higher)
                
                # Increased chance based on various factors
                if household.satisfaction < 0.4:
                    breakup_chance += 0.1
                if household.current_rent_burden() > 0.5:
                    breakup_chance += 0.12
                if household.size > 3:  # Large households more likely to split
                    breakup_chance += 0.05
                
                if random.random() < breakup_chance:
                    # Split into two households
                    new_size = max(1, household.size // 2)
                    if new_size > 0:
                        new_hh = self._create_new_household()
                        new_hh.size = new_size
                        new_hh.wealth = household.wealth * 0.4  # Split wealth
                        new_hh.income = household.income * 0.6  # New household gets lower income initially
                        household.size -= new_size
                        household.wealth *= 0.6
                        new_households.append(new_hh)
                        actions_this_step += 1
                        
                        # Record breakup event
                        if household.contract and household.contract.unit:
                            household.record_breakup_event(new_hh, year, period)
                        
                        # Handle housing situation - new household becomes unhoused initially
                        new_hh.housed = False
                        new_hh.contract = None

        # 3. Household mergers/sharing (people moving in together) - increased rate
        unhoused_households = [h for h in self.households if not h.housed and h not in households_to_remove]
        housed_households = [h for h in self.households if h.housed and h not in households_to_remove]
        
        # Try to get unhoused households to share with housed ones
        for unhoused_hh in unhoused_households[:3]:  # Limit to prevent too many actions
            for housed_hh in housed_households:
                if (housed_hh.contract and housed_hh.contract.unit and 
                    len(housed_hh.contract.unit.tenants) < 2 and  # Max 2 households per unit
                    abs(housed_hh.age - unhoused_hh.age) < 15 and
                    random.random() < 0.15):  # 15% chance of sharing
                    
                    # Move unhoused household to share the unit
                    unit = housed_hh.contract.unit
                    unit.add_tenant(unhoused_hh)
                    unhoused_hh.contract = Contract(unhoused_hh, unit)
                    unhoused_hh.housed = True
                    unhoused_hh.calculate_satisfaction()
                    actions_this_step += 1
                    
                    # Record merger event
                    housed_hh.record_merger_event(unhoused_hh, year, period)
                    break

        # 4. New household arrivals (people moving into the neighborhood) - much higher rate
        current_population = len(self.households) - len(households_to_remove) + len(new_households)
        target_population = 100  # Try to maintain around 100 households
        
        # High arrival rate to maintain population and create activity
        arrival_rate = 0.15  # 15% chance per step (much higher)
        
        # Add more households if below target
        while current_population < target_population and random.random() < arrival_rate:
            new_household = self._create_new_household()
            new_household.housed = False  # Start as unhoused
            new_households.append(new_household)
            actions_this_step += 1
            current_population += 1

        # Remove departing households
        for household in households_to_remove:
            if household in self.households:
                self.households.remove(household)

        # Add new households from lifecycle events and arrivals
        self.households.extend(new_households)
        
        return actions_this_step

    def step(self, year, period):
        # Track total actions for this step
        total_actions = 0
        
        # Process population changes first (returns action count)
        population_actions = self._process_population_changes(year, period)
        total_actions += population_actions
        
        # Update market conditions
        self.rental_market.update_market_conditions()
        market_conditions = self.rental_market.market_conditions

        # Update households and track movement actions
        movement_actions = 0
        for household in self.households:
            # Update household for this period
            household.update_month(year, period)
            
            # Track if household was housed before considering moving
            was_housed = household.housed
            current_unit = household.contract.unit if household.contract else None
            
            # Check for potential eviction due to high rent burden
            if (household.housed and 
                household.contract is not None):
                
                rent_burden = household.current_rent_burden()
                # Gradual eviction risk based on rent burden
                if rent_burden > 0.6:  # Start risk at 60% burden (increased threshold)
                    eviction_risk = (rent_burden - 0.6) * 3  # More aggressive eviction
                    if random.random() < eviction_risk:
                        household.contract.unit.remove_tenant(household)
                        household.contract = None
                        household.housed = False
                        household.satisfaction = 0
                        household.add_event({
                            "type": "EVICTED",
                            "reason": "High rent burden",
                            "rent_burden": rent_burden
                        }, year, period)
                        total_actions += 1
            
            # Consider moving for all households
            household.consider_moving(self.rental_market, self.policy, year, period)
            
            # Check if household moved
            if household.housed != was_housed or (household.contract and household.contract.unit != current_unit):
                movement_actions += 1

        total_actions += movement_actions

        # Update landlords and their units
        for landlord in self.landlords:
            landlord.update(market_conditions)
            landlord.update_rents(self.policy, market_conditions)

        # Government inspects units (twice per period)
        for landlord in self.landlords:
            for unit in landlord.units:
                if unit.occupied and random.random() < self.policy.inspection_rate * 2:
                    self.policy.inspect(unit)

        # Landlords collect rent (6 months worth)
        for landlord in self.landlords:
            landlord.collect_rent(periods=6)

        # Property tax (6 months, pro-rated)
        property_tax_this_period = 0
        for landlord in self.landlords:
            for unit in landlord.units:
                property_value = unit.base_rent * 12 * 20  # proxy for property value
                tax = (self.property_tax_rate / 2) * property_value  # Half-year tax
                landlord.total_profit -= tax
                property_tax_this_period += tax
        self.total_property_tax_paid += property_tax_this_period

        # Wealth tax (annually, at end of year)
        wealth_tax_this_period = 0
        if period == 2:  # End of year (second period)
            for household in self.households:
                taxable_wealth = max(0, household.wealth - self.wealth_tax_threshold)
                tax = self.wealth_tax_rate * taxable_wealth  # full year
                household.wealth -= tax
                wealth_tax_this_period += tax
        self.total_wealth_tax_paid += wealth_tax_this_period

        # Lower the wealth tax threshold for demonstration
        self.wealth_tax_threshold = 10000

        # Record metrics including action count
        self._record_detailed_metrics(year, period)
        self._record_basic_metrics(year, period, total_actions)

        # Record occupancy for this step
        step_occupancy = []
        for unit in self.rental_market.units:
            if unit.occupied and unit.tenants:
                # Record all tenants in the unit
                for tenant in unit.tenants:
                    step_occupancy.append((unit.id, tenant.id, tenant.size))
            else:
                # Vacant unit
                step_occupancy.append((unit.id, None, 0))
        self.occupancy_history.append(step_occupancy)

    def _record_detailed_metrics(self, year, period):
        # Record life stage distribution
        life_stages = defaultdict(int)
        for h in self.households:
            life_stages[h.life_stage] += 1
        self.detailed_metrics['life_stage_distribution'][f"{year}-{period}"] = dict(life_stages)

        # Record income distribution
        income_bins = [0, 1000, 2000, 3000, 4000, float('inf')]
        income_dist = defaultdict(int)
        for h in self.households:
            for i in range(len(income_bins)-1):
                if income_bins[i] <= h.income < income_bins[i+1]:
                    income_dist[f"{income_bins[i]}-{income_bins[i+1]}"] += 1
                    break
        self.detailed_metrics['income_distribution'][f"{year}-{period}"] = dict(income_dist)

        # Record wealth distribution
        wealth_bins = [0, 5000, 10000, 20000, 50000, float('inf')]
        wealth_dist = defaultdict(int)
        for h in self.households:
            for i in range(len(wealth_bins)-1):
                if wealth_bins[i] <= h.wealth < wealth_bins[i+1]:
                    wealth_dist[f"{wealth_bins[i]}-{wealth_bins[i+1]}"] += 1
                    break
        self.detailed_metrics['wealth_distribution'][f"{year}-{period}"] = dict(wealth_dist)

        # Record market conditions
        self.detailed_metrics['market_conditions'].append({
            'year': year,
            'period': period,
            'conditions': self.rental_market.market_conditions.copy()
        })

    def _record_basic_metrics(self, year, period, total_actions):
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
            "period": period,
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
            "wealth_tax": self.total_wealth_tax_paid,
            "total_actions": total_actions
        })

    def run(self):
        for year in range(1, self.years + 1):
            for period in range(1, 3):  # Two 6-month periods per year
                self.step(year, period)

    def report(self):
        print("\nBasic Metrics:")
        for m in self.metrics:
            print(f"{m['year']:>4}-{m['period']:>02} | "
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
        life_stages = self.detailed_metrics['life_stage_distribution'][f"{self.years}-2"]
        for stage, count in life_stages.items():
            print(f"{stage}: {count} households")

    def get_detailed_metrics(self):
        return self.detailed_metrics

    def get_market_trends(self):
        return self.rental_market.get_historical_trends()
