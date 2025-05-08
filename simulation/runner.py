# simulation/runner.py
import random
import numpy as np
from collections import defaultdict

class Simulation:
    def __init__(self, households, landlords, rental_market, policy, years=1):
        self.households = households
        self.landlords = landlords
        self.rental_market = rental_market
        self.policy = policy
        self.years = years
        self.metrics = []
        
        # Initialize detailed metrics tracking
        self.detailed_metrics = {
            'life_stage_distribution': defaultdict(int),
            'income_distribution': defaultdict(int),
            'wealth_distribution': defaultdict(int),
            'mobility_events': [],
            'renovation_events': [],
            'market_conditions': []
        }

    def step(self, year, month):
        # Update market conditions
        self.rental_market.update_market_conditions()
        market_conditions = self.rental_market.market_conditions

        # Update landlords and their units
        for landlord in self.landlords:
            landlord.update(market_conditions)
            landlord.update_rents(self.policy, market_conditions)

        # Update households
        for household in self.households:
            household.update_month(year, month)
            household.consider_moving(self.rental_market, self.policy, year, month)

        # Government inspects units
        for landlord in self.landlords:
            for unit in landlord.units:
                if unit.occupied and random.random() < self.policy.inspection_rate:
                    self.policy.inspect(unit)

        # Landlords collect rent
        for landlord in self.landlords:
            landlord.collect_rent()

        # Record detailed metrics
        self._record_detailed_metrics(year, month)
    
        # Record basic metrics
        self._record_basic_metrics(year, month)

    def _record_detailed_metrics(self, year, month):
        # Record life stage distribution
        life_stages = defaultdict(int)
        for h in self.households:
            life_stages[h.life_stage] += 1
        self.detailed_metrics['life_stage_distribution'][f"{year}-{month:02}"] = dict(life_stages)

        # Record income distribution
        income_bins = [0, 1000, 2000, 3000, 4000, float('inf')]
        income_dist = defaultdict(int)
        for h in self.households:
            for i in range(len(income_bins)-1):
                if income_bins[i] <= h.income < income_bins[i+1]:
                    income_dist[f"{income_bins[i]}-{income_bins[i+1]}"] += 1
                    break
        self.detailed_metrics['income_distribution'][f"{year}-{month:02}"] = dict(income_dist)

        # Record wealth distribution
        wealth_bins = [0, 5000, 10000, 20000, 50000, float('inf')]
        wealth_dist = defaultdict(int)
        for h in self.households:
            for i in range(len(wealth_bins)-1):
                if wealth_bins[i] <= h.wealth < wealth_bins[i+1]:
                    wealth_dist[f"{wealth_bins[i]}-{wealth_bins[i+1]}"] += 1
                    break
        self.detailed_metrics['wealth_distribution'][f"{year}-{month:02}"] = dict(wealth_dist)

        # Record market conditions
        self.detailed_metrics['market_conditions'].append({
            'year': year,
            'month': month,
            'conditions': self.rental_market.market_conditions.copy()
        })

    def _record_basic_metrics(self, year, month):
        # Calculate basic metrics
        housed = sum(h.housed for h in self.households)
        avg_burden = sum(h.current_rent_burden() or 0 for h in self.households if h.housed) / housed if housed else 0
        avg_satisfaction = sum(h.satisfaction for h in self.households) / len(self.households)
        total_profit = sum(l.total_profit for l in self.landlords)
        
        # Calculate additional metrics
        avg_income = np.mean([h.income for h in self.households])
        avg_wealth = np.mean([h.wealth for h in self.households])
        avg_quality = np.mean([u.quality for u in self.rental_market.units])
        avg_rent = np.mean([u.rent for u in self.rental_market.units])
        vacancy_rate = len([u for u in self.rental_market.units if not u.occupied]) / len(self.rental_market.units)
        
        # Calculate mobility metrics
        mobility_rate = sum(1 for h in self.households if h.months_in_current_unit == 0) / len(self.households)
        
        # Calculate renovation metrics
        renovation_count = sum(1 for u in self.rental_market.units if u.last_renovation == 0)

        self.metrics.append({
            "year": year,
            "month": month,
            "housed": housed,
            "avg_burden": avg_burden,
            "satisfaction": avg_satisfaction,
            "profit": total_profit,
            "violations": self.policy.violations_found,
            "avg_income": avg_income,
            "avg_wealth": avg_wealth,
            "avg_quality": avg_quality,
            "avg_rent": avg_rent,
            "vacancy_rate": vacancy_rate,
            "mobility_rate": mobility_rate,
            "renovation_count": renovation_count
        })

    def run(self):
        for year in range(1, self.years + 1):
            for month in range(1, 13):
                self.step(year, month)

    def report(self):
        # Print basic metrics
        print("\nBasic Metrics:")
        for m in self.metrics:
            print(f"{m['year']:>4}-{m['month']:>02} | "
                  f"Housed: {m['housed']:>3} | "
                  f"Burden: {m['avg_burden']:.2f} | "
                  f"Satisfaction: {m['satisfaction']:.2f} | "
                  f"Profit: {m['profit']:.0f} | "
                  f"Violations: {m['violations']}")

        # Print summary statistics
        print("\nSummary Statistics:")
        final_metrics = self.metrics[-1]
        print(f"Final Average Income: ${final_metrics['avg_income']:.2f}")
        print(f"Final Average Wealth: ${final_metrics['avg_wealth']:.2f}")
        print(f"Final Average Rent: ${final_metrics['avg_rent']:.2f}")
        print(f"Final Vacancy Rate: {final_metrics['vacancy_rate']:.2%}")
        print(f"Final Mobility Rate: {final_metrics['mobility_rate']:.2%}")
        print(f"Total Renovations: {final_metrics['renovation_count']}")

        # Print life stage distribution
        print("\nFinal Life Stage Distribution:")
        life_stages = self.detailed_metrics['life_stage_distribution'][f"{self.years}-12"]
        for stage, count in life_stages.items():
            print(f"{stage}: {count} households")

    def get_detailed_metrics(self):
        return self.detailed_metrics

    def get_market_trends(self):
        return self.rental_market.get_historical_trends()
