# models/unit.py
import random
import numpy as np

class RentalUnit:
    def __init__(self, id, quality, base_rent, size=None, location=None):
        self.id = id
        self.quality = quality
        self.base_rent = base_rent
        self.rent = base_rent
        self.occupied = False
        self.tenant = None
        self.tenants = []  # Support multiple tenants sharing
        self.landlord = None
        self.last_renovation = 0
        self.vacancy_duration = 0
        self.violations = 0  # Track housing code violations
        
        # Enhanced unit characteristics
        self.size = size if size is not None else random.randint(1, 4)
        self.location = location if location is not None else random.uniform(0, 1)
        self.location_score = self.location
        self.amenity_score = random.uniform(0, 1)
        self.amenities = self._generate_amenities()
        
        # Land value characteristics
        self.base_land_value = self._calculate_base_land_value()
        self.land_value = self.base_land_value
        
        # Depreciation and maintenance
        self.depreciation_rate = 0.01  # 1% per period
        self.maintenance_cost = base_rent * 0.1  # 10% of rent
        
    def _generate_amenities(self):
        amenity_list = ['parking', 'balcony', 'garden', 'gym', 'pool', 'security']
        return {amenity: random.random() < 0.3 for amenity in amenity_list}

    def _calculate_base_land_value(self):
        """Calculate the base land value based on location and size"""
        # Location has strong influence on land value (exponential relationship)
        location_factor = np.exp(self.location * 2) / np.e  # normalized to 1 at location=0.5
        
        # Size affects value linearly
        size_factor = self.size / 2  # normalized to 1 at size=2
        
        # Base value (could be adjusted based on market conditions)
        base_value = 100000  # Base land value of 100k
        
        return base_value * location_factor * size_factor

    def update_land_value(self, market_conditions):
        """Update land value based on market conditions"""
        market_demand = market_conditions.get('market_demand', 0.5)
        price_index = market_conditions.get('price_index', 100) / 100
        
        # Market demand affects land value
        demand_factor = 1 + (market_demand - 0.5)  # Range: 0.5 to 1.5
        
        # Price index affects land value
        price_factor = price_index
        
        # Location premiums from market conditions
        location_premiums = market_conditions.get('location_premiums', {})
        location_key = round(self.location, 1)
        location_premium = location_premiums.get(location_key, 0)
        
        # Update land value
        self.land_value = self.base_land_value * demand_factor * price_factor * (1 + location_premium)
        
        return self.land_value

    def get_improvement_value(self):
        """Calculate the value of improvements (buildings) on the land"""
        # Base improvement value from construction cost
        base_improvement = self.base_rent * 12 * 10  # Assume 10 years of rent as base improvement value
        
        # Quality affects improvement value
        quality_factor = self.quality * 2  # Range: 0 to 2
        
        # Recent renovations increase improvement value
        renovation_factor = 1 + (self.last_renovation * 0.1 if self.last_renovation > 0 else 0)
        
        return base_improvement * quality_factor * renovation_factor

    def assign(self, household):
        """Assign a single household to this unit"""
        if self.occupied and self.tenant is not None:
            # Remove previous tenant
            self.vacate()
        
        self.tenant = household
        self.tenants = [household]
        self.occupied = True
        self.vacancy_duration = 0
        # Update occupants count based on household size
        self.occupants = household.size
        
        # If unit was previously vacant, gradually restore rent to market levels
        if hasattr(self, 'rent_reduction_history') and self.rent_reduction_history:
            # Start restoring rent to base rent over time
            self.rent = min(self.base_rent, self.rent * 1.05)  # 5% increase per occupancy

    def assign_multiple(self, households):
        """Assign multiple households to share this unit"""
        if self.occupied:
            self.vacate()
        
        self.tenants = households
        self.tenant = households[0]  # Primary tenant for compatibility
        self.occupied = True
        self.vacancy_duration = 0
        # Update occupants count based on total household sizes
        self.occupants = sum(h.size for h in households)
        # If unit was previously vacant, gradually restore rent to market levels
        if hasattr(self, 'rent_reduction_history') and self.rent_reduction_history:
            # Start restoring rent to base rent over time
            self.rent = min(self.base_rent, self.rent * 1.05)  # 5% increase per occupancy

    def add_tenant(self, household):
        """Add an additional tenant to share the unit"""
        if household not in self.tenants:
            self.tenants.append(household)
            if not self.occupied:
                self.tenant = household
                self.occupied = True
                self.vacancy_duration = 0

    def remove_tenant(self, household):
        """Remove a specific tenant from shared unit"""
        if household in self.tenants:
            self.tenants.remove(household)
            # Update occupants count
            self.occupants = sum(h.size for h in self.tenants)
            
        if not self.tenants:
            # Unit becomes vacant
            self.tenant = None
            self.occupied = False
            self.occupants = 0
        elif self.tenant == household:
            # Update primary tenant
            self.tenant = self.tenants[0]

    def vacate(self):
        """Remove all tenants from the unit"""
        self.tenant = None
        self.tenants = []
        self.occupied = False
        self.occupants = 0

    def get_total_household_size(self):
        """Get total number of people living in the unit"""
        return sum(tenant.size for tenant in self.tenants)

    def get_total_income(self):
        """Get combined income of all tenants"""
        return sum(tenant.income for tenant in self.tenants)

    def update(self, year, period):
        # Apply depreciation
        self.quality = max(0.1, self.quality - self.depreciation_rate)
        
        # Reset renovation counter
        if self.last_renovation > 0:
            self.last_renovation -= 1
            
        # Update amenity scores based on quality
        if self.quality < 0.5:
            self.amenity_score = max(0, self.amenity_score - 0.02)

    def renovate(self, investment=None):
        if investment is None:
            investment = self.base_rent * 2  # Default renovation cost
            
        # Improve quality
        quality_improvement = min(0.3, investment / (self.base_rent * 10))
        self.quality = min(1.0, self.quality + quality_improvement)
        
        # Update amenities
        for amenity in self.amenities:
            if random.random() < 0.3:  # 30% chance to add/improve amenity
                self.amenities[amenity] = True
                
        self.amenity_score = min(1.0, self.amenity_score + 0.1)
        self.last_renovation = 12  # Mark as recently renovated
        
        return investment

    def calculate_market_rent(self, market_conditions):
        # Base rent calculation
        base = self.base_rent
        
        # Quality adjustment
        quality_multiplier = 0.8 + (self.quality * 0.4)  # 0.8 to 1.2 range
        
        # Location premium
        location_premiums = market_conditions.get('location_premiums', {})
        location_key = round(self.location, 1)
        location_premium = location_premiums.get(location_key, 0)
        
        # Market demand adjustment
        demand_factor = market_conditions.get('market_demand', 1.0)
        
        # Amenities premium
        amenity_count = sum(1 for v in self.amenities.values() if v)
        amenity_premium = amenity_count * 0.05  # 5% per amenity
        
        market_rent = base * quality_multiplier * (1 + location_premium + amenity_premium) * demand_factor
        
        return max(self.base_rent * 0.5, market_rent)  # Don't go below 50% of base rent

    def __str__(self):
        return f"Unit {self.id}: ${self.rent:.0f}, Quality: {self.quality:.2f}, {'Occupied' if self.occupied else 'Vacant'}"

class Landlord:
    def __init__(self, id, units, is_compliant=True):
        self.id = id
        self.units = units
        self.is_compliant = is_compliant
        self.total_profit = 0
        self.wealth = 0  # Initialize wealth
        
        # Landlord behavior parameters
        self.greed_factor = random.uniform(0.5, 1.5)  # How aggressively they raise rents
        self.market_awareness = random.uniform(0.7, 1.0)  # How well they track market conditions
        self.maintenance_priority = random.uniform(0.3, 1.0)  # How much they prioritize maintenance
        
        # Assign self as landlord to all units
        for unit in units:
            unit.landlord = self

    def add_unit(self, unit):
        """Add a unit to this landlord's portfolio"""
        self.units.append(unit)
        unit.landlord = self

    def update_rents(self, policy, market_conditions):
        # Track wealth trend
        self.wealth_history = getattr(self, 'wealth_history', [])
        self.wealth_history.append(self.wealth)
        # Keep last 4 periods (2 years) of history
        if len(self.wealth_history) > 4:
            self.wealth_history = self.wealth_history[-4:]
        
        # Calculate wealth trend
        wealth_trend = 0
        if len(self.wealth_history) >= 2:
            initial_wealth = self.wealth_history[0]
            current_wealth = self.wealth_history[-1]
            if initial_wealth != 0:
                wealth_trend = (current_wealth - initial_wealth) / initial_wealth
            else:
                # If initial wealth was 0, calculate trend based on absolute change
                wealth_trend = current_wealth / 1000 if current_wealth > 0 else 0

        market_demand = market_conditions.get('market_demand', 0.5)
        price_index = market_conditions.get('price_index', 100)
        market_rent = market_conditions.get('market_rent', 1000)
        market_adjustment = (market_rent - 1000) / 1000  # Normalized market pressure

        for unit in self.units:
            # Economic cycle effects
            cycle_adjustment = np.sin(price_index / 20) * 0.01  # Small cyclical adjustment

            if not unit.occupied:
                # Apply vacancy-based rent reduction strategy
                self._apply_vacancy_rent_reduction(unit, market_conditions, wealth_trend)
                # Apply cycle adjustment to the reduced rent
                unit.rent *= (1 + cycle_adjustment)
            else:
                # Occupied units: balance market conditions with tenant retention
                base_adjustment = 0.02 * self.greed_factor * self.market_awareness
                
                # Apply market pressure (can be negative)
                total_adjustment = base_adjustment + market_adjustment * 0.05
                
                # Factor in wealth trend
                if wealth_trend < -0.1:  # Significant wealth decrease
                    # More aggressive rent increase when losing money
                    total_adjustment += abs(wealth_trend) * 0.1 * self.greed_factor
                elif wealth_trend > 0.1:  # Significant wealth increase
                    # More conservative with increases when doing well
                    total_adjustment *= 0.8
                
                # Tenant satisfaction consideration
                if len(unit.tenants) > 0:
                    avg_satisfaction = sum(t.satisfaction for t in unit.tenants) / len(unit.tenants)
                    avg_tenant_wealth = sum(t.wealth for t in unit.tenants) / len(unit.tenants)
                    
                    # Consider tenant's ability to pay
                    if avg_tenant_wealth < unit.rent * 12:  # Less than a year's rent in savings
                        total_adjustment = min(total_adjustment, 0.02)  # Cap increase at 2%
                    
                    # If tenants are unhappy, be more conservative
                    if avg_satisfaction < 0.4:
                        total_adjustment = min(total_adjustment, -0.01)  # Small decrease or no increase
                    elif avg_satisfaction < 0.6:
                        total_adjustment = min(total_adjustment, 0.01)   # Small increase only
                    
                    # If market is soft and tenants are satisfied, might reduce rent to retain them
                    if market_demand < 0.4 and avg_satisfaction > 0.7:
                        total_adjustment = min(total_adjustment, -0.005)  # Small decrease to retain good tenants
                
                desired_rent = unit.rent * (1 + total_adjustment)
                
                # Apply policy limits for compliant landlords
                if self.is_compliant and policy is not None:
                    max_increase = policy.max_increase_rate
                    # Policy typically only limits increases, not decreases
                    if total_adjustment > 0:
                        desired_rent = min(desired_rent, unit.rent * (1 + max_increase))
                elif self.is_compliant:
                    # Default max increase rate when no policy is in effect
                    max_increase = 0.10  # 10% default max increase
                    if total_adjustment > 0:
                        desired_rent = min(desired_rent, unit.rent * (1 + max_increase))
                
                # Apply cycle adjustment
                desired_rent *= (1 + cycle_adjustment)
                
                # Apply the rent change with reasonable bounds
                unit.rent = max(unit.base_rent * 0.4, min(unit.base_rent * 2.5, desired_rent))

    def _apply_vacancy_rent_reduction(self, unit, market_conditions, wealth_trend):
        """
        Apply strategic rent reductions for vacant units to attract tenants.
        This method implements a progressive rent reduction strategy based on:
        - Vacancy duration (longer vacancies = bigger reductions)
        - Market conditions (soft market = more aggressive reductions)
        - Landlord's financial situation (wealth trend affects strategy)
        - Unit characteristics (quality, location, etc.)
        """
        vacancy_duration = unit.vacancy_duration
        market_demand = market_conditions.get('market_demand', 0.5)
        vacancy_rate = market_conditions.get('vacancy_rate', 0.1)
        
        # Base reduction factors
        duration_factor = min(0.25, vacancy_duration * 0.02)  # Max 25% reduction after ~12 periods
        market_factor = (0.5 - market_demand) * 0.2  # Soft market = more reduction
        vacancy_factor = vacancy_rate * 0.3  # High vacancy rate = more reduction
        
        # Landlord-specific factors
        wealth_pressure = max(0, -wealth_trend * 0.1)  # Financial pressure increases reduction
        landlord_aggressiveness = (1.5 - self.greed_factor) * 0.1  # Less greedy = more reduction
        
        # Unit-specific factors
        quality_factor = (0.7 - unit.quality) * 0.1  # Lower quality = more reduction needed
        location_factor = (0.5 - unit.location_score) * 0.05  # Less desirable location = more reduction
        
        # Calculate total reduction percentage
        total_reduction = (
            duration_factor + 
            market_factor + 
            vacancy_factor + 
            wealth_pressure + 
            landlord_aggressiveness + 
            quality_factor + 
            location_factor
        )
        
        # Apply progressive reduction based on vacancy duration
        if vacancy_duration >= 12:  # After 1 year (assuming 6-month periods)
            # More aggressive reduction for long-term vacancies
            total_reduction *= 1.5
        elif vacancy_duration >= 6:  # After 6 months
            # Moderate reduction
            total_reduction *= 1.2
        elif vacancy_duration >= 3:  # After 3 months
            # Small reduction
            total_reduction *= 1.0
        else:
            # Minimal reduction for short vacancies
            total_reduction *= 0.5
        
        # Cap the maximum reduction at 40% of base rent
        max_reduction = 0.4
        total_reduction = min(total_reduction, max_reduction)
        
        # Calculate new rent
        target_rent = unit.base_rent * (1 - total_reduction)
        
        # Ensure rent doesn't go below minimum threshold (60% of base rent)
        min_rent = unit.base_rent * 0.6
        target_rent = max(target_rent, min_rent)
        
        # Apply the reduction gradually (not all at once)
        current_rent = unit.rent
        max_change_per_period = 0.1  # Maximum 10% change per period
        
        if target_rent < current_rent:
            # Reduce rent
            reduction_amount = current_rent - target_rent
            max_reduction_this_period = current_rent * max_change_per_period
            actual_reduction = min(reduction_amount, max_reduction_this_period)
            unit.rent = current_rent - actual_reduction
        else:
            # If target rent is higher than current, don't increase for vacant units
            # This prevents rent increases on vacant units
            pass
        
        # Update vacancy duration
        unit.vacancy_duration += 1
        
        # Log the rent reduction decision (for debugging/monitoring)
        if hasattr(unit, 'rent_reduction_history'):
            unit.rent_reduction_history.append({
                'period': unit.vacancy_duration,
                'old_rent': current_rent,
                'new_rent': unit.rent,
                'reduction_factor': total_reduction,
                'reason': f"Vacancy duration: {vacancy_duration}, Market demand: {market_demand:.2f}"
            })
        else:
            unit.rent_reduction_history = [{
                'period': unit.vacancy_duration,
                'old_rent': current_rent,
                'new_rent': unit.rent,
                'reduction_factor': total_reduction,
                'reason': f"Vacancy duration: {vacancy_duration}, Market demand: {market_demand:.2f}"
            }]

    def collect_rent(self, periods=1):
        total_rent = 0
        for unit in self.units:
            if unit.occupied and unit.tenants:
                # Collect rent from all tenants sharing the unit
                unit_rent = unit.rent * periods
                total_rent += unit_rent
                
                # Deduct rent from each tenant's wealth
                rent_per_tenant = unit_rent / len(unit.tenants)
                for tenant in unit.tenants:
                    tenant.wealth -= rent_per_tenant
                
                # Deduct maintenance costs
                maintenance = unit.maintenance_cost * periods
                total_rent -= maintenance
                
        self.total_profit += total_rent
        self.wealth = self.total_profit  # Update landlord's wealth based on profit
        return total_rent

    def update(self, market_conditions):
        # Update all units
        for unit in self.units:
            unit.update(year=0, period=0)  # Simplified for now
            
        # Investment decisions
        if self.total_profit > 0 and random.random() < 0.1:  # 10% chance to invest
            self._consider_renovations()

    def _consider_renovations(self):
        # Find units that need renovation
        candidates = [u for u in self.units if u.quality < 0.6 and u.last_renovation == 0]
        
        if candidates and self.total_profit > 1000:
            unit = min(candidates, key=lambda u: u.quality)
            cost = unit.renovate()
            self.total_profit -= cost

    def get_portfolio_stats(self):
        total_units = len(self.units)
        occupied_units = len([u for u in self.units if u.occupied])
        avg_rent = np.mean([u.rent for u in self.units])
        avg_quality = np.mean([u.quality for u in self.units])
        
        # Calculate vacancy statistics
        vacant_units = [u for u in self.units if not u.occupied]
        avg_vacancy_duration = np.mean([u.vacancy_duration for u in vacant_units]) if vacant_units else 0
        
        # Calculate rent reduction statistics
        rent_reductions = []
        for unit in vacant_units:
            if hasattr(unit, 'rent_reduction_history') and unit.rent_reduction_history:
                latest_reduction = unit.rent_reduction_history[-1]
                rent_reductions.append(latest_reduction['reduction_factor'])
        
        avg_rent_reduction = np.mean(rent_reductions) if rent_reductions else 0
        
        return {
            'total_units': total_units,
            'occupied_units': occupied_units,
            'vacancy_rate': (total_units - occupied_units) / total_units,
            'average_rent': avg_rent,
            'average_quality': avg_quality,
            'total_profit': self.total_profit,
            'average_vacancy_duration': avg_vacancy_duration,
            'average_rent_reduction': avg_rent_reduction,
            'vacant_units_count': len(vacant_units)
        }
