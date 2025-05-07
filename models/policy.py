# models/policy.py
class RentCapPolicy:
    def __init__(self, rent_cap_ratio=0.3, max_increase_rate=0.05, inspection_rate=0.1):
        self.rent_cap_ratio = rent_cap_ratio
        self.max_increase_rate = max_increase_rate
        self.inspection_rate = inspection_rate
        self.violations_found = 0
        self.total_inspections = 0

    def max_rent_for_income(self, income):
        return self.rent_cap_ratio * income

    def max_rent_increase(self, current_rent):
        return self.max_increase_rate * current_rent

    def inspect(self, unit):
        self.total_inspections += 1
        if unit.rent > self.max_rent_for_income(unit.tenant.income):
            unit.violations += 1
            self.violations_found += 1