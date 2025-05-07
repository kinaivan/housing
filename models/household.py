# models/household.py
import collections
import random

TimeLineEntry = collections.namedtuple('TimeLineEntry', ('year', 'month', 'record'))

def new_timeline_entry(info, year, month):
    return TimeLineEntry(year, month, info)

class Household:
    def __init__(self, id, age, size, income, wealth, contract=None):
        self.id = id
        self.age = age
        self.size = size
        self.income = income
        self.wealth = wealth
        self.contract = contract
        self.housed = contract is not None
        self.timeline = []
        self.satisfaction = 0

        # behavioral attributes
        self.mobility_preference = random.uniform(0, 1)
        self.quality_preference = random.uniform(0, 1)
        self.cost_sensitivity = random.uniform(0.2, 0.5)  # how much rent burden matters

    def current_rent_burden(self):
        if self.contract and self.income > 0:
            return self.contract.unit.rent / self.income
        return None

    def update_month(self, year, month):
        self.age += 1/12
        self.adjust_income()
        self.adjust_wealth()
        if self.contract:
            self.contract.update()
        self.calculate_satisfaction()

    def adjust_income(self):
        # simplistic: small random drift
        drift = random.uniform(-0.02, 0.05)
        self.income = max(500, self.income * (1 + drift))

    def adjust_wealth(self):
        saving_rate = 0.1
        housing_cost = self.contract.unit.rent if self.contract else 0
        savings = max(0, self.income - housing_cost) * saving_rate
        self.wealth += savings

    def calculate_satisfaction(self):
        if self.contract:
            burden = self.contract.unit.rent / self.income
            self.satisfaction = max(0, 1 - burden * self.cost_sensitivity)
        else:
            self.satisfaction = 0

    def consider_moving(self, market, policy, year, month):
        # Probability-based move if dissatisfaction
        move_chance = 1 - self.satisfaction
        if random.random() < move_chance * self.mobility_preference:
            best_unit = market.find_best_unit(self.income, preference=self.quality_preference)
            if best_unit and best_unit.rent <= policy.max_rent_for_income(self.income):
                self.move_to(best_unit, year, month)

    def move_to(self, unit, year, month):
        if self.contract:
            self.contract.unit.vacate()
        unit.assign(self)
        self.contract = Contract(self, unit)
        self.housed = True
        self.calculate_satisfaction()
        self.add_event({"type": "MOVED_IN", "unit_id": unit.id, "rent": unit.rent}, year, month)

    def end_month(self):
        if self.contract:
            self.contract.update()

    def add_event(self, info, year, month):
        self.timeline.append(new_timeline_entry(info, year, month))

class Contract:
    def __init__(self, tenant, unit):
        self.tenant = tenant
        self.unit = unit
        self.months = 0

    def update(self):
        self.months += 1
