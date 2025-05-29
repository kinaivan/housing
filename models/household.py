# models/household.py
import collections
import random
import numpy as np

TimeLineEntry = collections.namedtuple('TimeLineEntry', ('year', 'period', 'record'))

def new_timeline_entry(info, year, period):
    return TimeLineEntry(year, period, info)

class Contract:
    def __init__(self, tenant, unit):
        self.tenant = tenant
        self.unit = unit
        self.months = 0
        self.start_date = None  # Could be used for lease terms

    def update(self):
        self.months += 1

class Household:
    def __init__(self, id, age, size, income, wealth, contract=None, is_owner_occupier=False, mortgage_balance=0, mortgage_interest_rate=0.03, mortgage_term=30):
        self.id = id
        self.age = age
        self.size = size
        self.income = income
        self.wealth = wealth
        self.contract = contract
        self.housed = contract is not None
        self.timeline = []
        self.satisfaction = 0
        self.months_in_current_unit = 0
        self.search_history = []

        # Enhanced behavioral attributes
        self.mobility_preference = random.uniform(0, 1)
        self.quality_preference = random.uniform(0, 1)
        self.cost_sensitivity = random.uniform(0.2, 0.5)
        self.location_preference = random.uniform(0, 1)  # Preference for central vs suburban
        self.size_preference = max(1, min(4, size + random.randint(-1, 1)))  # Preferred household size
        self.amenity_preference = random.uniform(0, 1)  # Preference for additional amenities
        self.risk_aversion = random.uniform(0, 1)  # How risk-averse the household is
        self.search_patience = random.uniform(0, 1)  # How long they'll search for ideal housing

        # Life cycle stage (affects preferences)
        self.life_stage = self._determine_life_stage()
        
        # Search parameters
        self.search_duration = 0
        self.max_search_duration = int(12 * (1 - self.search_patience))  # Max months to search

        # Mortgage attributes
        self.is_owner_occupier = is_owner_occupier
        self.mortgage_balance = mortgage_balance
        self.mortgage_interest_rate = mortgage_interest_rate
        self.mortgage_term = mortgage_term  # in years
        self.mortgage_interest_paid = 0
        self.monthly_payment = 0
        if self.is_owner_occupier and self.mortgage_balance > 0:
            r = self.mortgage_interest_rate / 12
            n = self.mortgage_term * 12
            self.monthly_payment = (self.mortgage_balance * r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def _determine_life_stage(self):
        if self.age < 25:
            return "young_adult"
        elif self.age < 35:
            return "family_formation"
        elif self.age < 55:
            return "established"
        else:
            return "retirement"

    def current_rent_burden(self):
        if self.is_owner_occupier:
            # For owner-occupiers, use mortgage payment as housing cost
            if hasattr(self, 'monthly_payment') and self.income > 0:
                return self.monthly_payment / self.income
            return 0
        elif self.contract and self.income > 0:
            return self.contract.unit.rent / self.income
        return 0  # Return 0 instead of None for unhoused households

    def update_month(self, year, period):
        # Age increment for 6-month period
        self.age += 0.5
        
        # Income and wealth adjustments for 6-month period
        self.adjust_income()
        self.adjust_wealth()
        
        # Update contract and satisfaction
        if self.is_owner_occupier:
            # Process 6 months of mortgage payments
            for _ in range(6):
                self.process_mortgage_month()
            if hasattr(self, 'mortgage_balance') and self.mortgage_balance > 0:
                if hasattr(self, 'owned_unit') and self.owned_unit is not None:
                    self.calculate_satisfaction_owner()
            self.months_in_current_unit += 6
        elif self.contract:
            # Update contract for 6 months
            for _ in range(6):
                self.contract.update()
            self.months_in_current_unit += 6
            self.calculate_satisfaction()
            
        # Life stage transition
        self._update_life_stage()
        
        # Add timeline entry
        self.add_event({
            "type": "PERIOD_UPDATE",
            "age": self.age,
            "life_stage": self.life_stage,
            "income": self.income,
            "wealth": self.wealth,
            "satisfaction": self.satisfaction
        }, year, period)

    def _update_life_stage(self):
        new_stage = self._determine_life_stage()
        if new_stage != self.life_stage:
            old_stage = self.life_stage
            self.life_stage = new_stage
            self._adjust_preferences_for_life_stage()
            
            # Add life stage transition event
            self.add_event({
                "type": "LIFE_STAGE_TRANSITION",
                "old_stage": old_stage,
                "new_stage": new_stage,
                "age": self.age
            }, None, None)

    def _adjust_preferences_for_life_stage(self):
        if self.life_stage == "young_adult":
            self.quality_preference *= 0.8  # Less emphasis on quality
            self.location_preference *= 1.2  # More emphasis on location
            self.mobility_preference *= 1.2  # More likely to move
            self.cost_sensitivity *= 1.1  # More sensitive to costs
        elif self.life_stage == "family_formation":
            self.size_preference = max(self.size_preference, 2)
            self.quality_preference *= 1.2
            self.location_preference *= 0.9
            self.mobility_preference *= 0.8  
            self.cost_sensitivity *= 0.9
        elif self.life_stage == "established":
            self.quality_preference *= 1.3
            self.cost_sensitivity *= 0.8
            self.mobility_preference *= 0.7  
            self.location_preference *= 0.8
        else:
            self.cost_sensitivity *= 1.2
            self.mobility_preference *= 0.6
            self.quality_preference *= 1.1
            self.location_preference *= 0.7 

    def adjust_income(self):
        # More sophisticated income adjustment based on life stage
        base_drift = random.uniform(-0.02, 0.05)
        life_stage_multiplier = {
            "young_adult": 1.2,
            "family_formation": 1.1,
            "established": 1.0,
            "retirement": 0.8
        }
        drift = base_drift * life_stage_multiplier[self.life_stage]
        self.income = max(500, self.income * (1 + drift))

    def adjust_wealth(self):
        # More sophisticated wealth accumulation
        base_saving_rate = 0.1
        life_stage_multiplier = {
            "young_adult": 0.8,  # Lower savings
            "family_formation": 0.9,
            "established": 1.2,  # Higher savings
            "retirement": 1.0
        }
        saving_rate = base_saving_rate * life_stage_multiplier[self.life_stage]
        housing_cost = self.contract.unit.rent if self.contract else 0
        savings = max(0, self.income - housing_cost) * saving_rate
        self.wealth += savings

    def calculate_satisfaction(self):
        if not self.contract:
            self.satisfaction = 0
            return

        # Multi-factor satisfaction calculation
        rent_burden = self.contract.unit.rent / self.income
        quality_score = self.contract.unit.quality
        size_match = 1 - abs(self.size - self.contract.unit.size) / max(self.size, self.contract.unit.size)
        location_score = self.contract.unit.location_score if hasattr(self.contract.unit, 'location_score') else 0.5
        amenity_score = self.contract.unit.amenity_score if hasattr(self.contract.unit, 'amenity_score') else 0.5

        # Weighted satisfaction calculation
        weights = {
            'rent_burden': self.cost_sensitivity*10,
            'quality': self.quality_preference,
            'size': 0.3,
            'location': self.location_preference,
            'amenities': self.amenity_preference
        }

        satisfaction = (
            (1 - rent_burden) * weights['rent_burden'] +
            quality_score * weights['quality'] +
            size_match * weights['size'] +
            location_score * weights['location'] +
            amenity_score * weights['amenities']
        ) / sum(weights.values())

        self.satisfaction = max(0, min(1, satisfaction))

    def calculate_satisfaction_owner(self):
        # Owner-occupier satisfaction based on their owned unit
        unit = getattr(self, 'owned_unit', None)
        if not unit:
            self.satisfaction = 0
            return
        # Use similar logic as rental satisfaction, but no rent burden
        quality_score = unit.quality
        size_match = 1 - abs(self.size - unit.size) / max(self.size, unit.size)
        location_score = unit.location_score if hasattr(unit, 'location_score') else 0.5
        amenity_score = unit.amenity_score if hasattr(unit, 'amenity_score') else 0.5
        weights = {
            'quality': self.quality_preference,
            'size': 0.3,
            'location': self.location_preference,
            'amenities': self.amenity_preference
        }
        satisfaction = (
            quality_score * weights['quality'] +
            size_match * weights['size'] +
            location_score * weights['location'] +
            amenity_score * weights['amenities']
        ) / sum(weights.values())
        self.satisfaction = max(0, min(1, satisfaction))

    def consider_moving(self, market, policy, year, period):
        # If not housed, always try to find housing
        if not self.housed:
            self._search_for_housing(market, policy, year, period)
            return

        # Much higher base move chance for dynamic behavior
        base_move_chance = 0.2  # 20% base chance per period (increased from 5%)
        
        # Satisfaction-based adjustments
        satisfaction_factor = (1 - self.satisfaction) * 0.3
        base_move_chance += satisfaction_factor
        
        # Rent burden adjustments - very sensitive to high costs
        rent_burden = self.current_rent_burden()
        if rent_burden > 0.3:
            base_move_chance += (rent_burden - 0.3) * 0.8  # Strong incentive to move
        
        # Opportunity-based movement - look for better deals
        vacant_units = [u for u in market.units if not u.occupied and not getattr(u, 'is_owner_occupied', False)]
        if vacant_units:
            # Check if there are significantly cheaper options
            current_rent = self.contract.unit.rent if self.contract else float('inf')
            cheapest_vacant = min(unit.rent for unit in vacant_units)
            if cheapest_vacant < current_rent * 0.8:  # 20% cheaper
                base_move_chance += 0.3  # Strong incentive to move for savings
        
        # Time-based adjustments - less stability, more movement
        time_factor = min(1, self.months_in_current_unit / 12)
        base_move_chance *= (1 - time_factor * 0.3)  # Slight reduction for tenure
        
        # Life stage adjustments - young people move more
        life_stage_multipliers = {
            "young_adult": 1.5,
            "family_formation": 1.2,
            "established": 1.0,
            "retirement": 0.7
        }
        base_move_chance *= life_stage_multipliers.get(self.life_stage, 1.0)
        
        # Market condition adjustments
        vacancy_rate = market.market_conditions['vacancy_rate']
        if vacancy_rate > 0.05:  # Easier to move when more options
            base_move_chance *= 1.4
        
        # Random life events (job change, relationship, etc.)
        if random.random() < 0.05:  # 5% chance of major life event
            base_move_chance += 0.4
        
        # Cap the final move chance
        move_chance = min(0.7, base_move_chance)  # Maximum 70% chance per period
        
        if random.random() < move_chance:
            self._search_for_housing(market, policy, year, period)

    def _search_for_housing(self, market, policy, year, period):
        self.search_duration += 1
        
        # Much more aggressive search behavior
        desperation_factor = min(2.0, 1 + (self.search_duration / 6) * 0.8)
        
        def calculate_unit_score(unit):
            # Skip if clearly unaffordable (more lenient threshold)
            max_affordable = self.income * 0.6 * desperation_factor  # Increased from 0.5
            if unit.rent > max_affordable:
                return -1
                
            # Base score components
            quality_score = unit.quality * self.quality_preference
            size_match = 1 - abs(self.size - unit.size) / max(self.size, unit.size)
            location_score = getattr(unit, 'location_score', 0.5) * self.location_preference
            
            # Much stronger affordability preference - prioritize cheaper units
            affordability = max(0, 1 - (unit.rent / self.income) / 0.5)  # Strong preference for affordable
            
            # Big bonus for vacant units
            vacancy_bonus = 0.5 if not unit.occupied else 0
            
            # Calculate base score with higher weight on affordability and vacancy
            base_score = (
                quality_score * 0.2 +
                size_match * 0.2 +
                location_score * 0.15 +
                affordability * 0.35 +  # Higher weight on affordability
                vacancy_bonus * 0.1     # Bonus for vacant units
            )
            
            # Strong bonuses for vacant units
            if not unit.occupied:
                base_score *= 1.8  # Big preference for vacant units
            else:
                # Penalty for displacing others, but less than before
                displacement_penalty = 0.2
                base_score *= (1 - displacement_penalty)
                
                # Check if current tenant might leave anyway
                if unit.tenant and unit.tenant.satisfaction < 0.4:
                    base_score *= 1.3  # Bonus if current tenant is dissatisfied
            
            # Apply desperation factor more aggressively
            base_score *= desperation_factor
            
            # Random factor to prevent identical scores
            base_score += random.uniform(-0.02, 0.02)
            
            return base_score

        # Get all potential units
        potential_units = []
        for unit in market.units:
            # Skip if unit is owner-occupied
            if getattr(unit, 'is_owner_occupied', False):
                continue
                
            # Calculate score and add to potential units
            score = calculate_unit_score(unit)
            if score > 0:  # Only consider positive scores
                potential_units.append((unit, score))
        
        # Sort units by score
        potential_units.sort(key=lambda x: x[1], reverse=True)
        
        # Try to find a suitable unit - much more lenient acceptance
        for unit, score in potential_units[:8]:  # Consider top 8 options
            # Much lower threshold for acceptance
            min_score = 0.3 / desperation_factor
            
            if score > min_score:
                if unit.occupied:
                    # Be more aggressive about displacing current tenants
                    current_tenant = unit.tenant
                    if current_tenant:
                        # Only displace if we have higher score or they're dissatisfied
                        if (score > 0.6 or 
                            current_tenant.satisfaction < 0.5 or
                            self.search_duration > 3):
                            
                            # Move current tenant out
                            unit.remove_tenant(current_tenant)
                            current_tenant.contract = None
                            current_tenant.housed = False
                            current_tenant.satisfaction = 0
                            current_tenant.search_duration = 0
                            
                            # Move to the unit
                            self.move_to(unit, year, period)
                            self.search_duration = 0
                            return
                else:
                    # If unit is vacant, definitely move in
                    self.move_to(unit, year, period)
                    self.search_duration = 0
                    return
        
        # If still searching and desperate, consider sharing
        if self.search_duration > 2:
            # Look for units with only one household that could accommodate sharing
            for unit in market.units:
                if (unit.occupied and len(unit.tenants) == 1 and 
                    not getattr(unit, 'is_owner_occupied', False) and
                    unit.get_total_household_size() + self.size <= 6):  # Don't overcrowd
                    
                    if random.random() < 0.3:  # 30% chance to share when desperate
                        unit.add_tenant(self)
                        self.contract = Contract(self, unit)
                        self.housed = True
                        self.calculate_satisfaction()
                        self.search_duration = 0
                        return

    def _accept_compromise_housing(self, market, policy, year, period):
        # Find the best available unit that meets minimum requirements
        acceptable_unit = market.find_acceptable_unit(
            self.income,
            min_quality=0.5,
            min_size=max(1, self.size - 1)
        )
        if acceptable_unit:
            self.move_to(acceptable_unit, year, period)
            self.search_duration = 0

    def move_to(self, unit, year, period):
        # Store previous unit info before vacating
        previous_unit_id = None
        if self.contract:
            previous_unit_id = self.contract.unit.id
            self.contract.unit.vacate()
            
        unit.assign(self)
        self.contract = Contract(self, unit)
        self.housed = True
        self.months_in_current_unit = 0
        self.calculate_satisfaction()

        # Determine the primary reason for moving
        move_reason = self._determine_move_reason(unit)

        # Create movement event with source unit information
        event_data = {
            "type": "MOVED_IN",
            "unit_id": unit.id,
            "rent": unit.rent,
            "move_reason": move_reason,
            "from_unit_id": previous_unit_id,  # Add source unit tracking
            "is_house_to_house": previous_unit_id is not None  # Flag for house-to-house moves
        }
        
        self.add_event(event_data, year, period)

    def _determine_move_reason(self, new_unit):
        if not self.housed:
            return "Unhoused - First Move"

        old_unit = self.contract.unit if self.contract else None
        if old_unit:
            # Calculate improvements with proper normalization
            old_rent_burden = old_unit.rent / self.income
            new_rent_burden = new_unit.rent / self.income
            
            # Normalize all improvements to a -1 to 1 scale
            rent_improvement = (old_rent_burden - new_rent_burden) / max(old_rent_burden, new_rent_burden)
            quality_improvement = (new_unit.quality - old_unit.quality) / max(old_unit.quality, new_unit.quality)
            size_diff_old = abs(self.size - old_unit.size) / max(self.size, old_unit.size)
            size_diff_new = abs(self.size - new_unit.size) / max(self.size, new_unit.size)
            size_improvement = (size_diff_old - size_diff_new) / max(size_diff_old, size_diff_new) if (size_diff_old or size_diff_new) else 0
            
            old_loc = getattr(old_unit, 'location_score', 0.5)
            new_loc = getattr(new_unit, 'location_score', 0.5)
            location_improvement = (new_loc - old_loc) / max(old_loc, new_loc)

            # Weight the improvements based on household preferences
            weighted_improvements = {
                "Affordability": rent_improvement * self.cost_sensitivity,
                "Quality": quality_improvement * self.quality_preference,
                "Size": size_improvement * (1 - abs(self.size - self.size_preference) / max(self.size, self.size_preference)),
                "Location": location_improvement * self.location_preference
            }

            # Add some randomization to avoid always picking the same reason
            for reason in weighted_improvements:
                weighted_improvements[reason] += random.uniform(-0.1, 0.1)

            # Pick the most significant improvement
            best_reason, best_value = max(weighted_improvements.items(), key=lambda x: x[1])
            
            # Only return "Better X" if the improvement is significant
            return f"Better {best_reason}"

        return "Initial Housing"

    def end_month(self):
        if self.contract:
            self.contract.update()

    def add_event(self, info, year, period):
        self.timeline.append(new_timeline_entry(info, year, period))

    def process_mortgage_month(self):
        if self.is_owner_occupier and self.mortgage_balance > 0:
            r = self.mortgage_interest_rate / 12
            interest = self.mortgage_balance * r
            principal = self.monthly_payment - interest
            self.mortgage_balance = max(0, self.mortgage_balance - principal)
            self.wealth -= self.monthly_payment
            self.mortgage_interest_paid += interest
            # Dutch-style: interest is tax-deductible (simulate as income boost)
            self.income += interest  # crude, but for visualization

    def buy_home(self, unit):
        # Remove from rental if currently renting
        if self.contract:
            self.contract.unit.vacate()
            self.contract = None
        # Pay down payment, set up mortgage
        property_value = unit.base_rent * 12 * 20
        down_payment = 0.2 * property_value
        mortgage_balance = 0.8 * property_value
        self.wealth -= down_payment
        self.is_owner_occupier = True
        self.mortgage_balance = mortgage_balance
        self.mortgage_interest_rate = 0.03
        self.mortgage_term = 30
        r = self.mortgage_interest_rate / 12
        n = self.mortgage_term * 12
        self.monthly_payment = (mortgage_balance * r * (1 + r) ** n) / ((1 + r) ** n - 1)
        self.housed = True
        self.owned_unit = unit
        unit.assign_owner(self)

    def sell_home(self):
        unit = getattr(self, 'owned_unit', None)
        if unit is not None:
            property_value = unit.base_rent * 12 * 20
            equity = max(0, property_value - getattr(self, 'mortgage_balance', 0))
            self.wealth += equity
            self.mortgage_balance = 0
            self.monthly_payment = 0
            self.is_owner_occupier = False
            self.owned_unit = None
            unit.remove_owner()
            self.housed = False
            self.contract = None

    def record_breakup_event(self, new_household, year, period):
        if self.contract:
            unit_id = self.contract.unit.id
            self.add_event({
                "type": "HOUSEHOLD_BREAKUP",
                "unit_id": unit_id,
                "original_size": self.size + new_household.size,
                "new_size": self.size,
                "new_household_id": new_household.id
            }, year, period)

    def record_merger_event(self, other_household, year, period):
        if self.contract:
            unit_id = self.contract.unit.id
            self.add_event({
                "type": "HOUSEHOLD_MERGER",
                "unit_id": unit_id,
                "original_size": self.size,
                "merged_size": self.size + other_household.size,
                "merged_with_id": other_household.id
            }, year, period)
