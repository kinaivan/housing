# simulation/runner.py
import random
import numpy as np
from collections import defaultdict
import copy
from models.household import Household, Contract
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy, LandValueTaxPolicy

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
        self.moves_this_period = []  # Track moves within each period
        
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
        
        # Initialize unit history tracking for dashboard
        self.unit_history = defaultdict(list)  # unit_id -> list of period data

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
        
        # Track households to remove after processing
        households_to_remove = set()
        
        # 1. Natural population changes (aging, etc)
        for household in self.households:
            # Age increment handled in household.update_month()
            pass
            
        # 2. Household breakups
        for household in self.households:
            if household.size > 1:  # Can only break up if more than 1 person
                breakup_chance = 0.02  # 2% base chance per period
                
                # Increase chance based on financial stress
                if household.contract:
                    rent_burden = household.current_rent_burden()
                    if rent_burden > 0.4:  # Moderate stress
                        breakup_chance += 0.02
                    if rent_burden > 0.6:  # High stress
                        breakup_chance += 0.03
                
                if random.random() < breakup_chance:
                    # Determine split
                    original_size = household.size
                    new_size = random.randint(1, household.size - 1)
                    remaining_size = household.size - new_size
                    
                    # Create new household
                    new_hh = Household(
                        id=self.next_household_id,
                        age=max(18, household.age - random.randint(0, 10)),
                        size=new_size,
                        income=household.income * (new_size / original_size),
                        wealth=household.wealth * (new_size / original_size)
                    )
                    self.next_household_id += 1
                    
                    # Update original household
                    household.size = remaining_size
                    household.income *= (remaining_size / original_size)
                    household.wealth *= (remaining_size / original_size)
                    
                    # Add new household to simulation
                    self.households.append(new_hh)
                    actions_this_step += 1
                    
                    # Record the breakup event
                    breakup_event = {
                        "type": "HOUSEHOLD_BREAKUP",
                        "household_id": household.id,
                        "household_name": household.name,
                        "from_unit_id": household.contract.unit.id if household.contract else None,
                        "original_size": original_size,
                        "remaining_size": remaining_size,
                        "new_household_id": new_hh.id,
                        "new_household_size": new_size
                    }
                    self.events_this_period.append(breakup_event)
        
        # 3. Household mergers
        unhoused_households = [h for h in self.households 
                             if not h.housed and h not in households_to_remove and h.size > 0]
        housed_households = [h for h in self.households 
                           if h.housed and h not in households_to_remove and h.size > 0]
        
        for unhoused_hh in unhoused_households:
            # Try to find a compatible housed household to merge with
            merge_chance = 0.1  # 10% base chance
            if random.random() < merge_chance:
                compatible_households = [
                    h for h in housed_households
                    if h.contract and h.contract.unit and
                    h.contract.unit.size >= (h.size + unhoused_hh.size)
                ]
                
                if compatible_households:
                    target_hh = random.choice(compatible_households)
                    
                    # Record the merger event
                    merger_event = {
                        "type": "HOUSEHOLD_MERGER",
                        "household_id": target_hh.id,
                        "household_name": target_hh.name,
                        "from_unit_id": target_hh.contract.unit.id,
                        "original_size": target_hh.size,
                        "other_household_id": unhoused_hh.id,
                        "other_household_size": unhoused_hh.size,
                        "combined_size": target_hh.size + unhoused_hh.size
                    }
                    self.events_this_period.append(merger_event)
                    
                    # Perform the merger
                    target_hh.size += unhoused_hh.size
                    target_hh.income += unhoused_hh.income
                    target_hh.wealth += unhoused_hh.wealth
                    households_to_remove.add(unhoused_hh)
                    actions_this_step += 1
        
        # Remove merged households
        self.households = [h for h in self.households if h not in households_to_remove]
        
        return actions_this_step

    def step(self, year, period):
        # Reset events for this period
        self.moves_this_period = []
        self.events_this_period = []
        total_actions = 0

        # Update market conditions
        self.rental_market.update_market_conditions()
        market_conditions = self.rental_market.market_conditions

        # Process population changes (births, deaths, aging)
        population_changes = self._process_population_changes(year, period)
        total_actions += population_changes

        # Process household moves
        movement_actions = 0
        for household in self.households:
            # Update household for this period
            household.update_month(year, period)
            
            # Record current state
            was_housed = household.housed
            current_unit = household.contract.unit if household.contract else None
            current_unit_id = current_unit.id if current_unit else None

            # Check if household should move
            if household.should_move(market_conditions):
                # Find and move to new unit
                new_unit = household.find_new_unit(self.rental_market, self.policy)
                if new_unit:
                    household.move_to(new_unit, year, period)
                elif household.housed:
                    # Couldn't find affordable housing, become unhoused
                    if household.contract:
                        household.contract.unit.remove_tenant(household)
                        household.contract = None
                    household.housed = False

            # Get new state
            new_unit = household.contract.unit if household.contract else None
            new_unit_id = new_unit.id if new_unit else None
            
            if current_unit_id != new_unit_id:
                movement_actions += 1
                # Record the move
                move_type = "MOVE"
                if not was_housed and new_unit_id is not None:
                    move_type = "MOVE_IN"
                elif was_housed and new_unit_id is None:
                    move_type = "MOVE_OUT"
                
                move_event = {
                    "type": move_type,
                    "household_id": household.id,
                    "household_name": household.name,
                    "from_unit_id": current_unit_id,
                    "to_unit_id": new_unit_id,
                    "reason": household._determine_move_reason(new_unit) if new_unit else "Became Unhoused"
                }
                self.events_this_period.append(move_event)
                self.moves_this_period.append(move_event)

        total_actions += movement_actions

        # Update landlords and their units
        for landlord in self.landlords:
            landlord.update(market_conditions)
            landlord.update_rents(self.policy, market_conditions)

        # Government inspects units (twice per period)
        for landlord in self.landlords:
            for unit in landlord.units:
                inspection_rate = self.policy.inspection_rate if self.policy else 0.0
                if unit.occupied and random.random() < inspection_rate * 2:
                    if self.policy:  # Only inspect if there's a policy in place
                        self.policy.inspect(unit)

        # Landlords collect rent (6 months worth)
        for landlord in self.landlords:
            landlord.collect_rent(periods=6)

        # Land Value Tax (6 months, pro-rated)
        if isinstance(self.policy, LandValueTaxPolicy):
            for landlord in self.landlords:
                for unit in landlord.units:
                    tax = self.policy.calculate_tax(unit, period_length=0.5)  # 6 months = 0.5 years
                    landlord.total_profit -= tax
                    landlord.wealth -= tax

        # Get list of unhoused households with their details
        unhoused_households = [
            {
                "id": h.id,
                "name": h.name,
                "size": h.size,
                "income": h.income,
                "wealth": h.wealth,
                "months_unhoused": h.months_unhoused if hasattr(h, "months_unhoused") else 0
            }
            for h in self.households if not h.housed
        ]

        # Create frame data with policy metrics and events
        frame_data = {
            "year": year,
            "period": period,
            "units": [
                {
                    "id": unit.id,
                    "occupants": len(unit.tenants),
                    "rent": unit.rent,
                    "is_occupied": unit.occupied,
                    "quality": unit.quality,
                    "lastRenovation": unit.last_renovation,
                    "land_value": unit.land_value,
                    "improvement_value": unit.get_improvement_value(),
                    "household": {
                        "id": unit.tenants[0].id,
                        "name": unit.tenants[0].name,
                        "income": unit.tenants[0].income,
                        "satisfaction": unit.tenants[0].satisfaction,
                        "size": unit.tenants[0].size,
                        "wealth": unit.tenants[0].wealth
                    } if unit.tenants else None
                }
                for landlord in self.landlords
                for unit in landlord.units
            ],
            "metrics": {
                "total_units": len([u for l in self.landlords for u in l.units]),
                "occupied_units": len([u for l in self.landlords for u in l.units if u.occupied]),
                "average_rent": sum(u.rent for l in self.landlords for u in l.units) / len([u for l in self.landlords for u in l.units]) if self.landlords else 0,
                "total_population": sum(len(u.tenants) for l in self.landlords for u in l.units if u.occupied),
                "policy_metrics": self.policy.get_metrics() if self.policy else None
            },
            "moves": self.moves_this_period,
            "events": self.events_this_period,
            "unhoused_households": unhoused_households
        }
        
        # Record metrics and validate data
        self._record_occupancy_state()
        self._record_detailed_metrics(year, period, total_actions)
        self._validate_and_fix_household_unit_consistency()
        
        return frame_data

    def _calculate_property_value(self, unit, year, period):
        """Calculate dynamic property value based on multiple factors"""
        # Base value from rent capitalization (more conservative multiplier)
        base_value = unit.rent * 12 * 12  # 12x annual rent as base multiplier
        
        # Market conditions adjustment (additive, not multiplicative)
        market_demand = self.rental_market.market_conditions.get('market_demand', 0.5)
        price_index = self.rental_market.market_conditions.get('price_index', 100) / 100
        
        # Quality adjustment (smaller range)
        quality_adjustment = (unit.quality - 0.5) * 0.2  # ±10% for quality
        
        # Location value (smaller impact)
        location_premiums = self.rental_market.market_conditions.get('location_premiums', {})
        location_key = round(getattr(unit, 'location', 0.5), 1)
        location_premium = min(0.1, location_premiums.get(location_key, 0))  # Cap at 10%
        
        # Vacancy penalty (smaller impact)
        vacancy_adjustment = 0
        if hasattr(unit, 'vacancy_duration') and unit.vacancy_duration > 0:
            # Property values decrease with extended vacancy
            vacancy_adjustment = -min(0.15, unit.vacancy_duration * 0.03)  # Max -15%
        
        # Renovation bonus (smaller impact)
        renovation_adjustment = 0
        if hasattr(unit, 'last_renovation') and unit.last_renovation > 0:
            # Recent renovations increase property value
            renovation_adjustment = min(0.1, unit.last_renovation * 0.008)  # Max +10%
        
        # Market cycle effects (smaller variation)
        cycle_phase = (year * 2 + period) % 8  # 4-year cycles
        cycle_adjustment = 0.05 * np.sin(cycle_phase * np.pi / 4)  # ±5% variation
        
        # Market demand effect (smaller impact)
        demand_adjustment = (market_demand - 0.5) * 0.1  # ±5% for demand
        
        # Economic volatility (smaller random variation)
        volatility = np.random.normal(0, 0.02)  # ±2% random variation
        
        # Combine all adjustments additively to prevent compounding
        total_adjustment = (quality_adjustment + 
                           location_premium + 
                           vacancy_adjustment + 
                           renovation_adjustment + 
                           cycle_adjustment + 
                           demand_adjustment + 
                           volatility)
        
        # Apply total adjustment to base value
        property_value = base_value * (1 + total_adjustment) * price_index
        
        # Reasonable bounds: 8x to 20x annual rent
        min_value = unit.rent * 12 * 8
        max_value = unit.rent * 12 * 20
        return max(min_value, min(max_value, property_value))

    def _record_detailed_metrics(self, year, period, total_actions):
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
            "violations": self.policy.violations_found if self.policy else 0,
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

    def _validate_and_fix_household_unit_consistency(self):
        """Ensure household-unit relationships are consistent and fix any issues"""
        issues_fixed = 0
        
        # Check all households
        for household in self.households:
            if household.housed and household.contract and household.contract.unit:
                unit = household.contract.unit
                
                # Ensure household is in unit's tenant list
                if household not in unit.tenants:
                    print(f"WARNING: HH {household.id} claims to live in Unit {unit.id} but not in tenant list. Adding.")
                    unit.tenants.append(household)
                    issues_fixed += 1
                
                # Ensure unit is marked as occupied
                if not unit.occupied:
                    print(f"WARNING: Unit {unit.id} has tenants but marked as vacant. Fixing.")
                    unit.occupied = True
                    unit.tenant = unit.tenants[0]  # Set primary tenant
                    issues_fixed += 1
            
            elif household.housed and not household.contract:
                # Household thinks it's housed but has no contract
                print(f"WARNING: HH {household.id} thinks it's housed but has no contract. Fixing.")
                household.housed = False
                issues_fixed += 1
        
        # Check all units
        for unit in self.rental_market.units:
            if unit.occupied and unit.tenants:
                # Ensure all tenants in unit have valid contracts pointing to this unit
                for tenant in unit.tenants[:]:  # Use slice copy to avoid modification during iteration
                    if not tenant.housed or not tenant.contract or tenant.contract.unit != unit:
                        print(f"WARNING: Unit {unit.id} has tenant HH {tenant.id} but relationship broken. Fixing.")
                        unit.tenants.remove(tenant)
                        tenant.housed = False
                        tenant.contract = None
                        issues_fixed += 1
                
                # If no valid tenants remain, mark unit as vacant
                if not unit.tenants:
                    print(f"WARNING: Unit {unit.id} marked occupied but no valid tenants. Marking vacant.")
                    unit.occupied = False
                    unit.tenant = None
                    issues_fixed += 1
                else:
                    # Update primary tenant
                    unit.tenant = unit.tenants[0]
            
            elif unit.occupied and not unit.tenants:
                # Unit marked occupied but no tenants
                print(f"WARNING: Unit {unit.id} marked occupied but no tenants. Marking vacant.")
                unit.occupied = False
                unit.tenant = None
                issues_fixed += 1
            
            elif not unit.occupied and unit.tenants:
                # Unit marked vacant but has tenants
                print(f"WARNING: Unit {unit.id} marked vacant but has tenants. Fixing.")
                unit.occupied = True
                unit.tenant = unit.tenants[0]
                issues_fixed += 1
        
        if issues_fixed > 0:
            print(f"Fixed {issues_fixed} household-unit consistency issues.")
        return issues_fixed
    
    def _record_occupancy_state(self):
        """Record the current occupancy state of all units and unhoused households"""
        occupancy = []
        for unit in self.rental_market.units:
            if unit.occupied and unit.tenants:
                # Get the total size of all households in the unit
                total_size = unit.get_total_household_size()
                # Record unit ID, household ID of first tenant, and total household size
                occupancy.append((unit.id, unit.tenants[0].id, total_size))
            else:
                occupancy.append((unit.id, None, 0))
        
        # Record the current state
        self.occupancy_history.append(occupancy)
        
        # Also record unhoused households with their sizes
        unhoused = [h for h in self.households if not h.housed and h.size > 0]
        if hasattr(self, 'unhoused_households'):
            self.unhoused_households = unhoused

    def validate_data_integrity(self):
        """Validate that household-unit relationships are consistent"""
        errors = []
        
        # Check households
        for household in self.households:
            if household.housed:
                if not household.contract:
                    errors.append(f"HH {household.id}: Housed but no contract")
                elif not household.contract.unit:
                    errors.append(f"HH {household.id}: Has contract but no unit")
                elif household not in household.contract.unit.tenants:
                    errors.append(f"HH {household.id}: Not in unit {household.contract.unit.id} tenant list")
        
        # Check units
        for unit in self.rental_market.units:
            if unit.occupied:
                if not unit.tenants:
                    errors.append(f"Unit {unit.id}: Occupied but no tenants")
                else:
                    for tenant in unit.tenants:
                        if not tenant.housed:
                            errors.append(f"Unit {unit.id}: Tenant HH {tenant.id} not marked as housed")
                        elif not tenant.contract or tenant.contract.unit != unit:
                            errors.append(f"Unit {unit.id}: Tenant HH {tenant.id} contract mismatch")
            else:
                if unit.tenants:
                    errors.append(f"Unit {unit.id}: Not occupied but has tenants: {[t.id for t in unit.tenants]}")
        
        return errors
