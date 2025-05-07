# simulation/runner.py
import random

class Simulation:
    def __init__(self, households, landlords, rental_market, policy, years=1):
        self.households = households
        self.landlords = landlords
        self.rental_market = rental_market
        self.policy = policy
        self.years = years
        self.metrics = []

    def step(self, year, month):
        # Rent updates
        for landlord in self.landlords:
            landlord.update_rents(self.policy)

        # Households consider moving
        for household in self.households:
            household.consider_moving(self.rental_market, self.policy, year, month)
            household.calculate_satisfaction()

        # Government inspects units
        for landlord in self.landlords:
            for unit in landlord.units:
                if unit.occupied and random.random() < self.policy.inspection_rate:
                    self.policy.inspect(unit)

        # Landlords collect rent
        for landlord in self.landlords:
            landlord.collect_rent()
    
        # Record metrics
        housed = sum(h.housed for h in self.households)
        avg_burden = sum(h.current_rent_burden() or 0 for h in self.households if h.housed) / housed if housed else 0
        avg_satisfaction = sum(h.satisfaction for h in self.households) / len(self.households)
        total_profit = sum(l.total_profit for l in self.landlords)

        self.metrics.append({
            "year": year, "month": month, "housed": housed,
            "avg_burden": avg_burden, "satisfaction": avg_satisfaction,
            "profit": total_profit, "violations": self.policy.violations_found
        })

    def run(self):
        for year in range(1, self.years + 1):
            for month in range(1, 13):
                self.step(year, month)

    def report(self):
        for m in self.metrics:
            print(f"{m['year']:>4}-{m['month']:>02} | Housed: {m['housed']:>2} | Avg Burden: {m['avg_burden']:.2f} | Satisfaction: {m['satisfaction']:.2f} | Profit: {m['profit']:.0f} | Violations: {m['violations']}")
