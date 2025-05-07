# models/unit.py
import random

class RentalUnit:
    def __init__(self, id, quality, base_rent):
        self.id = id
        self.quality = quality
        self.rent = base_rent
        self.tenant = None
        self.occupied = False
        self.violations = 0

    def assign(self, tenant):
        self.tenant = tenant
        self.occupied = True

    def vacate(self):
        self.tenant = None
        self.occupied = False

    def raise_rent(self, amount, rent_cap=None):
        new_rent = self.rent + amount
        if rent_cap is not None:
            new_rent = min(new_rent, rent_cap)
        self.rent = max(new_rent, 100)  # ensure rent doesn't go too low


class Landlord:
    def __init__(self, id, units, is_compliant=True):
        self.id = id
        self.units = units
        self.total_profit = 0
        self.is_compliant = is_compliant

    def update_rents(self, policy):
        for unit in self.units:
            if not unit.occupied:
                unit.raise_rent(-10)  # lower rent if vacant
            elif unit.tenant:
                # Greedy strategy: raise rent to max tenant can pay
                if policy.rent_cap_ratio < 1.0:
                    max_rent = policy.max_rent_for_income(unit.tenant.income)
                else:
                    max_rent = 0.5 * unit.tenant.income  # unlimited if no cap

                unit.rent = max(max_rent, 100)  # set directly to max allowed

    def collect_rent(self):
        for unit in self.units:
            if unit.occupied:
                self.total_profit += unit.rent
