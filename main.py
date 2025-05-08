if __name__ == "__main__":
    from models.household import Household
    from models.unit import RentalUnit, Landlord
    from models.market import RentalMarket
    from models.policy import RentCapPolicy
    from simulation.runner import Simulation
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    import numpy as np
    import random, copy

    # Set style for better visualizations
    plt.style.use('seaborn-v0_8')
    sns.set_theme()

    # Create base agents with more diverse characteristics
    households = []
    for i in range(100):
        # More realistic age distribution
        age = random.normalvariate(45, 15)  # Mean age 45, std dev 15
        age = max(18, min(85, age))  # Bound between 18 and 85
        
        # Size based on age
        if age < 30:
            size = random.randint(1, 2)
        elif age < 45:
            size = random.randint(2, 4)
        else:
            size = random.randint(1, 3)
        
        households.append(Household(
            id=i,
            age=age,
            size=size,
            income=random.randint(1000, 3000),
            wealth=random.randint(0, 10000)
        ))

    # Create rental units with more diverse characteristics
    units = []
    for i in range(100):
        quality = random.uniform(0.3, 0.9)
        base_rent = random.randint(500, 1500)
        units.append(RentalUnit(
            id=i,
            quality=quality,
            base_rent=base_rent
        ))

    # Create landlords with varying compliance rates
    landlords = []
    for i in range(10):
        landlord_units = units[i*10:(i+1)*10]
        is_compliant = random.random() < 0.7  # 70% of landlords are compliant
        landlords.append(Landlord(
            id=i,
            units=landlord_units,
            is_compliant=is_compliant
        ))

    # Create rental market
    market_with_cap = RentalMarket(units)

    # Create rent control policy
    policy_with_cap = RentCapPolicy(
        rent_cap_ratio=0.3,  # 30% of income
        max_increase_rate=0.05,  # 5% max increase per year
        inspection_rate=0.1  # 10% of units inspected per year
    )

    # Create no-cap policy (effectively no restrictions)
    policy_no_cap = RentCapPolicy(
        rent_cap_ratio=1.0,  # 100% of income (effectively no cap)
        max_increase_rate=0.2,  # 20% max increase per year (more realistic for unregulated market)
        inspection_rate=0.0  # No inspections in unregulated market
    )

    # Run simulation with rent control
    simulation_with_cap = Simulation(households, landlords, market_with_cap, policy_with_cap, 2)
    simulation_with_cap.run()

    # Reset and run without rent control
    households_no_cap = [copy.deepcopy(h) for h in households]
    units_no_cap = [copy.deepcopy(u) for u in units]
    landlords_no_cap = [copy.deepcopy(l) for l in landlords]
    market_no_cap = RentalMarket(units_no_cap)
    simulation_without_cap = Simulation(households_no_cap, landlords_no_cap, market_no_cap, policy_no_cap, 2)
    simulation_without_cap.run()

    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(3, 2)

    # 1. Satisfaction Comparison
    ax1 = fig.add_subplot(gs[0, :])
    months = [f"{m['year']}-{m['month']:02}" for m in simulation_with_cap.metrics]
    satisfaction_cap = [m['satisfaction'] for m in simulation_with_cap.metrics]
    satisfaction_nocap = [m['satisfaction'] for m in simulation_without_cap.metrics]

    ax1.plot(months, satisfaction_cap, label="With Rent Cap", linewidth=2)
    ax1.plot(months, satisfaction_nocap, label="No Rent Cap", linewidth=2)
    ax1.set_xticks(ax1.get_xticks()[::3])  # Show every third tick
    ax1.set_ylabel("Average Satisfaction")
    ax1.set_title("Tenant Satisfaction: Rent Cap vs No Cap")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Rent Distribution
    ax2 = fig.add_subplot(gs[1, 0])
    rents_cap = [u.rent for u in units]
    rents_nocap = [u.rent for u in units_no_cap]

    sns.kdeplot(data=rents_cap, ax=ax2, label="With Rent Cap", fill=True, alpha=0.3)
    sns.kdeplot(data=rents_nocap, ax=ax2, label="No Rent Cap", fill=True, alpha=0.3)
    ax2.set_xlabel("Rent")
    ax2.set_ylabel("Density")
    ax2.set_title("Rent Distribution")
    ax2.legend()

    # 3. Vacancy Rates
    ax3 = fig.add_subplot(gs[1, 1])
    vacancy_cap = [m['vacancy_rate'] for m in simulation_with_cap.metrics]
    vacancy_nocap = [m['vacancy_rate'] for m in simulation_without_cap.metrics]

    ax3.plot(months, vacancy_cap, label="With Rent Cap", linewidth=2)
    ax3.plot(months, vacancy_nocap, label="No Rent Cap", linewidth=2)
    ax3.set_xticks(ax3.get_xticks()[::3])
    ax3.set_ylabel("Vacancy Rate")
    ax3.set_title("Vacancy Rates Over Time")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Market Statistics
    ax4 = fig.add_subplot(gs[2, 0])
    market_stats_cap = market_with_cap.get_market_statistics()
    market_stats_nocap = market_no_cap.get_market_statistics()

    stats = ['average_rent', 'vacancy_rate', 'market_demand']
    x = np.arange(len(stats))
    width = 0.35

    ax4.bar(x - width/2, [market_stats_cap[s] for s in stats], width, label='With Rent Cap')
    ax4.bar(x + width/2, [market_stats_nocap[s] for s in stats], width, label='No Rent Cap')
    ax4.set_ylabel('Value')
    ax4.set_title('Market Statistics Comparison')
    ax4.set_xticks(x)
    ax4.set_xticklabels(['Avg Rent', 'Vacancy', 'Demand'])
    ax4.legend()

    # 5. Location Premium Analysis
    ax5 = fig.add_subplot(gs[2, 1])
    location_premiums_cap = market_with_cap.market_conditions['location_premiums']
    location_premiums_nocap = market_no_cap.market_conditions['location_premiums']

    locations = sorted(set(list(location_premiums_cap.keys()) + list(location_premiums_nocap.keys())))
    premiums_cap = [location_premiums_cap.get(loc, 0) for loc in locations]
    premiums_nocap = [location_premiums_nocap.get(loc, 0) for loc in locations]

    ax5.plot(locations, premiums_cap, 'o-', label='With Rent Cap')
    ax5.plot(locations, premiums_nocap, 'o-', label='No Rent Cap')
    ax5.set_xlabel('Location (0=Suburban, 1=Central)')
    ax5.set_ylabel('Rent Premium')
    ax5.set_title('Location Premium Analysis')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Average Satisfaction (With Cap): {np.mean(satisfaction_cap):.3f}")
    print(f"Average Satisfaction (No Cap): {np.mean(satisfaction_nocap):.3f}")
    print(f"Average Rent (With Cap): ${np.mean(rents_cap):.2f}")
    print(f"Average Rent (No Cap): ${np.mean(rents_nocap):.2f}")
    print(f"Average Vacancy Rate (With Cap): {np.mean(vacancy_cap):.3f}")
    print(f"Average Vacancy Rate (No Cap): {np.mean(vacancy_nocap):.3f}")