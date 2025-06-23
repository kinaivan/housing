from dash import Output, Input, State, callback_context, no_update, html
from app.utils.visualization import make_figure
from simulation.realtime_sim import RealtimeSimulation
from models.household import Household
from models.unit import RentalUnit, Landlord
from models.market import RentalMarket
from models.policy import RentCapPolicy
import random
import math

def create_household(id):
    """Create a household with realistic size distribution"""
    age = random.randint(25, 60)
    # Size distribution based on age
    if age < 30:
        size = random.choices([1, 2], weights=[70, 30])[0]
    elif age < 45:
        size = random.choices([1, 2, 3, 4], weights=[20, 40, 25, 15])[0]
    else:
        size = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
    return Household(id=id, age=age, size=size, income=2500, wealth=10000)

def initialize_simulation(initial_households=20, migration_rate=0.1):
    """Initialize a new simulation with given parameters"""
    households = [create_household(i) for i in range(initial_households)]
    landlords = [Landlord(id=0, units=[])]
    units = [RentalUnit(id=i, quality=1.0, base_rent=1200) for i in range(20)]
    landlords[0].units = units
    rental_market = RentalMarket(units=units)
    policy = RentCapPolicy()
    sim = RealtimeSimulation(households, landlords, rental_market, policy, years=10)
    setattr(sim, 'migration_rate', migration_rate)
    sim.last_initial_households = initial_households
    sim.last_migration_rate = migration_rate
    return sim

# Initialize default simulation
sim = initialize_simulation()
prev_frame = None

# Add default button styles
default_button_style = {
    'padding': '10px 20px',
    'border': 'none',
    'borderRadius': '5px',
    'cursor': 'pointer',
    'marginRight': '10px',
    'transition': 'all 0.3s ease',
    'width': '100px',
}

default_play_style = {
    **default_button_style,
    'backgroundColor': '#28a745',
    'color': 'white',
}

default_pause_style = {
    **default_button_style,
    'backgroundColor': '#dc3545',
    'color': 'white',
}

default_reset_style = {
    **default_button_style,
    'backgroundColor': '#6c757d',
    'color': 'white',
    'marginRight': '0'
}

def create_sidebar_stats(current_state, sim):
    if current_state is None:
        return "No data available"
    total_units = len(current_state['units'])
    occupied_units = sum(1 for unit in current_state['units'] if unit.occupied)
    owner_occupied = sum(1 for unit in current_state['units'] if getattr(unit, 'landlord', None) is None and unit.occupied)
    rented_units = sum(1 for unit in current_state['units'] if getattr(unit, 'landlord', None) is not None and unit.occupied)
    vacant_units = total_units - occupied_units
    unhoused = current_state['unhoused']
    rents = [unit.rent for unit in current_state['units'] if getattr(unit, 'landlord', None) is not None and unit.occupied]
    avg_rent = sum(rents) / len(rents) if rents else 0
    median_rent = sorted(rents)[len(rents)//2] if rents else 0
    occupancy_rate = (occupied_units / total_units) * 100 if total_units else 0
    all_incomes = [h.income for h in current_state.get('households', [])]
    rent_to_income = (avg_rent / (sum(all_incomes)/len(all_incomes))) * 100 if all_incomes and avg_rent else 0
    return [
        html.Div([
            html.H4("Market Statistics"),
            html.P(f"Total Units: {total_units}"),
            html.P(f"Owner-Occupied: {owner_occupied}"),
            html.P(f"Rented: {rented_units}"),
            html.P(f"Vacant: {vacant_units}"),
            html.P(f"Unhoused: {unhoused}"),
            html.P(f"Average Rent: €{avg_rent:.2f}"),
            html.P(f"Median Rent: €{median_rent:.2f}"),
            html.P(f"Occupancy Rate: {occupancy_rate:.1f}%"),
            html.P(f"Rent-to-Income Ratio: {rent_to_income:.1f}%")
        ])
    ]

def create_movement_log(current_state):
    if current_state is None:
        return "No movement data available"
    movement_logs = []
    for h in current_state.get('households', []):
        for event in getattr(h, 'timeline', []):
            info = event.record
            if info.get('type') == 'MOVED_IN':
                movement_logs.append(f"Household {h.id} moved in to unit {info.get('unit_id', '?')}")
            elif info.get('type') == 'EVICTED':
                movement_logs.append(f"Household {h.id} was evicted from unit {info.get('unit_id', '?')}")
            elif info.get('type') == 'HOUSEHOLD_BREAKUP':
                movement_logs.append(f"Household {h.id} broke up")
            elif info.get('type') == 'HOUSEHOLD_MERGER':
                movement_logs.append(f"Household {h.id} merged with another household")
            elif info.get('type') == 'APARTMENT_SHARING':
                movement_logs.append(f"Household {h.id} started apartment sharing")
    movement_logs = movement_logs[-10:]
    return [html.Div([html.Div(m, style={'margin': '5px 0'}) for m in movement_logs])]

def register_simulation_callbacks(app):
    @app.callback(
        [
            Output('auto-stepper', 'disabled'),
            Output('auto-stepper', 'n_intervals'),
            Output('sim-graph', 'figure'),
            Output('sidebar-stats', 'children'),
            Output('movement-log', 'children'),
            Output('period-slider', 'value'),
            Output('simulation-status', 'children'),
            Output('simulation-status', 'style'),
            Output('play-button', 'style'),
            Output('pause-button', 'style'),
            Output('reset-button', 'style')
        ],
        [
            Input('auto-stepper', 'n_intervals'),
            Input('play-button', 'n_clicks'),
            Input('pause-button', 'n_clicks'),
            Input('reset-button', 'n_clicks'),
            Input('initial-households-input', 'value'),
            Input('migration-rate-slider', 'value'),
            Input('scenario-selector', 'value')
        ],
        [
            State('period-slider', 'value'),
            State('play-button', 'style'),
            State('pause-button', 'style'),
            State('reset-button', 'style'),
            State('auto-stepper', 'disabled')
        ],
        prevent_initial_call=True
    )
    def update_simulation(n_intervals, play, pause, reset, initial_households, migration_rate, scenario, 
                         period_value, play_style, pause_style, reset_style, is_paused):
        global sim, prev_frame
        
        # Base styles for status and buttons
        status_base_style = {
            'textAlign': 'center',
            'marginBottom': '20px',
            'padding': '10px',
            'borderRadius': '5px',
            'fontWeight': 'bold'
        }
        
        # Initialize button styles if they're None
        play_style = play_style or default_play_style.copy()
        pause_style = pause_style or default_pause_style.copy()
        reset_style = reset_style or default_reset_style.copy()
        
        try:
            ctx = callback_context
            if not ctx.triggered:
                if sim is None:
                    sim = initialize_simulation()
                frame = sim.get_current_state()
                if frame:
                    fig = make_figure(frame, grid_size=None, prev_frame=None, is_cap_scenario=True)
                    stats = create_sidebar_stats(frame, sim)
                    log_divs = create_movement_log(frame)
                    return True, 0, fig, stats, log_divs, 0, "Simulation Ready", \
                           {**status_base_style, 'backgroundColor': '#e9ecef'}, \
                           play_style, pause_style, reset_style
                return True, 0, no_update, no_update, no_update, 0, "Simulation Ready", \
                       {**status_base_style, 'backgroundColor': '#e9ecef'}, \
                       play_style, pause_style, reset_style

            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # Initialize parameters with safe defaults
            init_hh = initial_households if initial_households and initial_households > 0 else 20
            mig_rate = migration_rate if migration_rate is not None else 0.1
            is_cap_scenario = scenario == 'capped' if scenario is not None else True
            period_value = period_value if period_value is not None else 0
            n_intervals = n_intervals if n_intervals is not None else 0
            
            # Function to get current state and visualization
            def get_current_visualization():
                global prev_frame
                frame = sim.get_current_state()
                if frame is None:
                    return no_update, no_update, no_update
                try:
                    fig = make_figure(frame, grid_size=None, prev_frame=prev_frame, is_cap_scenario=is_cap_scenario)
                    stats = create_sidebar_stats(frame, sim)
                    log_divs = create_movement_log(frame)
                    prev_frame = frame  # Update prev_frame after successful visualization
                    return fig, stats, log_divs
                except Exception as e:
                    print(f"Error in visualization: {str(e)}")
                    return no_update, no_update, no_update
            
            # Handle control buttons
            if triggered_id == 'play-button' and play is not None:
                # If simulation hasn't been initialized or parameters changed, reset it
                if (sim is None or 
                    getattr(sim, 'last_initial_households', None) != init_hh or 
                    getattr(sim, 'last_migration_rate', None) != mig_rate or
                    getattr(sim, 'is_cap_scenario', None) != is_cap_scenario):
                    sim = initialize_simulation(init_hh, mig_rate)
                    sim.is_cap_scenario = is_cap_scenario
                    prev_frame = None
                
                fig, stats, log_divs = get_current_visualization()
                if fig is no_update:  # If visualization failed, try without prev_frame
                    frame = sim.get_current_state()
                    if frame:
                        fig = make_figure(frame, grid_size=None, prev_frame=None, is_cap_scenario=is_cap_scenario)
                        stats = create_sidebar_stats(frame, sim)
                        log_divs = create_movement_log(frame)
                
                # Update button styles
                play_style.update({'opacity': '0.5', 'cursor': 'not-allowed'})
                pause_style.update({'opacity': '1', 'cursor': 'pointer'})
                reset_style.update({'opacity': '1', 'cursor': 'pointer'})
                
                return False, n_intervals, fig, stats, log_divs, period_value, \
                       "Simulation Running", {**status_base_style, 'backgroundColor': '#28a745', 'color': 'white'}, \
                       play_style, pause_style, reset_style
                    
            elif triggered_id == 'pause-button' and pause is not None:
                # Get current state for display during pause
                fig, stats, log_divs = get_current_visualization()
                if fig is no_update:  # If visualization failed, try without prev_frame
                    frame = sim.get_current_state()
                    if frame:
                        fig = make_figure(frame, grid_size=None, prev_frame=None, is_cap_scenario=is_cap_scenario)
                        stats = create_sidebar_stats(frame, sim)
                        log_divs = create_movement_log(frame)
                
                # Update button styles
                play_style.update({'opacity': '1', 'cursor': 'pointer'})
                pause_style.update({'opacity': '0.5', 'cursor': 'not-allowed'})
                reset_style.update({'opacity': '1', 'cursor': 'pointer'})
                
                return True, n_intervals, fig, stats, log_divs, period_value, \
                       "Simulation Paused", {**status_base_style, 'backgroundColor': '#dc3545', 'color': 'white'}, \
                       play_style, pause_style, reset_style
                    
            elif triggered_id == 'reset-button' and reset is not None:
                # Reset simulation state with current parameters
                sim = initialize_simulation(init_hh, mig_rate)
                sim.is_cap_scenario = is_cap_scenario
                prev_frame = None
                
                # Get initial visualization
                frame = sim.get_current_state()
                fig = make_figure(frame, grid_size=None, prev_frame=None, is_cap_scenario=is_cap_scenario)
                stats = create_sidebar_stats(frame, sim)
                log_divs = create_movement_log(frame)
                
                # Update button styles
                play_style.update({'opacity': '1', 'cursor': 'pointer'})
                pause_style.update({'opacity': '1', 'cursor': 'pointer'})
                reset_style.update({'opacity': '0.5', 'cursor': 'not-allowed'})
                
                return True, 0, fig, stats, log_divs, 0, \
                       "Simulation Reset", {**status_base_style, 'backgroundColor': '#6c757d', 'color': 'white'}, \
                       play_style, pause_style, reset_style
            
            elif triggered_id == 'auto-stepper' and not is_paused:
                # Only step if simulation exists and no step is in progress
                if sim is not None:
                    current_state = sim.get_current_state()
                    if current_state and not current_state.get('step_in_progress', False):
                        # Step the simulation
                        new_state = sim.step()
                        if new_state is not None:
                            fig, stats, log_divs = get_current_visualization()
                            if fig is no_update:  # If visualization failed, try without prev_frame
                                fig = make_figure(new_state, grid_size=None, prev_frame=None, is_cap_scenario=is_cap_scenario)
                                stats = create_sidebar_stats(new_state, sim)
                                log_divs = create_movement_log(new_state)
                            return False, n_intervals, fig, stats, log_divs, sim.current_period - 1, \
                                   "Simulation Running", {**status_base_style, 'backgroundColor': '#28a745', 'color': 'white'}, \
                                   play_style, pause_style, reset_style
                    # If step is in progress or we couldn't step, return current state
                    fig, stats, log_divs = get_current_visualization()
                    if fig is no_update:  # If visualization failed, try without prev_frame
                        frame = sim.get_current_state()
                        if frame:
                            fig = make_figure(frame, grid_size=None, prev_frame=None, is_cap_scenario=is_cap_scenario)
                            stats = create_sidebar_stats(frame, sim)
                            log_divs = create_movement_log(frame)
                    return False, n_intervals, fig, stats, log_divs, period_value, \
                           "Processing...", {**status_base_style, 'backgroundColor': '#ffc107', 'color': 'black'}, \
                           play_style, pause_style, reset_style
                
            # Default return if no conditions met
            if sim is not None:
                frame = sim.get_current_state()
                if frame:
                    fig = make_figure(frame, grid_size=None, prev_frame=None, is_cap_scenario=is_cap_scenario)
                    stats = create_sidebar_stats(frame, sim)
                    log_divs = create_movement_log(frame)
                    return True, n_intervals, fig, stats, log_divs, period_value, \
                           "Simulation Ready", {**status_base_style, 'backgroundColor': '#e9ecef'}, \
                           play_style, pause_style, reset_style
            
            return True, n_intervals, no_update, no_update, no_update, period_value, \
                   "Simulation Ready", {**status_base_style, 'backgroundColor': '#e9ecef'}, \
                   play_style, pause_style, reset_style
                
        except Exception as e:
            print(f"Error in simulation callback: {str(e)}")
            return True, n_intervals or 0, no_update, no_update, no_update, period_value or 0, \
                   f"Error: {str(e)}", {**status_base_style, 'backgroundColor': '#dc3545', 'color': 'white'}, \
                   play_style or default_play_style, pause_style or default_pause_style, reset_style or default_reset_style 