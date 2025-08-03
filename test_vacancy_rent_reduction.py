#!/usr/bin/env python3
"""
Test script to demonstrate the new vacancy-based rent reduction feature.
This script shows how landlords now reduce rent for vacant units to attract tenants.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy

def test_vacancy_rent_reduction():
    """Test the vacancy-based rent reduction feature"""
    print("=== Testing Vacancy-Based Rent Reduction Feature ===\n")
    
    # Create test units
    units = [
        RentalUnit(id=1, quality=0.8, base_rent=1200, size=2, location=0.7),
        RentalUnit(id=2, quality=0.6, base_rent=1000, size=1, location=0.5),
        RentalUnit(id=3, quality=0.9, base_rent=1500, size=3, location=0.8),
    ]
    
    # Create landlords
    landlord1 = Landlord(id=1, units=[units[0], units[1]], is_compliant=True)
    landlord2 = Landlord(id=2, units=[units[2]], is_compliant=False)
    
    # Create market
    market = RentalMarket(units)
    
    # Create a simple policy
    policy = RentCapPolicy()  # Uses default 10% max increase
    
    print("Initial state:")
    for unit in units:
        print(f"Unit {unit.id}: Rent=${unit.rent:.0f}, Quality={unit.quality:.1f}, Occupied={unit.occupied}")
    print()
    
    # Simulate units becoming vacant
    print("Making all units vacant...")
    for unit in units:
        unit.vacate()
    
    print("After making units vacant:")
    for unit in units:
        print(f"Unit {unit.id}: Rent=${unit.rent:.0f}, Vacancy Duration={unit.vacancy_duration}")
    print()
    
    # Simulate several periods of vacancy with rent reductions
    print("Simulating 8 periods (4 years) of vacancy with rent reductions:")
    print("Period | Unit 1 Rent | Unit 2 Rent | Unit 3 Rent | Market Demand")
    print("-" * 65)
    
    for period in range(8):
        # Update market conditions
        market.update_market_conditions()
        
        # Update landlord rent strategies
        landlord1.update_rents(policy, market.market_conditions)
        landlord2.update_rents(policy, market.market_conditions)
        
        # Print current state
        market_demand = market.market_conditions['market_demand']
        print(f"  {period+1:2d}   | ${units[0].rent:8.0f} | ${units[1].rent:8.0f} | ${units[2].rent:8.0f} | {market_demand:.2f}")
    
    print()
    
    # Show rent reduction history for one unit
    print("Rent reduction history for Unit 1:")
    if hasattr(units[0], 'rent_reduction_history'):
        for entry in units[0].rent_reduction_history:
            print(f"  Period {entry['period']}: ${entry['old_rent']:.0f} → ${entry['new_rent']:.0f} "
                  f"(Reduction: {entry['reduction_factor']:.1%}) - {entry['reason']}")
    
    print()
    
    # Test what happens when a unit gets occupied
    print("Testing rent restoration when Unit 1 gets occupied...")
    from models.household import Household
    
    # Create a test household
    household = Household(id=999, age=30, size=2, income=3000, wealth=5000)
    
    # Assign household to unit
    units[0].assign(household)
    
    print(f"After occupation: Unit 1 rent = ${units[0].rent:.0f}")
    print(f"Unit 1 occupied: {units[0].occupied}")
    print(f"Unit 1 vacancy duration: {units[0].vacancy_duration}")
    
    print()
    
    # Show landlord portfolio statistics
    print("Landlord 1 Portfolio Statistics:")
    stats = landlord1.get_portfolio_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_vacancy_rent_reduction() 