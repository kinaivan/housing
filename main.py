if __name__ == "__main__":
    from models.household import Household
    from models.unit import RentalUnit, Landlord
    from models.market import RentalMarket
    from models.policy import RentCapPolicy
    from simulation.runner import Simulation
    import matplotlib.pyplot as plt
    import random, copy

    # Create base agents
    base_households = [Household(id=i, age=random.randint(25, 65), size=1,
                                  income=random.randint(1000, 3000), wealth=0) for i in range(250)]
    base_units = [RentalUnit(id=i, quality=random.uniform(0.5, 1.0),
                             base_rent=random.randint(300, 900)) for i in range(100)]

    # Deep copy for both scenarios
    households_with_cap = copy.deepcopy(base_households)
    units_with_cap = copy.deepcopy(base_units)
    households_no_cap = copy.deepcopy(base_households)
    units_no_cap = copy.deepcopy(base_units)

    # With rent cap
    market_cap = RentalMarket(units_with_cap)
    policy_cap = RentCapPolicy(rent_cap_ratio=0.3, max_increase_rate=0.05, inspection_rate=0.1)
    landlord_cap = Landlord(id=0, units=units_with_cap, is_compliant=True)
    sim_cap = Simulation(households_with_cap, [landlord_cap], market_cap, policy_cap, years=2)
    sim_cap.run()
    sim_cap.report()
    print("-" * 40)

    # No rent cap (greedy, uncapped)
    market_nocap = RentalMarket(units_no_cap)
    policy_nocap = RentCapPolicy(rent_cap_ratio=1.0, max_increase_rate=0.05, inspection_rate=0.1)
    landlord_nocap = Landlord(id=1, units=units_no_cap, is_compliant=True)  # Still compliant, just no cap to obey
    sim_nocap = Simulation(households_no_cap, [landlord_nocap], market_nocap, policy_nocap, years=2)
    sim_nocap.run()
    sim_nocap.report()

    # Plot satisfaction comparison
    months = [f"{m['year']}-{m['month']:02}" for m in sim_cap.metrics]
    satisfaction_cap = [m['satisfaction'] for m in sim_cap.metrics]
    satisfaction_nocap = [m['satisfaction'] for m in sim_nocap.metrics]

    plt.figure(figsize=(10, 5))
    plt.plot(months, satisfaction_cap, label="With Rent Cap")
    plt.plot(months, satisfaction_nocap, label="No Rent Cap")
    plt.xticks(rotation=45)
    plt.ylabel("Average Satisfaction")
    plt.xlabel("Month")
    plt.title("Tenant Satisfaction: Rent Cap vs No Cap")
    plt.legend()
    plt.tight_layout()
    plt.show()