from simulation.runner import Simulation
from models.household import Household
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy
import copy

class RealtimeSimulation:
    def __init__(self, households, landlords, rental_market, policy, years=1):
        # Create initial simulation
        self.initial_households = households
        self.initial_landlords = landlords
        self.initial_rental_market = rental_market
        self.initial_policy = policy
        self.years = years
        
        # Initialize simulation with shallow copies
        self.simulation = Simulation(
            list(households),  # shallow copy
            list(landlords),   # shallow copy
            rental_market,     # no need to copy
            policy,           # no need to copy
            years
        )
        self.current_year = 1
        self.current_period = 1
        self.total_periods = years * 12
        self.current_frame = 0
        self.frames = []
        self.unhoused_data = []
        self.unhoused_households = []
        
        # Pre-compute initial state
        self._compute_current_state()
        
    def _compute_current_state(self):
        """Helper to compute and store current simulation state"""
        self.unhoused_households = [h for h in self.simulation.households if not h.housed and h.size > 0]
        current_state = {
            'year': self.current_year,
            'period': self.current_period,
            'metrics': self.simulation.metrics[-1] if self.simulation.metrics else {},
            'occupancy': self.simulation.occupancy_history[-1] if self.simulation.occupancy_history else {},
            'unhoused': len(self.unhoused_households),
            'unhoused_households': self.unhoused_households,
            'units': self.simulation.rental_market.units,
            'households': self.simulation.households,
            'moves': getattr(self.simulation, 'moves_this_period', []),
            'events': getattr(self.simulation, 'events_this_period', [])
        }
        self.frames.append(current_state)
        self.unhoused_data.append(current_state['unhoused'])
        return current_state

    def step(self):
        """Execute one step of the simulation and return the current state"""
        if self.current_year > self.simulation.years:
            return None
            
        # Run one step of the simulation
        self.simulation.step(self.current_year, self.current_period)
        
        # Update state and counters
        self.current_frame += 1
        
        # Increment period (each step represents 6 months)
        if self.current_period == 1:
            self.current_period = 2  # First 6 months -> Second 6 months
        else:
            self.current_period = 1  # Second 6 months -> Next year, first 6 months
            self.current_year += 1
        
        return self._compute_current_state()
        
    def get_current_state(self):
        """Get the current state of the simulation"""
        if not self.frames:
            return None
        return self.frames[-1]
        
    def get_frame(self, frame_idx):
        """Get a specific frame from the simulation history"""
        if 0 <= frame_idx < len(self.frames):
            return self.frames[frame_idx]
        return None
        
    def get_all_frames(self):
        """Get all frames from the simulation history"""
        return self.frames
        
    def get_unhoused_data(self):
        """Get the history of unhoused households"""
        return self.unhoused_data
        
    def reset(self):
        """Reset the simulation to its initial state"""
        self.current_year = 1
        self.current_period = 1
        self.current_frame = 0
        self.frames = []
        self.unhoused_data = []
        self.unhoused_households = []
        
        # Reset using stored initial values with shallow copies
        self.simulation = Simulation(
            list(self.initial_households),  # shallow copy
            list(self.initial_landlords),   # shallow copy
            self.initial_rental_market,     # reuse original
            self.initial_policy,            # reuse original
            self.years
        )
        
        # Pre-compute initial state
        self._compute_current_state()
