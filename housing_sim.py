import random
import numpy as np

class Household:
    def __init__(self, income):
        self.income = income
        self.rent_threshold = 0.3 * income
        self.satisfaction = 0
        self.housed = False
        self.unit = None

    def choose_unit(self, units):
        affordable_units = [u for u in units if u.rent <= self.rent_threshold and not u.occupied]
        if affordable_units:
            best_unit = max(affordable_units, key=lambda u: u.quality)
            self.unit = best_unit
            self.housed = True
            self.satisfaction = 1 - (best_unit.rent / self.income)
            best_unit.occupied = True
            best_unit.tenant = self
        else:
            self.unit = None
            self.housed = False
            self.satisfaction = 0


class Landlord:
    def __init__(self, units):
        self.units = units
        self.profit = 0

    def set_rents(self, rent_cap_enabled=False):
        for unit in self.units:
            if rent_cap_enabled:
                max_rent = 0.3 * unit.max_tenant_income
                unit.rent = min(unit.rent + random.uniform(-10, 10), max_rent)
            else:
                if not unit.occupied:
                    unit.rent -= 10  # lower rent if vacant
                else:
                    unit.rent += 10  # increase if occupied
            unit.rent = max(100, unit.rent)  # floor
            self.profit += unit.rent if unit.occupied else 0


class RentalUnit:
    def __init__(self, quality, base_rent):
        self.quality = quality
        self.rent = base_rent
        self.occupied = False
        self.tenant = None
        self.max_tenant_income = 0  # to be updated when tenant moves in


class HousingMarket:
    def __init__(self, num_households=15, num_units=10, rent_cap_enabled=False):
        self.households = [Household(random.randint(1000, 5000)) for _ in range(num_households)]
        self.units = [RentalUnit(random.uniform(0.5, 1.0), random.randint(200, 1000)) for _ in range(num_units)]
        self.landlord = Landlord(self.units)
        self.rent_cap_enabled = rent_cap_enabled
        self.metrics = []

    def step(self):
        # Reset units
        for unit in self.units:
            unit.occupied = False
            unit.tenant = None

        # Rent adjustment
        for h in self.households:
            unit = h.unit
            if unit:
                unit.max_tenant_income = max(unit.max_tenant_income, h.income)

        self.landlord.set_rents(self.rent_cap_enabled)

        # Households choose
        for h in self.households:
            h.choose_unit(self.units)

        # Record metrics
        housed = sum(h.housed for h in self.households)
        avg_burden = np.mean([h.unit.rent / h.income for h in self.households if h.housed]) if housed > 0 else 0
        avg_satisfaction = np.mean([h.satisfaction for h in self.households])
        total_profit = self.landlord.profit

        self.metrics.append({
            'avg_burden': avg_burden,
            'housed': housed,
            'displaced': len(self.households) - housed,
            'avg_satisfaction': avg_satisfaction,
            'total_profit': total_profit
        })

    def run(self, steps=10):
        for _ in range(steps):
            self.step()

    def report(self):
        count = 0
        for i, m in enumerate(self.metrics):
            count += 1
            if count == 999:
                print(f"Step {i}: Housed={m['housed']}, Avg Burden={m['avg_burden']:.2f}, Satisfaction={m['avg_satisfaction']:.2f}, Profit={m['total_profit']}")


if __name__ == "__main__":
    market = HousingMarket(rent_cap_enabled=False)
    market.run(steps=1000)
    market.report()

    print("\nWith rent cap:")
    capped_market = HousingMarket(rent_cap_enabled=True)
    capped_market.run(steps=1000)
    capped_market.report()