# models/market.py
import numpy as np
from collections import defaultdict
import random

class RentalMarket:
    def __init__(self, units):
        self.units = units
        self.market_conditions = {
            'base_demand': 0.5,
            'average_rent': self._calculate_average_rent(),
            'rent_growth_rate': 0.02,
            'market_demand': 0.5,
            'vacancy_rate': self._calculate_vacancy_rate(),
            'price_index': 100,  # Base price index
            'location_premiums': self._calculate_location_premiums()
        }
        self.historical_data = {
            'rents': [],
            'vacancy_rates': [],
            'price_indices': [],
            'demand_levels': []
        }

    def _calculate_average_rent(self):
        return np.mean([u.rent for u in self.units])

    def _calculate_vacancy_rate(self):
        vacant = len([u for u in self.units if not u.occupied])
        return vacant / len(self.units) if self.units else 0

    def _calculate_location_premiums(self):
        location_rents = defaultdict(list)
        for unit in self.units:
            location_rents[round(unit.location, 1)].append(unit.rent)
        
        return {
            loc: np.mean(rents) for loc, rents in location_rents.items()
        }

    def update_market_conditions(self):
        self.market_conditions.update({
            'average_rent': self._calculate_average_rent(),
            'vacancy_rate': self._calculate_vacancy_rate(),
            'location_premiums': self._calculate_location_premiums()
        })

        # Update price index
        if self.historical_data['rents']:
            base_rent = np.mean(self.historical_data['rents'][0])
            current_rent = self._calculate_average_rent()
            self.market_conditions['price_index'] = (current_rent / base_rent) * 100

        self._store_historical_data()
        self._update_market_demand()

    def _store_historical_data(self):
        self.historical_data['rents'].append(self._calculate_average_rent())
        self.historical_data['vacancy_rates'].append(self._calculate_vacancy_rate())
        self.historical_data['price_indices'].append(self.market_conditions['price_index'])
        self.historical_data['demand_levels'].append(self.market_conditions['market_demand'])

    def _update_market_demand(self):
        vacancy_factor = 1 - self.market_conditions['vacancy_rate']
        price_factor = 1 - (self.market_conditions['price_index'] / 100 - 1)
        economic_factor = 1.0  # Could be updated based on external economic conditions
        
        # Add seasonal factor
        current_month = len(self.historical_data['rents']) % 12
        seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * current_month / 12)  # Seasonal variation
        
        # Add trend factor based on historical data
        trend_factor = 1.0
        if len(self.historical_data['rents']) > 12:
            recent_trend = np.mean(self.historical_data['rents'][-12:]) / np.mean(self.historical_data['rents'][-24:-12])
            trend_factor = 1 + (recent_trend - 1) * 0.5  # Dampen the trend effect
        
        self.market_conditions['market_demand'] = (
            self.market_conditions['base_demand'] * 
            vacancy_factor * 
            price_factor * 
            economic_factor *
            seasonal_factor *
            trend_factor
        )
        
        # Ensure demand stays within reasonable bounds
        self.market_conditions['market_demand'] = max(0.1, min(0.9, self.market_conditions['market_demand']))

    def find_best_unit(self, income, preference=0.5, size_preference=1, location_preference=0.5, only_vacant=True):
        available_units = []
        for unit in self.units:
            # Skip owner-occupied units
            if getattr(unit, 'is_owner_occupied', False):
                continue
                
            # Skip occupied units if only looking for vacant ones
            if only_vacant and unit.occupied:
                continue
                
            # Basic affordability check
            if unit.rent > 0.5 * income:
                continue
                
            available_units.append(unit)
            
        return random.choice(available_units) if available_units else None

    def find_acceptable_unit(self, max_rent, min_quality=0.5, min_size=1):
        available = [
            u for u in self.units 
            if not u.occupied 
            and not getattr(u, 'is_owner_occupied', False)
            and u.rent <= max_rent 
            and u.quality >= min_quality
            and u.size >= min_size
        ]
        if not available:
            return None
        return min(available, key=lambda u: u.rent)  # Return cheapest acceptable unit

    def vacant_units(self):
        return [u for u in self.units if not u.occupied]

    def get_market_statistics(self):
        return {
            'average_rent': self._calculate_average_rent(),
            'vacancy_rate': self._calculate_vacancy_rate(),
            'price_index': self.market_conditions['price_index'],
            'market_demand': self.market_conditions['market_demand'],
            'location_premiums': self.market_conditions['location_premiums']
        }

    def get_historical_trends(self):
        return {
            'rent_trend': self.historical_data['rents'],
            'vacancy_trend': self.historical_data['vacancy_rates'],
            'price_index_trend': self.historical_data['price_indices'],
            'demand_trend': self.historical_data['demand_levels']
        }
