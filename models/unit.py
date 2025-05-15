# models/unit.py
import random
import numpy as np

class RentalUnit:
    def __init__(self, id, quality, base_rent, location=None):
        self.id = id
        self.quality = quality
        self.rent = base_rent
        self.base_rent = base_rent
        self.tenant = None
        self.occupied = False
        self.violations = 0
        self.vacancy_duration = 0
        self.last_renovation = 0
        self.maintenance_cost = base_rent * 0.1
        
        # Location attributes
        self.location = location or random.uniform(0, 1)  # 0 = suburban, 1 = central
        self.location_score = self._calculate_location_score()
        
        # Unit characteristics
        self.size = random.randint(1, 4)  # Number of bedrooms
        self.amenities = self._generate_amenities()
        self.amenity_score = self._calculate_amenity_score()
        
        # Market dynamics
        self.market_demand = 0.5  # Initial market demand
        self.price_elasticity = random.uniform(0.5, 1.5)  # How sensitive to price changes
        
        # Quality degradation
        self.quality_degradation_rate = random.uniform(0.01, 0.03)  # Monthly quality decrease
        self.minimum_quality = 0.3  # Minimum quality before renovation needed

        self.owner = None  # Household object if owner-occupied, else None
        self.is_owner_occupied = False

    def _generate_amenities(self):
        amenities = {
            'parking': random.random() < 0.7,
            'laundry': random.random() < 0.6,
            'gym': random.random() < 0.3,
            'pool': random.random() < 0.2,
            'security': random.random() < 0.4
        }
        return amenities

    def _calculate_amenity_score(self):
        amenity_weights = {
            'parking': 0.2,
            'laundry': 0.2,
            'gym': 0.15,
            'pool': 0.15,
            'security': 0.3
        }
        score = sum(amenity_weights[amenity] for amenity, present in self.amenities.items() if present)
        return score

    def _calculate_location_score(self):
        base_score = 1 - abs(0.5 - self.location)
        return base_score

    def assign(self, tenant):
        self.tenant = tenant
        self.occupied = True
        self.vacancy_duration = 0

    def vacate(self):
        self.tenant = None
        self.occupied = False
        self.vacancy_duration = 0

    def update(self, market_conditions):
        if not self.occupied:
            self.vacancy_duration += 1
            self._adjust_rent_for_vacancy()
        
        self._degrade_quality()
        self._update_market_demand(market_conditions)

    def _adjust_rent_for_vacancy(self):
        vacancy_factor = min(1.0, self.vacancy_duration / 6)  # Max effect after 6 months
        reduction = self.rent * 0.05 * vacancy_factor  # Up to 5% reduction per month
        self.rent = max(self.base_rent * 0.7, self.rent - reduction)  # Never below 70% of base rent

    def _degrade_quality(self):
        if self.occupied:
            self.quality -= self.quality_degradation_rate
            if self.quality < self.minimum_quality:
                self._schedule_renovation()

    def _schedule_renovation(self):
        self.quality = 0.8  # Reset to 80% of original quality
        self.last_renovation = 0
        self.rent *= 1.1  # Increase rent after renovation

    def _update_market_demand(self, market_conditions):
        base_demand = market_conditions.get('base_demand', 0.5)
        location_factor = self.location_score
        price_factor = 1 - (self.rent / market_conditions.get('average_rent', self.rent))
        quality_factor = self.quality
        
        self.market_demand = (base_demand + location_factor + price_factor + quality_factor) / 4

    def raise_rent(self, amount, rent_cap=None, market_conditions=None):
        if market_conditions:
            # Consider market conditions in rent adjustment
            market_factor = market_conditions.get('rent_growth_rate', 0.02)
            demand_factor = self.market_demand
            quality_factor = self.quality
            
            # Calculate rent increase based on multiple factors
            base_increase = amount * (1 + market_factor) * demand_factor * quality_factor
        else:
            base_increase = amount

        new_rent = self.rent + base_increase
        if rent_cap is not None:
            new_rent = min(new_rent, rent_cap)
        self.rent = max(new_rent, self.base_rent * 0.7)  # ensure rent doesn't go too low

    def assign_owner(self, owner):
        self.owner = owner
        self.is_owner_occupied = True
        self.tenant = owner  # For visualization/occupancy
        self.occupied = True
        self.vacancy_duration = 0
        # Remove from landlord if present
        if hasattr(self, 'landlord') and self.landlord is not None:
            self.landlord.remove_unit(self)
            self.landlord = None

    def remove_owner(self):
        self.owner = None
        self.is_owner_occupied = False
        self.tenant = None
        self.occupied = False
        self.vacancy_duration = 0
        # Unit is now available for rent; landlord assignment handled in simulation


class Landlord:
    def __init__(self, id, units, is_compliant=True):
        self.id = id
        self.units = units
        self.total_profit = 0
        self.is_compliant = is_compliant
        self.maintenance_budget = 0
        self.renovation_budget = 0
        self.risk_preference = random.uniform(0, 1)  # 0 = conservative, 1 = aggressive
        self.market_knowledge = random.uniform(0.5, 1.0)  # How well they understand the market

    def update_rents(self, policy, market_conditions):
        for unit in self.units:
            if not unit.occupied:
                self._handle_vacant_unit(unit, market_conditions)
            else:
                self._adjust_occupied_unit_rent(unit, policy, market_conditions)

    def _handle_vacant_unit(self, unit, market_conditions):
        market_demand = market_conditions.get('market_demand', 0.5)
        average_rent = market_conditions.get('average_rent', unit.rent)
        
        if unit.vacancy_duration > 3:  # If vacant for more than 3 months
            reduction = unit.rent * 0.05 * (1 - self.risk_preference)
            unit.rent = max(unit.base_rent * 0.7, unit.rent - reduction)
        else:
            # Adjust based on market conditions
            adjustment = (market_demand - 0.5) * 0.1 * unit.rent
            unit.rent = max(unit.base_rent * 0.7, unit.rent + adjustment)

    def _adjust_occupied_unit_rent(self, unit, policy, market_conditions):
        # Calculate base max rent based on tenant income
        if policy is not None:
            max_rent = policy.max_rent_for_income(unit.tenant.income)
            if not self.is_compliant:
                max_rent *= 1.1  # 10% over cap for non-compliant landlords
        else:
            # If no policy, use a default maximum of 50% of income
            max_rent = unit.tenant.income * 0.5

        # Consider market conditions
        market_demand = market_conditions.get('market_demand', 0.5)
        average_rent = market_conditions.get('average_rent', unit.rent)
        rent_growth = market_conditions.get('rent_growth_rate', 0.02)

        # Calculate rent increase based on multiple factors
        base_increase = unit.rent * rent_growth * (1 + self.risk_preference)
        market_adjustment = (market_demand - 0.5) * 0.1 * unit.rent
        quality_factor = unit.quality * 0.1 * unit.rent

        new_rent = unit.rent + base_increase + market_adjustment + quality_factor
        unit.rent = min(max_rent, new_rent)

    def collect_rent(self):
        for unit in self.units:
            if unit.occupied:
                # Calculate net profit after maintenance
                maintenance_cost = unit.maintenance_cost * unit.quality
                self.total_profit += unit.rent - maintenance_cost
                self.maintenance_budget += maintenance_cost

    def update(self, market_conditions):
        for unit in self.units:
            unit.update(market_conditions)
        self.update_rents(None, market_conditions)  # Policy is handled separately
        self.collect_rent()

    def remove_unit(self, unit):
        if unit in self.units:
            self.units.remove(unit)

    def add_unit(self, unit):
        if unit not in self.units:
            self.units.append(unit)
