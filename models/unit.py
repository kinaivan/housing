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
        
        # Depreciation and maintenance
        self.depreciation_rate = 0.01  # 1% per period
        self.maintenance_cost = base_rent * 0.1  # 10% of rent
        
    def _generate_amenities(self):
        amenity_list = ['parking', 'balcony', 'garden', 'gym', 'pool', 'security']
        return {amenity: random.random() < 0.3 for amenity in amenity_list}

    def assign(self, household):
        """Assign a single household to this unit"""
        if self.occupied and self.tenant is not None:
            # Remove previous tenant
            self.vacate()
        
        self.tenant = household
        self.tenants = [household]
        self.occupied = True
        self.vacancy_duration = 0

    def assign_multiple(self, households):
        """Assign multiple households to share this unit"""
        if self.occupied:
            self.vacate()
        
        self.tenants = households
        self.tenant = households[0]  # Primary tenant for compatibility
        self.occupied = True
        self.vacancy_duration = 0

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
            
        if not self.tenants:
            # Unit becomes vacant
            self.tenant = None
            self.occupied = False
        elif self.tenant == household:
            # Update primary tenant
            self.tenant = self.tenants[0]

    def vacate(self):
        """Remove all tenants from the unit"""
        self.tenant = None
        self.tenants = []
        self.occupied = False

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
        self.maintenance_budget = 0
        self.renovation_budget = 0
        
        # Set landlord reference in units
        for unit in self.units:
            unit.landlord = self
            
        # Landlord characteristics
        self.greed_factor = random.uniform(0.5, 1.5)
        self.maintenance_willingness = random.uniform(0.3, 0.9)
        self.market_awareness = random.uniform(0.4, 1.0)

    def add_unit(self, unit):
        """Add a unit to this landlord's portfolio"""
        self.units.append(unit)
        unit.landlord = self

    def update_rents(self, policy, market_conditions):
        for unit in self.units:
            # Calculate market rent
            market_rent = unit.calculate_market_rent(market_conditions)
            
            # Market conditions factors
            market_demand = market_conditions.get('market_demand', 0.5)
            vacancy_rate = market_conditions.get('vacancy_rate', 0.1)
            price_index = market_conditions.get('price_index', 100)
            
            # Base market adjustment (can be positive or negative)
            market_pressure = (market_demand - 0.5) * 2  # -1 to +1 range
            vacancy_pressure = (0.15 - vacancy_rate) * 2  # Negative when high vacancy
            
            # Landlord's market responsiveness
            market_adjustment = (market_pressure + vacancy_pressure) * 0.5 * self.market_awareness
            
            # If unit is vacant, be more responsive to market conditions
            if not unit.occupied:
                if unit.vacancy_duration > 0:
                    # Aggressive rent adjustments for vacant units
                    if market_demand < 0.4 or vacancy_rate > 0.2:
                        # Market is soft - reduce rents significantly
                        vacancy_discount = min(0.25, 0.05 + 0.08 * (unit.vacancy_duration / 2))
                        desired_rent = unit.rent * (1 - vacancy_discount)
                    elif market_demand > 0.6 and vacancy_rate < 0.1:
                        # Hot market - can increase even vacant units
                        desired_rent = unit.rent * (1 + 0.05 * self.greed_factor)
                    else:
                        # Moderate market - small adjustment toward market rate
                        adjustment = market_adjustment * 0.1
                        desired_rent = unit.rent * (1 + adjustment)
                    
                    # But don't go below 50% of base rent or above 200%
                    desired_rent = max(unit.base_rent * 0.5, min(unit.base_rent * 2.0, desired_rent))
                else:
                    # Newly vacant - try market rate first
                    desired_rent = market_rent
            else:
                # Occupied units: balance market conditions with tenant retention
                base_adjustment = 0.02 * self.greed_factor * self.market_awareness
                
                # Apply market pressure (can be negative)
                total_adjustment = base_adjustment + market_adjustment * 0.05
                
                # Tenant satisfaction consideration
                if len(unit.tenants) > 0:
                    avg_satisfaction = sum(t.satisfaction for t in unit.tenants) / len(unit.tenants)
                    
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
            
            # Economic cycle effects
            cycle_adjustment = np.sin(price_index / 20) * 0.01  # Small cyclical adjustment
            desired_rent *= (1 + cycle_adjustment)
            
            # Apply the rent change with reasonable bounds
            unit.rent = max(unit.base_rent * 0.4, min(unit.base_rent * 2.5, desired_rent))

    def collect_rent(self, periods=1):
        total_rent = 0
        for unit in self.units:
            if unit.occupied and unit.tenants:
                # Collect rent from all tenants sharing the unit
                unit_rent = unit.rent * periods
                total_rent += unit_rent
                
                # Deduct maintenance costs
                maintenance = unit.maintenance_cost * periods
                total_rent -= maintenance
                
        self.total_profit += total_rent
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
        
        return {
            'total_units': total_units,
            'occupied_units': occupied_units,
            'vacancy_rate': (total_units - occupied_units) / total_units,
            'average_rent': avg_rent,
            'average_quality': avg_quality,
            'total_profit': self.total_profit
        }
