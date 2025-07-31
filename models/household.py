# models/household.py
import collections
import random
import numpy as np
from .dutch_names import generate_dutch_name

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
        self.name = generate_dutch_name()  # Generate a Dutch name for the household
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
        
        # Merger tracking
        self.is_merged = False
        self.merge_instability = 0.0  # Higher values increase breakup chance

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
        
        # Track wealth trend
        self.wealth_history = getattr(self, 'wealth_history', [])
        self.wealth_history.append(self.wealth)
        # Keep last 4 periods (2 years) of history
        if len(self.wealth_history) > 4:
            self.wealth_history = self.wealth_history[-4:]
        
        # Calculate wealth trend
        self.wealth_trend = 0
        if len(self.wealth_history) >= 2:
            initial_wealth = self.wealth_history[0]
            current_wealth = self.wealth_history[-1]
            if initial_wealth != 0:
                self.wealth_trend = (current_wealth - initial_wealth) / initial_wealth
            else:
                # If initial wealth was 0, calculate trend based on absolute change
                self.wealth_trend = current_wealth / 1000 if current_wealth > 0 else 0
        
        # Income and wealth adjustments for 6-month period
        self.adjust_income()
        self.adjust_wealth()
        
        # Check if we need to find cheaper housing
        if self.contract and not self.is_owner_occupier:
            current_rent = self.contract.unit.rent
            monthly_income = self.income / 12
            rent_burden = current_rent / monthly_income if monthly_income > 0 else float('inf')
            
            # Factors that might force a move
            wealth_depleting = self.wealth_trend < -0.2  # Significant wealth decrease
            high_rent_burden = rent_burden > 0.5  # Spending more than 50% on rent
            low_savings = self.wealth < current_rent * 6  # Less than 6 months of rent in savings
            
            if (wealth_depleting and high_rent_burden) or low_savings:
                self.needs_cheaper_housing = True
                self.add_event({
                    "type": "FINANCIAL_STRESS",
                    "rent_burden": rent_burden,
                    "wealth_trend": self.wealth_trend,
                    "savings_months": self.wealth / current_rent if current_rent > 0 else 0
                }, year, period)
        
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
            "satisfaction": self.satisfaction,
            "wealth_trend": self.wealth_trend
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
        
        # Size satisfaction accounts for total household size in unit
        total_household_size = self.contract.unit.get_total_household_size()
        size_match = 1 - abs(total_household_size - self.contract.unit.size) / max(total_household_size, self.contract.unit.size)
        
        # Location and amenity scores
        location_score = self.contract.unit.location_score if hasattr(self.contract.unit, 'location_score') else 0.5
        amenity_score = self.contract.unit.amenity_score if hasattr(self.contract.unit, 'amenity_score') else 0.5

        # Sharing penalty - reduces satisfaction if sharing with others
        sharing_penalty = 0
        if len(self.contract.unit.tenants) > 1:
            sharing_penalty = 0.1 * (len(self.contract.unit.tenants) - 1)  # 10% penalty per additional household

        # Weighted satisfaction calculation
        weights = {
            'rent_burden': self.cost_sensitivity * 10,
            'quality': self.quality_preference,
            'size': 1.0,
            'location': self.location_preference,
            'amenities': self.amenity_preference
        }

        # Calculate component scores
        scores = {
            'rent_burden': max(0, 1 - rent_burden),  # Higher score for lower burden
            'quality': quality_score,
            'size': size_match,
            'location': 1 - abs(self.location_preference - location_score),  # Match to preference
            'amenities': amenity_score
        }

        # Calculate weighted average
        total_weight = sum(weights.values())
        weighted_satisfaction = sum(scores[k] * weights[k] for k in weights.keys()) / total_weight

        # Apply sharing penalty
        weighted_satisfaction = max(0, weighted_satisfaction - sharing_penalty)

        self.satisfaction = weighted_satisfaction

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
        """Consider whether to move to a new unit"""
        # If not housed, try to find housing but with more limitations
        if not self.housed:
            # Only try to find housing if not too picky or desperate enough
            search_desperation = min(1.0, self.search_duration / 8.0)  # Becomes desperate over time
            search_threshold = 0.3 + (1 - self.search_patience) * 0.4  # Pickier households search less often
            
            if random.random() < search_threshold + search_desperation:
                # First try to find ideal housing
                new_unit = self._search_for_housing(market, policy, year, period)
                if new_unit:
                    self.move_to(new_unit, year, period)
                    return
                
                # If desperate (searching for a while), consider sharing
                if self.search_duration > 4:  # Increased threshold for sharing
                    # Look for units that could accommodate sharing
                    potential_shared_units = [
                        u for u in market.units 
                        if u.occupied and len(u.tenants) == 1 
                        and u.get_total_household_size() + self.size <= u.size * 1.3  # Reduced overcrowding tolerance
                    ]
                    
                    # Sort by compatibility
                    def sharing_compatibility(unit):
                        primary_tenant = unit.tenants[0]
                        age_diff = abs(self.age - primary_tenant.age)
                        stage_match = self.life_stage == primary_tenant.life_stage
                        effective_rent = unit.rent / 2  # Split rent
                        rent_burden = effective_rent / self.income
                        
                        score = 1.0
                        if age_diff > 15:
                            score *= 0.6  # Stricter age matching
                        if not stage_match:
                            score *= 0.6  # Stricter life stage matching
                        if rent_burden > 0.4:
                            score *= 0.5  # More rent burden sensitive
                        return score
                    
                    potential_shared_units.sort(key=sharing_compatibility, reverse=True)
                    
                    # Try to share with most compatible household (reduced chance)
                    if potential_shared_units:
                        share_chance = 0.2 * (1 + self.search_duration / 10)  # Reduced and slower increase
                        if random.random() < share_chance:
                            self.move_to(potential_shared_units[0], year, period)
                            return
            
            self.search_duration += 1
            return
            
        # If housed, consider moving based on satisfaction and other factors
        move_chance = 0.2  # Base 20% chance to consider moving
        
        # Adjust based on satisfaction
        if self.satisfaction < 0.3:
            move_chance += 0.3
        elif self.satisfaction < 0.5:
            move_chance += 0.15
            
        # Adjust based on rent burden
        rent_burden = self.current_rent_burden()
        if rent_burden > 0.5:
            move_chance += 0.2
        elif rent_burden > 0.4:
            move_chance += 0.1
            
        # Adjust based on household characteristics
        move_chance *= self.mobility_preference
        
        # Reduce moving if recently moved
        if self.months_in_current_unit < 6:
            move_chance *= 0.5
            
        # Consider moving
        if random.random() < move_chance:
            # Search for better housing
            new_unit = self._search_for_housing(market, policy, year, period)
            if new_unit:
                # Only move if new unit is significantly better
                current_satisfaction = self.satisfaction
                
                # Temporarily calculate satisfaction in new unit
                old_contract = self.contract
                self.contract = Contract(self, new_unit)
                self.calculate_satisfaction()
                potential_satisfaction = self.satisfaction
                self.contract = old_contract
                self.calculate_satisfaction()  # Restore original satisfaction
                
                # Move if new unit offers significant improvement
                if potential_satisfaction > current_satisfaction + 0.15:
                    self.move_to(new_unit, year, period)

    def _search_for_housing(self, market, policy, year, period):
        """Search for housing that meets household's preferences"""
        available_units = [u for u in market.units if not u.occupied or len(u.tenants) < 2]  # Allow up to 2 households per unit
        
        if not available_units:
            return None

        def calculate_unit_score(unit):
            # Skip if clearly unaffordable (more lenient threshold)
            if unit.rent > self.income * 0.8:  # 80% of income as max rent
                return -float('inf')
            
            # Calculate effective rent (full rent if sole tenant, half if sharing)
            effective_rent = unit.rent
            if unit.occupied and unit.tenants:  # If would be sharing
                effective_rent = unit.rent / 2
            
            # Skip if effective rent still too high
            if effective_rent > self.income * 0.5:  # 50% of income as max effective rent
                return -float('inf')
            
            # Calculate rent burden based on effective rent
            rent_burden = effective_rent / self.income
            
            # Calculate size match considering current occupants
            total_size = self.size
            if unit.occupied and unit.tenants:
                total_size += sum(t.size for t in unit.tenants)
            size_match = 1 - abs(total_size - unit.size) / max(total_size, unit.size)
            
            # Sharing penalty
            sharing_penalty = 0
            if unit.occupied and unit.tenants:
                sharing_penalty = 0.2  # 20% penalty for sharing
                
                # Additional penalties for mismatched characteristics
                primary_tenant = unit.tenants[0]
                age_diff = abs(self.age - primary_tenant.age)
                if age_diff > 15:  # Big age gap
                    sharing_penalty += 0.1
                if self.life_stage != primary_tenant.life_stage:  # Different life stages
                    sharing_penalty += 0.1
            
            # Base score calculation
            score = (
                (1 - rent_burden) * self.cost_sensitivity * 10 +
                unit.quality * self.quality_preference +
                size_match * 1.0 +
                (1 - abs(self.location_preference - unit.location)) * self.location_preference +
                unit.amenity_score * self.amenity_preference
            )
            
            # Apply sharing penalty
            score = score * (1 - sharing_penalty)
            
            # Vacancy bonus - empty units are slightly preferred
            if not unit.occupied:
                score *= 1.1
            
            return score

        # Sort units by score
        scored_units = [(u, calculate_unit_score(u)) for u in available_units]
        scored_units.sort(key=lambda x: x[1], reverse=True)
        
        # Return best unit if it meets minimum score threshold
        if scored_units and scored_units[0][1] > 0:
            return scored_units[0][0]
        
        return None

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
        """Move household to a new unit"""
        old_unit = self.contract.unit if self.contract else None
        old_unit_id = old_unit.id if old_unit else None
        
        # End current contract if exists
        if self.contract:
            old_unit = self.contract.unit
            old_unit.remove_tenant(self)
            self.contract = None
            
        # Create new contract
        self.contract = Contract(self, unit)
        unit.add_tenant(self)
        self.housed = True
        self.months_in_current_unit = 0
        
        # Record the move
        self.add_event({
            "type": "MOVED_IN",
            "unit_id": unit.id,
            "old_unit_id": old_unit_id,
            "rent": unit.rent,
            "quality": unit.quality
        }, year, period)

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

    def add_event(self, event_data, year, period):
        """Add an event to the household's timeline"""
        # Add common fields to all events
        event_data.update({
            "household_id": self.id,
            "household_name": self.name,
            "age": int(self.age),  # Ensure numeric values are basic types
            "size": int(self.size),
            "income": float(self.income),
            "wealth": float(self.wealth),
            "housed": bool(self.housed),
            "life_stage": str(self.life_stage)  # Ensure string values are basic types
        })
        
        # Ensure all values in event_data are JSON serializable
        for key, value in event_data.items():
            if isinstance(value, (int, float, str, bool, type(None))):
                continue
            elif isinstance(value, (list, tuple)):
                event_data[key] = list(value)  # Convert to list
            elif isinstance(value, dict):
                continue  # Assume nested dicts are handled
            else:
                # Convert any other types to string representation
                event_data[key] = str(value)
        
        self.timeline.append(TimeLineEntry(year, period, event_data))
        # Keep only the last 10 events to prevent memory bloat
        if len(self.timeline) > 10:
            self.timeline = self.timeline[-10:]

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

    def buy_home(self, unit, property_value=None):
        # Remove from rental if currently renting
        if self.contract:
            self.contract.unit.vacate()
            self.contract = None
        # Pay down payment, set up mortgage
        if property_value is None:
            property_value = unit.base_rent * 12 * 15  # More conservative fallback
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

    def sell_home(self, property_value=None):
        unit = getattr(self, 'owned_unit', None)
        if unit is not None:
            if property_value is None:
                property_value = unit.base_rent * 12 * 15  # More conservative fallback
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
        """Record a household breakup event"""
        if self.contract and self.contract.unit:
            self.add_event({
                "type": "HOUSEHOLD_BREAKUP",
                "unit_id": self.contract.unit.id,
                "original_size": self.size + new_household.size,
                "remaining_size": self.size,
                "new_household_id": new_household.id,
                "new_household_size": new_household.size
            }, year, period)

    def record_merger_event(self, other_household, year, period):
        """Record a household merger event"""
        if self.contract and self.contract.unit:
            self.add_event({
                "type": "HOUSEHOLD_MERGER",
                "unit_id": self.contract.unit.id,
                "original_size": self.size,
                "other_household_id": other_household.id,
                "other_household_size": other_household.size,
                "combined_size": self.size + other_household.size
            }, year, period)

    def should_move(self, market_conditions):
        """Determine if household should consider moving based on various factors."""
        # Don't move if just moved recently (within 6 months)
        if self.months_in_current_unit < 6:
            return False

        # Base move probability 5%
        base_move_probability = 0.05

        # Financial stress increases move probability
        if hasattr(self, 'wealth_trend') and self.wealth_trend < 0:
            # Consider moving if wealth is decreasing
            if self.wealth_trend < -0.1:  # 10% decrease in wealth
                base_move_probability += abs(self.wealth_trend) * 0.2

        # High rent burden increases move probability
        current_rent_burden = self.current_rent_burden() if self.housed else 0
        if current_rent_burden > 0.4:  # More than 40% of income on rent
            base_move_probability += (current_rent_burden - 0.4) * 0.3

        # Low satisfaction increases move probability
        if hasattr(self, 'satisfaction') and self.satisfaction < 0.5:  # Unsatisfied
            base_move_probability += (0.5 - self.satisfaction) * 0.2

        # Market conditions affect probability
        market_multiplier = market_conditions.get('mobility_multiplier', 1.0)
        final_probability = base_move_probability * market_multiplier

        # Cap the maximum probability at 30%
        final_probability = min(0.3, final_probability)

        return random.random() < final_probability

    def find_new_unit(self, market, policy):
        """Find a new unit to move to based on household preferences and constraints."""
        available_units = [u for u in market.units if not u.occupied]
        if not available_units:
            return None

        # Score each available unit
        scored_units = []
        for unit in available_units:
            # Skip if rent is too high (more than 50% of income)
            if unit.rent > self.income * 0.5:
                continue

            score = self.evaluate_unit(unit, market.market_conditions)
            scored_units.append((score, unit))

        if not scored_units:
            return None

        # Sort by score (highest first) and return the best unit
        scored_units.sort(reverse=True, key=lambda x: x[0])
        return scored_units[0][1] if scored_units else None

    def evaluate_unit(self, unit, market_conditions):
        """Score a unit based on household preferences and market conditions."""
        score = 0.0

        # Base affordability score (0-40 points)
        rent_to_income = unit.rent / self.income if self.income > 0 else float('inf')
        if rent_to_income <= 0.3:
            affordability_score = 40
        elif rent_to_income <= 0.4:
            affordability_score = 30
        elif rent_to_income <= 0.5:
            affordability_score = 20
        else:
            affordability_score = 0
        
        # If wealth is decreasing, put more weight on affordability
        if hasattr(self, 'wealth_trend') and self.wealth_trend < 0:
            affordability_score *= 1.5  # 50% more importance when losing money

        score += affordability_score

        # Quality score (0-30 points)
        quality_score = unit.quality * 30
        score += quality_score

        # Size match score (0-20 points)
        ideal_size = self.size * 25  # 25 square meters per person
        size_diff = abs(unit.square_meters - ideal_size) if hasattr(unit, 'square_meters') else float('inf')
        if size_diff <= 10:
            size_score = 20
        elif size_diff <= 20:
            size_score = 15
        elif size_diff <= 30:
            size_score = 10
        elif size_diff <= 40:
            size_score = 5
        else:
            size_score = 0
        score += size_score

        # Location/neighborhood score (0-10 points)
        # This could be based on distance to city center, amenities, etc.
        # For now, use a random factor influenced by market conditions
        location_score = random.uniform(0, 10) * market_conditions.get('location_multiplier', 1.0)
        score += location_score

        return score
