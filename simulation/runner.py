# simulation/runner.py
import random
import numpy as np
from collections import defaultdict
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
        
        # Process household departures and lifecycle events
        households_to_remove = []
        new_households = []

        # 1. Household departures (leaving the neighborhood) - reduced rates
        for household in self.households:
            if household not in households_to_remove:
                # Lower base departure rate
                leave_chance = 0.02  # Base 2% chance per period
                
                # Moderate incentives to leave
                if household.current_rent_burden() > 0.6:  # Increased threshold
                    leave_chance += 0.05  # Reduced penalty
                if not household.housed:
                    leave_chance += 0.08  # Still higher for unhoused but not as extreme
                if household.satisfaction < 0.2:  # More extreme dissatisfaction threshold
                    leave_chance += 0.04
                
                # Age-based factors
                if household.age > 75:
                    leave_chance += 0.05  # Reduced from 0.1
                
                if random.random() < leave_chance:
                    # If leaving, properly handle their current housing
                    if household.housed:
                        if household.contract and household.contract.unit:
                            household.contract.unit.remove_tenant(household)
                    households_to_remove.append(household)
                    actions_this_step += 1

        # 2. Household breakups - only for housed households with multiple people
        for household in self.households:
            if (household not in households_to_remove and 
                household.size > 1 and 
                household.housed and 
                household.contract and 
                household.contract.unit and
                household.contract.unit.occupied and
                household.contract.unit.get_total_household_size() > 1):  # Only households with people can break up
                
                breakup_chance = 0.04  # Base 4% chance per period
                
                # Moderate chance increases
                if household.satisfaction < 0.3:
                    breakup_chance += 0.05
                if household.current_rent_burden() > 0.6:
                    breakup_chance += 0.06
                if household.size > 3:
                    breakup_chance += 0.03
                
                # Merged households are more likely to break up
                if getattr(household, 'is_merged', False):
                    breakup_chance += getattr(household, 'merge_instability', 0.3)
                
                if random.random() < breakup_chance:
                    # Split into two households - one stays, one leaves
                    original_size = household.size
                    new_size = max(1, household.size // 2)
                    remaining_size = household.size - new_size
                    
                    # Ensure both resulting households have at least 1 person
                    if new_size > 0 and remaining_size > 0 and new_size >= 1 and remaining_size >= 1:
                        # Create new household that will leave
                        new_hh = self._create_new_household()
                        new_hh.size = new_size
                        new_hh.wealth = household.wealth * 0.4
                        new_hh.income = household.income * 0.6
                        
                        # Update original household size and resources
                        household.size = remaining_size
                        household.wealth *= 0.6
                        household.income *= 0.8  # Some income loss due to breakup
                        
                        # New household becomes unhoused
                        new_hh.housed = False
                        new_hh.contract = None
                        new_households.append(new_hh)
                        actions_this_step += 1
                        
                        # Record the breakup with proper details
                        if household.contract and household.contract.unit:
                            household.record_breakup_event(new_hh, year, period)
                            # Also log the breakup in movement logs
                            household.add_event({
                                "type": "HOUSEHOLD_BREAKUP_DETAILED",
                                "unit_id": household.contract.unit.id,
                                "original_size": original_size,
                                "remaining_size": remaining_size,
                                "departed_size": new_size,
                                "departed_household_id": new_hh.id
                            }, year, period)

        # 3. Household mergers and sharing
        # Only include households with actual people (size > 0) and valid contracts
        unhoused_households = [h for h in self.households 
                              if not h.housed and h not in households_to_remove and h.size > 0]
        housed_households = [h for h in self.households 
                            if (h.housed and h not in households_to_remove and h.size > 0 and 
                                h.contract and h.contract.unit and h.contract.unit.occupied)]
        
        # A) Real household mergers (two households become one)
        merger_attempts = 0
        for unhoused_hh in unhoused_households[:2]:  # Limit attempts
            if merger_attempts >= 1:  # Max 1 merger per step
                break
            for housed_hh in housed_households:
                if (housed_hh.contract and housed_hh.contract.unit and 
                    housed_hh.contract.unit.occupied and
                    housed_hh.contract.unit.get_total_household_size() > 0 and  # Unit must have people
                    len(housed_hh.contract.unit.tenants) == 1 and  # Only merge with single households
                    housed_hh.size > 0 and unhoused_hh.size > 0 and  # Both must have people
                    abs(housed_hh.age - unhoused_hh.age) < 20 and
                    housed_hh.life_stage == unhoused_hh.life_stage and
                    random.random() < 0.15):  # Lower chance for true merger
                    
                    # True household merger - combine households into one
                    unit = housed_hh.contract.unit
                    
                    # Store original details for logging
                    original_housed_size = housed_hh.size
                    original_unhoused_size = unhoused_hh.size
                    unhoused_hh_id = unhoused_hh.id
                    
                    # Combine household characteristics
                    combined_size = housed_hh.size + unhoused_hh.size
                    
                    # Prevent overly large households (max 6 people)
                    if combined_size > 6:
                        continue
                        
                    combined_income = housed_hh.income + unhoused_hh.income * 0.8  # Slight efficiency loss
                    combined_wealth = housed_hh.wealth + unhoused_hh.wealth
                    combined_age = (housed_hh.age + unhoused_hh.age) / 2
                    
                    # Update the housed household with combined stats
                    housed_hh.size = combined_size
                    housed_hh.income = combined_income
                    housed_hh.wealth = combined_wealth
                    housed_hh.age = combined_age
                    
                    # Mark household as merged (more likely to split later)
                    housed_hh.is_merged = True
                    housed_hh.merge_instability = random.uniform(0.3, 0.6)  # Instability factor
                    
                    # Record the merger with detailed information
                    housed_hh.record_merger_event(unhoused_hh, year, period)
                    housed_hh.add_event({
                        "type": "HOUSEHOLD_MERGER_DETAILED",
                        "unit_id": unit.id,
                        "merged_household_a_id": housed_hh.id,
                        "merged_household_b_id": unhoused_hh_id,
                        "household_a_original_size": original_housed_size,
                        "household_b_original_size": original_unhoused_size,
                        "combined_size": combined_size
                    }, year, period)
                    
                    # Remove the unhoused household (it's now part of the housed one)
                    households_to_remove.append(unhoused_hh)
                    actions_this_step += 1
                    merger_attempts += 1
                    break
        
        # B) Apartment sharing (households share space but remain separate)
        for unhoused_hh in unhoused_households[:3]:
            if unhoused_hh in households_to_remove or unhoused_hh.size == 0:
                continue
            for housed_hh in housed_households:
                if (housed_hh.contract and housed_hh.contract.unit and 
                    housed_hh.contract.unit.occupied and
                    housed_hh.contract.unit.get_total_household_size() > 0 and  # Unit must have people
                    housed_hh.size > 0 and  # Housed household must have people
                    len(housed_hh.contract.unit.tenants) == 1 and
                    abs(housed_hh.age - unhoused_hh.age) < 15 and
                    random.random() < 0.20):  # Sharing is more common than merging
                    
                    unit = housed_hh.contract.unit
                    unit.add_tenant(unhoused_hh)
                    unhoused_hh.contract = Contract(unhoused_hh, unit)
                    unhoused_hh.housed = True
                    unhoused_hh.calculate_satisfaction()
                    
                    # Log the sharing arrangement
                    unhoused_hh.add_event({
                        "type": "APARTMENT_SHARING",
                        "unit_id": unit.id,
                        "sharing_with_household_id": housed_hh.id,
                        "own_size": unhoused_hh.size,
                        "roommate_size": housed_hh.size
                    }, year, period)
                    
                    actions_this_step += 1
                    break

        # 4. New household arrivals - scaled for smaller simulation (max 2 per step)
        current_population = len(self.households) - len(households_to_remove) + len(new_households)
        target_population = 20  # Scaled down target
        
        # Dynamic arrival rate based on current population
        population_deficit = max(0, target_population - current_population)
        base_arrival_rate = 0.15  # Lower base rate for smaller simulation
        arrival_rate = base_arrival_rate + (population_deficit * 0.02)  # Increases with deficit
        
        # Add new households but limit to max 2 per step
        arrivals_this_step = 0
        max_arrivals_per_step = 2
        
        while (current_population < target_population and 
               arrivals_this_step < max_arrivals_per_step and 
               random.random() < arrival_rate):
            new_household = self._create_new_household()
            new_household.housed = False
            new_households.append(new_household)
            actions_this_step += 1
            current_population += 1
            arrivals_this_step += 1

        # Remove departing households
        for household in households_to_remove:
            if household in self.households:
                self.households.remove(household)

        # Add new households
        self.households.extend(new_households)
        
        return actions_this_step

    def step(self, year, period):
        # Track total actions for this step
        total_actions = 0
        

        # Process population changes first to capture the effects of breakups/mergers
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
            
            # Check for potential eviction due to high rent burden - more realistic risk
            if (household.housed and 
                household.contract is not None):
                
                rent_burden = household.current_rent_burden()
                # Moderate eviction risk
                if rent_burden > 0.6:  # Lowered threshold for more evictions
                    eviction_risk = (rent_burden - 0.6) * 2.0  # Increased multiplier
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
            
            # Additional causes of becoming unhoused
            if (household.housed and random.random() < 0.01):  # 1% chance of life events
                life_event_reasons = ["Job loss", "Family emergency", "Health issues", "Relationship breakdown"]
                reason = random.choice(life_event_reasons)
                if household.contract:
                    household.contract.unit.remove_tenant(household)
                    household.contract = None
                household.housed = False
                household.satisfaction = 0
                household.wealth = max(0, household.wealth - random.randint(1000, 5000))  # Financial impact
                household.add_event({
                    "type": "EVICTED",
                    "reason": reason,
                    "rent_burden": household.current_rent_burden()
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
                # Use dynamic property value calculation
                property_value = self._calculate_property_value(unit, year, period)
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

        # Validate and fix data consistency before recording
        fixes_made = self._validate_and_fix_household_unit_consistency()
        
        # Run final validation check
        integrity_errors = self.validate_data_integrity()
        if integrity_errors:
            print(f"Year {year} Period {period}: {len(integrity_errors)} remaining data integrity issues:")
            for error in integrity_errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(integrity_errors) > 5:
                print(f"  ... and {len(integrity_errors) - 5} more")
        
        # Record occupancy AFTER all movements and changes are complete
        self._record_occupancy_state()
        
        # Record metrics including action count
        self._record_detailed_metrics(year, period)
        self._record_basic_metrics(year, period, total_actions)


        
        # Record detailed unit history for dashboard
        for unit in self.rental_market.units:
            # Get tenant information
            tenant_info = None
            if unit.occupied and unit.tenant:
                tenant_info = {
                    'id': unit.tenant.id,
                    'size': unit.tenant.size,
                    'income': unit.tenant.income,
                    'wealth': unit.tenant.wealth,
                    'satisfaction': getattr(unit.tenant, 'satisfaction', 0),
                    'life_stage': getattr(unit.tenant, 'life_stage', 'unknown'),
                    'rent_burden': unit.tenant.current_rent_burden() if hasattr(unit.tenant, 'current_rent_burden') else 0
                }
            
            # Calculate dynamic property value based on current conditions
            property_value = self._calculate_property_value(unit, year, period)
            
            # Record unit state for this period
            unit_period_data = {
                'year': year,
                'period': period,
                'rent': unit.rent,
                'quality': unit.quality,
                'property_value': property_value,
                'occupied': unit.occupied,
                'tenant_info': tenant_info,
                'vacancy_duration': getattr(unit, 'vacancy_duration', 0),
                'last_renovation': getattr(unit, 'last_renovation', 0)
            }
            self.unit_history[unit.id].append(unit_period_data)

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
