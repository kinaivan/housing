# models/market.py
class RentalMarket:
    def __init__(self, units):
        self.units = units

    def find_best_unit(self, max_rent, preference=None):
        available = [u for u in self.units if not u.occupied and u.rent <= max_rent]
        if not available:
            return None
        if preference is None:
            return max(available, key=lambda u: u.quality)
        # Weighted quality sorting if preference is specified
        return max(available, key=lambda u: preference * u.quality - (1 - preference) * (u.rent / max_rent))
    
    def vacant_units(self):
        return [u for u in self.units if not u.occupied]
