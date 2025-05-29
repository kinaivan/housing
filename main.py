# main.py

import random, copy
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from models.household import Household, Contract
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy
from simulation.runner import Simulation
from visualization.animated_sim import export_frames

if __name__ == "__main__":
    # 1) Styling
    plt.style.use('seaborn-v0_8')
    sns.set_theme()

    # 2) Build initial population & housing stock
    random.seed(123)
    
    # Create exactly 100 households
    base_households = []
    for i in range(100):
        age = max(18, min(85, random.normalvariate(45, 15)))
        if age < 30:       size = random.randint(1,2)
        elif age < 45:     size = random.randint(2,4)
        else:              size = random.randint(1,3)
        income = random.randint(1000,3000)
        wealth = random.randint(0,10000)
        base_households.append(
            Household(id=i, age=age, size=size, income=income, wealth=wealth)
        )

    # Create exactly 100 rental units (no owner-occupied units)
    base_units = []
    for i in range(100):
        quality = random.uniform(0.3,0.9)
        base_rent = random.randint(500,1500)
        base_units.append(
            RentalUnit(id=i, quality=quality, base_rent=base_rent)
        )

    # Set up initial occupancy: 91 occupied units, 9 empty, 92 housed households, 8 unhoused
    occupied_units = random.sample(base_units, 91)
    empty_units = [u for u in base_units if u not in occupied_units]
    
    # House 92 households in 91 units (1 unit will have 2 households sharing)
    housed_households = random.sample(base_households, 92)
    unhoused_households = [h for h in base_households if h not in housed_households]
    
    # Assign households to units
    households_assigned = 0
    shared_unit_assigned = False
    
    for i, unit in enumerate(occupied_units):
        if households_assigned < len(housed_households):
            # Assign first household
            hh1 = housed_households[households_assigned]
            unit.assign(hh1)
            hh1.contract = Contract(hh1, unit)
            hh1.housed = True
            hh1.calculate_satisfaction()
            households_assigned += 1
            
            # For one random unit, add a second household (sharing)
            if (not shared_unit_assigned and 
                households_assigned < len(housed_households) and 
                random.random() < 0.5):  # 50% chance this will be the sharing unit
                hh2 = housed_households[households_assigned]
                unit.add_tenant(hh2)
                hh2.contract = Contract(hh2, unit)
                hh2.housed = True
                hh2.calculate_satisfaction()
                households_assigned += 1
                shared_unit_assigned = True
    
    # Verify we have the right numbers
    total_housed = sum(1 for h in base_households if h.housed)
    total_unhoused = len([h for h in base_households if not h.housed])
    total_occupied = len([u for u in base_units if u.occupied])
    total_empty = len([u for u in base_units if not u.occupied])
    
    print(f"Initial setup verification:")
    print(f"  Housed households: {total_housed}")
    print(f"  Unhoused households: {total_unhoused}")
    print(f"  Occupied units: {total_occupied}")
    print(f"  Empty units: {total_empty}")
    print(f"  Total households: {len(base_households)}")
    print(f"  Total units: {len(base_units)}")

    # Create landlords for all units (all are rental now)
    def make_landlords(units, compliant_rate=0.7):
        L = []
        n_landlords = len(units)//10
        for j in range(n_landlords):
            chunk = units[j*10:(j+1)*10]
            L.append(
                Landlord(
                    id=j,
                    units=chunk,
                    is_compliant=(random.random() < compliant_rate)
                )
            )
        return L

    # 4) Scenario A: With Rent Cap
    hh_cap = copy.deepcopy(base_households)
    u_cap  = copy.deepcopy(base_units)
    ll_cap = make_landlords(u_cap)
    market_cap = RentalMarket(u_cap)
    policy_cap = RentCapPolicy(
        rent_cap_ratio=0.3,
        max_increase_rate=0.05,
        inspection_rate=0.1
    )
    sim_cap = Simulation(hh_cap, ll_cap, market_cap, policy_cap, years=10)
    sim_cap.run()

    # 5) Scenario B: No Rent Cap
    hh_nocap = copy.deepcopy(base_households)
    u_nocap  = copy.deepcopy(base_units)
    ll_nocap = make_landlords(u_nocap)
    market_nocap = RentalMarket(u_nocap)
    policy_nocap = RentCapPolicy(
        rent_cap_ratio=1.0,    # effectively unlimited
        max_increase_rate=0.2,
        inspection_rate=0.0
    )
    sim_nocap = Simulation(hh_nocap, ll_nocap, market_nocap, policy_nocap, years=10)
    sim_nocap.run()

    # 6) Extract time-series & final stock stats
    periods = [f"Year {m['year']}, Period {m['period']}" for m in sim_cap.metrics]
    sat_cap = [m['satisfaction'] for m in sim_cap.metrics]
    sat_nocap = [m['satisfaction'] for m in sim_nocap.metrics]
    vac_cap = [m['vacancy_rate'] for m in sim_cap.metrics]
    vac_nocap = [m['vacancy_rate'] for m in sim_nocap.metrics]
    rents_cap = [u.rent for u in u_cap]
    rents_nocap = [u.rent for u in u_nocap]

    # 7) Make a 3×2 panel with adjusted x-axis for longer timeline
    fig, axs = plt.subplots(3,2,figsize=(16,12))
    fig.suptitle("Housing Market: Rent-Cap vs No-Cap (10 Year Simulation)", fontsize=16)

    # (1) Satisfaction
    ax = axs[0,0]
    ax.plot(periods, sat_cap,   label="With Cap", lw=2)
    ax.plot(periods, sat_nocap, label="No Cap",   lw=2)
    ax.set_title("Tenant Satisfaction")
    ax.set_ylabel("Satisfaction")
    ax.set_xticks(periods[::4])  # Show every 2 years
    ax.set_xticklabels(periods[::4], rotation=45)
    ax.legend(); ax.grid(alpha=0.3)

    # (2) Rent distribution
    ax = axs[0,1]
    sns.kdeplot(rents_cap,   ax=ax, label="With Cap",   fill=True, alpha=0.4)
    sns.kdeplot(rents_nocap, ax=ax, label="No Cap",     fill=True, alpha=0.4)
    ax.set_title("Rent Distribution"); ax.legend()

    # (3) Vacancy over time
    ax = axs[1,0]
    ax.plot(periods, vac_cap,   label="With Cap", lw=2)
    ax.plot(periods, vac_nocap, label="No Cap",   lw=2)
    ax.set_title("Vacancy Rate")
    ax.set_ylabel("Vacancy")
    ax.set_xticks(periods[::4])  # Show every 2 years
    ax.set_xticklabels(periods[::4], rotation=45)
    ax.legend(); ax.grid(alpha=0.3)

    # (4) Market stats (scaled)
    stats = ['average_rent','vacancy_rate','market_demand']
    x = np.arange(len(stats)); w=0.3
    sc = market_cap.get_market_statistics()
    sn = market_nocap.get_market_statistics()
    cap_vals = [ sc['average_rent'],
                sc['vacancy_rate']*1e4,
                sc['market_demand']*1e4 ]
    noc_vals= [ sn['average_rent'],
                sn['vacancy_rate']*1e4,
                sn['market_demand']*1e4 ]
    ax = axs[1,1]
    ax.bar(x-w/2, cap_vals,   w, label="With Cap")
    ax.bar(x+w/2, noc_vals,   w, label="No Cap")
    ax.set_xticks(x)
    ax.set_xticklabels(['AvgRent','Vac×1e4','Dem×1e4'])
    ax.set_title("Market Stats"); ax.legend()

    # (5) Location premium
    caps = market_cap.market_conditions['location_premiums']
    noc  = market_nocap.market_conditions['location_premiums']
    locs = sorted(set(caps)|set(noc))
    pc   = [caps.get(l,0) for l in locs]
    pnc  = [noc.get(l,0) for l in locs]
    ax = axs[2,0]
    ax.plot(locs, pc,  'o-', label="With Cap")
    ax.plot(locs, pnc, 'o-', label="No Cap")
    ax.set_title("Location Premiums"); ax.legend()

    # (6) blank
    axs[2,1].axis('off')

    plt.tight_layout(rect=[0,0.03,1,0.95])
    # plt.show()  # Skip showing matplotlib plots, we only need the frame exports

    # 8) Print a neat summary
    print("\nSummary Statistics:")
    print(f"Avg Satisfaction → Cap: {np.mean(sat_cap):.3f}   NoCap: {np.mean(sat_nocap):.3f}")
    print(f"Avg Rent         → Cap: ${np.mean(rents_cap):.2f}  NoCap: ${np.mean(rents_nocap):.2f}")
    print(f"Avg Vacancy      → Cap: {np.mean(vac_cap):.3f}       NoCap: {np.mean(vac_nocap):.3f}")
    print(f"Final Profit     → Cap: {sim_cap.metrics[-1]['profit']:.0f}   NoCap: {sim_nocap.metrics[-1]['profit']:.0f}")
    print(f"Total Violations → Cap: {sim_cap.metrics[-1]['violations']}   NoCap: {sim_nocap.metrics[-1]['violations']}")

    # Export simulation frames for Dash app
    export_frames(sim_cap, 'frames_cap.pkl')
    export_frames(sim_nocap, 'frames_nocap.pkl')