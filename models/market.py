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
            'location_premiums': self._calculate_location_premiums(),
            'interest_rates': 0.03,  # Base mortgage rate
            'sale_volume': 0,  # Number of sales in current period
            'average_sale_price': 0,  # Average sale price in current period
            'owner_occupancy_rate': self._calculate_owner_occupancy_rate()
        }
        self.historical_data = {
            'rents': [],
            'vacancy_rates': [],
            'price_indices': [],
            'demand_levels': [],
            'sale_prices': [],
            'sale_volumes': [],
            'owner_occupancy_rates': []
        }
        self.transactions = []  # Track property transactions

    def _calculate_average_rent(self):
        rents = [u.rent for u in self.units]
        return np.mean(rents) if rents else 0

    def _calculate_vacancy_rate(self):
        if not self.units:
            return 0
        vacant = len([u for u in self.units if not u.occupied])
        return vacant / len(self.units)

    def _calculate_location_premiums(self):
        location_rents = defaultdict(list)
        for unit in self.units:
            location_rents[round(unit.location, 1)].append(unit.rent)
        
        return {
            loc: np.mean(rents) if rents else 0 for loc, rents in location_rents.items()
        }

    def _calculate_owner_occupancy_rate(self):
        """Calculate the percentage of units that are owner-occupied"""
        if not self.units:
            return 0
        owner_occupied = len([u for u in self.units if getattr(u, 'is_owner_occupied', False)])
        return owner_occupied / len(self.units)

    def process_property_sales(self):
        """Process all pending property sales"""
        sales_this_period = []
        
        # Get all units listed for sale
        for_sale_units = [u for u in self.units if u.for_sale]
        
        # Track sales data
        total_sale_price = 0
        num_sales = 0
        
        for unit in for_sale_units:
            # Skip if no valid sale price
            if not unit.sale_price:
                continue
                
            # If unit has a landlord, they're selling
            if unit.landlord:
                # Record the sale
                sale_data = {
                    'unit_id': unit.id,
                    'seller_type': 'landlord',
                    'seller_id': unit.landlord.id,
                    'sale_price': unit.sale_price,
                    'market_value': unit.market_value,
                    'condition': unit.quality
                }
                sales_this_period.append(sale_data)
                
                # Update statistics
                total_sale_price += unit.sale_price
                num_sales += 1
                
                # Remove from landlord's portfolio
                unit.landlord.sell_unit(unit, unit.sale_price)
                
            # If unit has an owner, they're selling
            elif unit.owner:
                # Record the sale
                sale_data = {
                    'unit_id': unit.id,
                    'seller_type': 'owner_occupier',
                    'seller_id': unit.owner.id,
                    'sale_price': unit.sale_price,
                    'market_value': unit.market_value,
                    'condition': unit.quality
                }
                sales_this_period.append(sale_data)
                
                # Update statistics
                total_sale_price += unit.sale_price
                num_sales += 1
                
                # Process the sale
                unit.owner.sell_home(unit.sale_price)
            
            # Reset unit's sale status
            unit.remove_from_market()
        
        # Update market conditions with sales data
        self.market_conditions['sale_volume'] = num_sales
        self.market_conditions['average_sale_price'] = (
            total_sale_price / num_sales if num_sales > 0 else 0
        )
        
        # Store transactions
        self.transactions.extend(sales_this_period)
        
        # Update historical data
        self._store_sales_data()

    def _store_sales_data(self):
        """Store sales data in historical records"""
        self.historical_data['sale_prices'].append(
            self.market_conditions['average_sale_price']
        )
        self.historical_data['sale_volumes'].append(
            self.market_conditions['sale_volume']
        )
        self.historical_data['owner_occupancy_rates'].append(
            self._calculate_owner_occupancy_rate()
        )

    def update_market_conditions(self):
        # Update basic metrics
        self.market_conditions.update({
            'average_rent': self._calculate_average_rent(),
            'vacancy_rate': self._calculate_vacancy_rate(),
            'location_premiums': self._calculate_location_premiums(),
            'owner_occupancy_rate': self._calculate_owner_occupancy_rate()
        })

        # Process property sales
        self.process_property_sales()

        # Update vacancy duration for all units
        for unit in self.units:
            if not unit.occupied and not unit.is_owner_occupied:
                pass
            else:
                unit.vacancy_duration = 0

        # Update price index
        if self.historical_data['rents']:
            base_rent = self.historical_data['rents'][0]
            current_rent = self._calculate_average_rent()
            if base_rent > 0:
                self.market_conditions['price_index'] = (current_rent / base_rent) * 100
            else:
                self.market_conditions['price_index'] = 100

        # Update interest rates based on market conditions
        base_rate = 0.03  # 3% base rate
        demand_adjustment = (self.market_conditions['market_demand'] - 0.5) * 0.01
        price_adjustment = (self.market_conditions['price_index'] - 100) / 1000
        self.market_conditions['interest_rates'] = max(0.02, min(0.08, 
            base_rate + demand_adjustment + price_adjustment
        ))

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
        
        # Add seasonal factor (now for 6-month periods)
        current_period = len(self.historical_data['rents']) % 2
        seasonal_factor = 1 + 0.1 * np.sin(np.pi * current_period)  # Seasonal variation
        
        # Add trend factor based on historical data
        trend_factor = 1.0
        if len(self.historical_data['rents']) > 3:
            recent_rents = self.historical_data['rents'][-2:]
            older_rents = self.historical_data['rents'][-4:-2]
            if recent_rents and older_rents:
                recent_avg = np.mean(recent_rents)
                older_avg = np.mean(older_rents)
                if older_avg > 0:
                    recent_trend = recent_avg / older_avg
                    trend_factor = 1 + (recent_trend - 1) * 0.5  # Dampen the trend effect
        
        # More dynamic market demand based on conditions
        base_demand = 0.5 + (0.2 if self.market_conditions['vacancy_rate'] > 0.1 else -0.1)
        
        self.market_conditions['market_demand'] = (
            base_demand * 
            vacancy_factor * 
            price_factor * 
            economic_factor *
            seasonal_factor *
            trend_factor
        )
        
        # Ensure demand stays within reasonable bounds but allow for more variation
        self.market_conditions['market_demand'] = max(0.2, min(0.95, self.market_conditions['market_demand']))

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
        stats = super().get_market_statistics()
        stats.update({
            'interest_rates': self.market_conditions['interest_rates'],
            'sale_volume': self.market_conditions['sale_volume'],
            'average_sale_price': self.market_conditions['average_sale_price'],
            'owner_occupancy_rate': self.market_conditions['owner_occupancy_rate']
        })
        return stats

    def get_historical_trends(self):
        trends = super().get_historical_trends()
        trends.update({
            'sale_price_trend': self.historical_data['sale_prices'],
            'sale_volume_trend': self.historical_data['sale_volumes'],
            'owner_occupancy_trend': self.historical_data['owner_occupancy_rates']
        })
        return trends

    def get_for_sale_units(self, max_price=None, min_quality=None):
        """Get list of units currently for sale matching criteria"""
        units = [u for u in self.units if u.for_sale]
        
        if max_price is not None:
            units = [u for u in units if u.sale_price <= max_price]
            
        if min_quality is not None:
            units = [u for u in units if u.quality >= min_quality]
            
        return units

    def get_recent_sales(self, num_periods=1):
        """Get recent sales data for market analysis"""
        if not self.transactions:
            return []
            
        # Get sales from recent periods
        recent_sales = self.transactions[-num_periods:]
        
        # Calculate summary statistics
        if recent_sales:
            prices = [s['sale_price'] for s in recent_sales]
            return {
                'num_sales': len(recent_sales),
                'avg_price': np.mean(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'price_std': np.std(prices),
                'sales_data': recent_sales
            }
        return {
            'num_sales': 0,
            'avg_price': 0,
            'min_price': 0,
            'max_price': 0,
            'price_std': 0,
            'sales_data': []
        }
