# models/household.py
import collections
import random
import numpy as np

TimeLineEntry = collections.namedtuple('TimeLineEntry', ('year', 'month', 'record'))

def new_timeline_entry(info, year, month):
    return TimeLineEntry(year, month, info)

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

    def update_month(self, year, month):
        # Age increment is now more realistic (1/12 per month)
        self.age += 1/12
        # Income adjustment
        self.adjust_income()
        # Wealth adjustment (always called)
        self.adjust_wealth()
        # Update contract and satisfaction
        if self.is_owner_occupier:
            self.process_mortgage_month()
            if hasattr(self, 'mortgage_balance') and self.mortgage_balance > 0:
                if hasattr(self, 'owned_unit') and self.owned_unit is not None:
                    self.calculate_satisfaction_owner()
            self.months_in_current_unit += 1
        elif self.contract:
            self.contract.update()
            self.months_in_current_unit += 1
            self.calculate_satisfaction()
        # Life stage transition
        self._update_life_stage()
        # Add timeline entry
        self.add_event({
            "type": "MONTHLY_UPDATE",
            "age": self.age,
            "life_stage": self.life_stage,
            "income": self.income,
            "wealth": self.wealth,
            "satisfaction": self.satisfaction
        }, year, month)

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

    def consider_moving(self, market, policy, year, month):
        if self.is_owner_occupier:
            return  # Owner-occupiers do not move in this logic
        if not self.housed:
            self._search_for_housing(market, policy, year, month)
            return

        base_move_chance = 1 - self.satisfaction
        time_factor = min(1, self.months_in_current_unit / 24)  # Less likely to move if recently moved
        life_stage_factor = {
            "young_adult": 1.2,
            "family_formation": 1.1,
            "established": 0.8,
            "retirement": 0.6
        }[self.life_stage]

        move_chance = base_move_chance * self.mobility_preference * (1 - time_factor) * life_stage_factor

        if random.random() < move_chance:
            self._search_for_housing(market, policy, year, month)

    def _search_for_housing(self, market, policy, year, month):
        self.search_duration += 1
        if self.search_duration > self.max_search_duration:
            self._accept_compromise_housing(market, policy, year, month)
            return

        def calculate_unit_score(unit):
            # Base score components
            quality_score = unit.quality * self.quality_preference
            size_match = 1 - abs(self.size - unit.size) / max(self.size, unit.size)
            location_score = getattr(unit, 'location_score', 0.5) * self.location_preference
            affordability = 1 - (unit.rent / self.income) * self.cost_sensitivity
            
            # Calculate base score
            base_score = (
                quality_score * 0.3 +
                size_match * 0.25 +
                location_score * 0.25 +
                affordability * 0.2
            )
            
            # Apply penalties and bonuses
            if unit.occupied:
                # Significant penalty for displacing others
                base_score *= 0.7
                # Extra penalty if the current tenant is satisfied
                if unit.tenant and unit.tenant.satisfaction > 0.7:
                    base_score *= 0.8
            else:
                # Bonus for vacant units to encourage filling vacancies
                base_score *= 1.2
                
            # Small random factor to prevent identical scores
            base_score += random.uniform(-0.05, 0.05)
            
            return base_score

        # Get all potential units that meet basic criteria
        potential_units = []
        for unit in market.units:
            # Skip if unit is owner-occupied
            if getattr(unit, 'is_owner_occupied', False):
                continue
                
            # Skip if rent is clearly unaffordable
            if unit.rent > 0.5 * self.income:
                continue
                
            # Skip if it's our current unit
            if self.contract and unit == self.contract.unit:
                continue
                
            # Calculate score and add to potential units
            score = calculate_unit_score(unit)
            potential_units.append((unit, score))
        
        # Sort units by score
        potential_units.sort(key=lambda x: x[1], reverse=True)
        
        # Try to find a suitable unit
        for unit, score in potential_units[:5]:  # Consider top 5 options
            if score > 0.6:  # Only accept if score is good enough
                if unit.occupied:
                    current_tenant = unit.tenant
                    # Only displace if it would significantly improve our situation
                    if score > current_tenant.satisfaction * 1.2:
                        # Save current tenant info for displacement
                        current_tenant.contract.unit.vacate()
                        current_tenant.contract = None
                        current_tenant.housed = False
                        current_tenant.satisfaction = 0
                        # Move to the unit
                        self.move_to(unit, year, month)
                        # Force displaced tenant to look for new housing
                        current_tenant._search_for_housing(market, policy, year, month)
                        self.search_duration = 0
                        return
                else:
                    # If unit is vacant, just move in
                    self.move_to(unit, year, month)
                    self.search_duration = 0
                    return

    def _accept_compromise_housing(self, market, policy, year, month):
        # Find the best available unit that meets minimum requirements
        acceptable_unit = market.find_acceptable_unit(
            self.income,
            min_quality=0.5,
            min_size=max(1, self.size - 1)
        )
        if acceptable_unit:
            self.move_to(acceptable_unit, year, month)
            self.search_duration = 0

    def move_to(self, unit, year, month):
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
        
        self.add_event(event_data, year, month)

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

    def add_event(self, info, year, month):
        self.timeline.append(new_timeline_entry(info, year, month))

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

class Contract:
    def __init__(self, tenant, unit):
        self.tenant = tenant
        self.unit = unit
        self.months = 0
        self.start_date = None  # Could be used for lease terms

    def update(self):
        self.months += 1
