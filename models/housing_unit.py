# models/housing_unit.py
import random

class HousingUnit:
    def __init__(self, id, quality, base_rent, base_price):
        self.id = id
        self.quality = quality
        self.rent = base_rent
        self.price = base_price
        self.current_value = base_price
        self.occupied = False
        self.tenant = None
        self.owner = None
        self.violations = 0

    def assign_renter(self, tenant):
        self.tenant = tenant
        self.occupied = True

    def vacate_renter(self):
        self.tenant = None
        self.occupied = False

    def assign_owner(self, owner):
        self.owner = owner

    def update_price(self, growth_rate=0.02):
        self.current_value *= (1 + growth_rate)