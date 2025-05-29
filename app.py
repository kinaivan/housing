import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import numpy as np
import pickle

# --- You need to prepare your simulation data as two lists of frames: frames_cap and frames_nocap ---
# Each frame is a list of dicts for each unit, as described in previous answers.

# Example: load from pickle or generate in your main.py and save
with open('frames_cap.pkl', 'rb') as f:
    frames_cap = pickle.load(f)
with open('frames_nocap.pkl', 'rb') as f:
    frames_nocap = pickle.load(f)

# Load movement logs
with open('frames_cap_movement_logs.pkl', 'rb') as f:
    movement_logs_cap = pickle.load(f)
with open('frames_nocap_movement_logs.pkl', 'rb') as f:
    movement_logs_nocap = pickle.load(f)

# Load unhoused data
with open('frames_cap_unhoused.pkl', 'rb') as f:
    unhoused_data_cap = pickle.load(f)
with open('frames_nocap_unhoused.pkl', 'rb') as f:
    unhoused_data_nocap = pickle.load(f)

n_months = len(frames_cap)
n_units = len(frames_cap[0])
grid_size = int(np.ceil(np.sqrt(n_units)))

def get_positions(n):
    grid = []
    for i in range(n):
        row, col = divmod(i, grid_size)
        x = col
        y = grid_size - row - 1
        grid.append((x, y))
    return grid

positions = get_positions(n_units)

def make_house_shapes(frame, grid_size, is_cap_scenario):
    shapes = []
    annotations = []
    
    # First, draw all houses
    for i, u in enumerate(frame):
        row, col = divmod(i, grid_size)
        x = col
        y = grid_size - row - 1
        
        # House body
        color = (
            (0.7, 0.776, 1.0, 1.0) if u['is_owner_occupied']  # royalblue
            else (0.196, 0.804, 0.196, 1.0) if u['occupied']  # limegreen
            else (0.827, 0.827, 0.827, 1.0)  # lightgray
        )
        shapes.append(dict(
            type="rect",
            x0=x-0.2, y0=y-0.2, x1=x+0.2, y1=y+0.2,
            line=dict(color="black", width=2),
            fillcolor=f"rgba({int(color[0]*255)},{int(color[1]*255)},{int(color[2]*255)},{color[3]})",
            layer="below"
        ))
        # Roof (triangle)
        shapes.append(dict(
            type="path",
            path=f'M {x-0.22},{y+0.2} L{x},{y+0.4} L{x+0.22},{y+0.2} Z',
            line=dict(color="black", width=2),
            fillcolor="rgba(217,95,2,1.0)",  # #d95f02
            layer="below"
        ))

        # Add house number label
        annotations.append(dict(
            x=x, y=y-0.34,
            text=f"Unit {u['unit_id']}",
            showarrow=False,
            font=dict(size=8),
            align="center"
        ))

    # Draw unhoused area on the right
    waiting_area_x = grid_size + 0.5
    shapes.append(dict(
        type="rect",
        x0=waiting_area_x, y0=-0.5,
        x1=waiting_area_x + 2, y1=grid_size + 0.5,
        line=dict(color="black", width=1),
        fillcolor="rgba(255,240,240,0.5)",
        layer="below"
    ))
    annotations.append(dict(
        x=waiting_area_x + 1, y=grid_size,
        text="Unhoused<br>Households",
        showarrow=False,
        font=dict(size=12),
        align="center"
    ))

    return shapes, annotations

def make_figure(frame, grid_size, prev_frame=None, is_cap_scenario=True, movement_logs=None, current_month=None, unhoused_data=None, prev_unhoused_data=None):
    shapes, annotations = make_house_shapes(frame, grid_size, is_cap_scenario)
    
    # Create scatter traces for households
    household_x = []
    household_y = []
    household_text = []
    household_colors = []
    
    # Add invisible scatter for house hover info
    house_x = []
    house_y = []
    house_hover = []
    
    # Add houses and their hover info
    for i, u in enumerate(frame):
        row, col = divmod(i, grid_size)
        x = col
        y = grid_size - row - 1
        
        # Add house hover point
        house_x.append(x)
        house_y.append(y)
        
        # Format conditional values
        satisfaction = u['tenant_satisfaction']
        satisfaction_str = f"{satisfaction:.2f}" if satisfaction is not None else "N/A"
        
        owner_satisfaction = u['owner_satisfaction']
        owner_satisfaction_str = f"{owner_satisfaction:.2f}" if owner_satisfaction is not None else "N/A"
        
        life_stage = u['tenant_life_stage'] if u['tenant_life_stage'] is not None else "N/A"
        
        house_hover.append(
            f"Unit {u['unit_id']}<br>"
            f"{'Owner-Occupied' if u['is_owner_occupied'] else ('Rented' if u['occupied'] else 'Vacant')}<br>"
            f"Rent: ${u['rent']:.0f}<br>"
            f"Quality: {u['quality']:.2f}<br>"
            f"Property Value: ${u['property_value']:.0f}<br>"
            f"Tenant Size: {u['tenant_size']}<br>"
            f"Tenant Income: ${u['tenant_income']:.0f}<br>"
            f"Tenant Wealth: ${u['tenant_wealth']:.0f}<br>"
            f"Tenant Satisfaction: {satisfaction_str}<br>"
            f"Tenant Life Stage: {life_stage}<br>"
            f"Tenant Rent Burden: {u['tenant_rent_burden']:.2%}<br>"
            f"Owner Income: ${u['owner_income']:.0f}<br>"
            f"Owner Wealth: ${u['owner_wealth']:.0f}<br>"
            f"Owner Mortgage: ${u['owner_mortgage']:.0f}<br>"
            f"Owner Monthly Payment: ${u['owner_monthly_payment']:.0f}<br>"
            f"Owner Satisfaction: {owner_satisfaction_str}"
        )
        
        # Add households in houses
        if u['occupied'] or u['is_owner_occupied']:
            size = u['tenant_size'] if not u['is_owner_occupied'] else 1
            for j in range(size):
                offset_x = (j - (size - 1) / 2) * 0.15
                px = x + offset_x
                py = y - 0.05
                color = "rgba(27,158,119,1)" if not u['is_owner_occupied'] else "rgba(55,119,194,1)"  # #1b9e77 or #3777c2
                
                # Add stick figure parts
                # Head
                shapes.append(dict(
                    type="circle",
                    x0=px-0.04, y0=py+0.02, x1=px+0.04, y1=py+0.10,
                    line=dict(color="rgba(34,34,34,1)", width=1),
                    fillcolor=color,
                    layer="above"
                ))
                # Body
                shapes.append(dict(
                    type="line",
                    x0=px, y0=py+0.02, x1=px, y1=py-0.02,
                    line=dict(color="rgba(34,34,34,1)", width=1.5),
                    layer="above"
                ))
                # Arms
                shapes.append(dict(
                    type="line",
                    x0=px-0.04, y0=py-0.04, x1=px, y1=py,
                    line=dict(color="rgba(34,34,34,1)", width=1.5),
                    layer="above"
                ))
                shapes.append(dict(
                    type="line",
                    x0=px, y0=py, x1=px+0.04, y1=py-0.04,
                    line=dict(color="rgba(34,34,34,1)", width=1.5),
                    layer="above"
                ))
                # Legs
                shapes.append(dict(
                    type="line",
                    x0=px, y0=py-0.02, x1=px-0.03, y1=py-0.08,
                    line=dict(color="rgba(34,34,34,1)", width=1.5),
                    layer="above"
                ))
                shapes.append(dict(
                    type="line",
                    x0=px, y0=py-0.02, x1=px+0.03, y1=py-0.08,
                    line=dict(color="rgba(34,34,34,1)", width=1.5),
                    layer="above"
                ))
                
                household_x.append(px)
                household_y.append(py)
                household_text.append(f"{'Owner' if u['is_owner_occupied'] else 'Tenant'} in Unit {u['unit_id']}")
                household_colors.append("rgba(0,0,0,0)")  # Invisible markers for hover only

        # Add household event indicators (breakup/merger)
        if u.get('household_event') == 'breakup':
            # Add exclamation mark
            shapes.append(dict(
                type="line",
                x0=x, y0=y+0.5, x1=x, y1=y+0.3,
                line=dict(color="red", width=2),
                layer="above"
            ))
            shapes.append(dict(
                type="circle",
                x0=x-0.02, y0=y+0.2, x1=x+0.02, y1=y+0.24,
                line=dict(color="red", width=2),
                fillcolor="red",
                layer="above"
            ))
        elif u.get('household_event') == 'merger':
            # Add check mark
            shapes.append(dict(
                type="path",
                path=f'M {x-0.1},{y+0.35} L {x},{y+0.25} L {x+0.15},{y+0.45}',
                line=dict(color="green", width=2),
                layer="above"
            ))

    # Add unhoused households on the right - with proper tracking
    waiting_area_x = grid_size + 1
    unhoused_count = unhoused_data['count'] if unhoused_data else 0
    unhoused_households = unhoused_data['households'] if unhoused_data else []
    
    # Create a mapping of household IDs to their positions for movement tracking
    unhoused_positions = {}
    
    for i in range(unhoused_count):
        row = i // 2  # 2 households per row
        col = i % 2
        px = waiting_area_x + col * 0.5
        py = grid_size - 1 - row * 0.5
        
        # Store position for this household
        if i < len(unhoused_households):
            household_id = unhoused_households[i]['id']
            unhoused_positions[household_id] = (px, py)
        
        # Add stick figure parts for unhoused households
        # Head
        shapes.append(dict(
            type="circle",
            x0=px-0.04, y0=py+0.02, x1=px+0.04, y1=py+0.10,
            line=dict(color="rgba(34,34,34,1)", width=1),
            fillcolor="rgba(228,26,28,1)",  # #e41a1c
            layer="above"
        ))
        # Body
        shapes.append(dict(
            type="line",
            x0=px, y0=py+0.02, x1=px, y1=py-0.02,
            line=dict(color="rgba(34,34,34,1)", width=1.5),
            layer="above"
        ))
        # Arms
        shapes.append(dict(
            type="line",
            x0=px-0.04, y0=py-0.04, x1=px, y1=py,
            line=dict(color="rgba(34,34,34,1)", width=1.5),
            layer="above"
        ))
        shapes.append(dict(
            type="line",
            x0=px, y0=py, x1=px+0.04, y1=py-0.04,
            line=dict(color="rgba(34,34,34,1)", width=1.5),
            layer="above"
        ))
        # Legs
        shapes.append(dict(
            type="line",
            x0=px, y0=py-0.02, x1=px-0.03, y1=py-0.08,
            line=dict(color="rgba(34,34,34,1)", width=1.5),
            layer="above"
        ))
        shapes.append(dict(
            type="line",
            x0=px, y0=py-0.02, x1=px+0.03, y1=py-0.08,
            line=dict(color="rgba(34,34,34,1)", width=1.5),
            layer="above"
        ))
        
        household_x.append(px)
        household_y.append(py)
        # Add hover info for unhoused households
        if i < len(unhoused_households):
            hh_info = unhoused_households[i]
            household_text.append(f"Unhoused Household {hh_info['id']}<br>Size: {hh_info['size']}<br>Income: ${hh_info['income']:.0f}<br>Wealth: ${hh_info['wealth']:.0f}<br>Life Stage: {hh_info['life_stage']}")
        else:
            household_text.append("Unhoused Household")
        household_colors.append("rgba(0,0,0,0)")  # Invisible markers for hover only

    # Create the main figure
    fig = go.Figure()

    # Add invisible scatter for house hover info
    fig.add_trace(go.Scatter(
        x=house_x,
        y=house_y,
        mode='markers',
        marker=dict(size=1, color='rgba(0,0,0,0)'),  # invisible
        text=house_hover,
        hoverinfo='text',
        name='Houses'
    ))
    
    # Add households as invisible points for hover info
    fig.add_trace(go.Scatter(
        x=household_x,
        y=household_y,
        mode='markers',
        marker=dict(
            size=1,
            color=household_colors
        ),
        text=household_text,
        hoverinfo='text',
        name='Households'
    ))

    # Add movement arrows if we have movement logs for this frame
    if movement_logs is not None and current_month is not None and current_month < len(movement_logs):
        movements = []
        
        # Create position mapping for previous unhoused households (for movement tracking)
        prev_unhoused_positions = {}
        if prev_unhoused_data and 'households' in prev_unhoused_data:
            for i, hh_info in enumerate(prev_unhoused_data['households']):
                row = i // 2
                col = i % 2
                px = waiting_area_x + col * 0.5
                py = grid_size - 1 - row * 0.5
                prev_unhoused_positions[hh_info['id']] = (px, py)
        
        # Parse each movement log entry to get source and destination units
        for log_entry in movement_logs[current_month]:
            # Parse the movement log entry to extract unit numbers and household ID
            # Example format: "HH X moved from Unit Y to Unit Z" or "HH X moved from Unhoused to Unit Z"
            parts = log_entry.split(", ")[0]  # Get the first part with movement info
            
            # Extract household ID
            hh_id = None
            if "HH " in parts:
                hh_id_str = parts.split("HH ")[1].split(" ")[0]
                try:
                    hh_id = int(hh_id_str)
                except:
                    hh_id = None
            
            if "moved from Unit" in parts:
                # Extract source and destination unit numbers
                source_unit = int(parts.split("Unit ")[1].split(" to")[0])
                dest_unit = int(parts.split("to Unit ")[1])
                
                # Get source unit position
                source_row, source_col = divmod(source_unit, grid_size)
                source_x = source_col
                source_y = grid_size - source_row - 1
                
                # Get destination unit position
                dest_row, dest_col = divmod(dest_unit, grid_size)
                dest_x = dest_col
                dest_y = grid_size - dest_row - 1
                
                movements.append({
                    'from_x': source_x,
                    'from_y': source_y,
                    'to_x': dest_x,
                    'to_y': dest_y,
                    'color': 'blue'  # house-to-house moves
                })
            elif "moved from Unhoused to Unit" in parts:
                # Extract destination unit number
                dest_unit = int(parts.split("to Unit ")[1])
                
                # Get destination unit position
                dest_row, dest_col = divmod(dest_unit, grid_size)
                dest_x = dest_col
                dest_y = grid_size - dest_row - 1
                
                # Try to find the specific household's position from previous frame
                from_x, from_y = waiting_area_x, grid_size - 1  # Default position
                if hh_id and hh_id in prev_unhoused_positions:
                    from_x, from_y = prev_unhoused_positions[hh_id]
                
                movements.append({
                    'from_x': from_x,
                    'from_y': from_y,
                    'to_x': dest_x,
                    'to_y': dest_y,
                    'color': 'green'  # unhoused to housed moves
                })

        # Add all movement arrows
        for move in movements:
            fig.add_trace(go.Scatter(
                x=[move['from_x'], move['to_x']],
                y=[move['from_y'], move['to_y']],
                mode='lines+markers',
                line=dict(
                    color=move['color'],
                    width=2,
                    dash='dot'
                ),
                marker=dict(symbol=['circle', 'arrow-right']),
                showlegend=False
            ))

    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            visible=False,
            fixedrange=True,  # Prevent zoom/pan
            range=[-1, grid_size + 8]  # Fixed range
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            visible=False,
            fixedrange=True,
            range=[-1, grid_size + 0.5]  # Fixed range
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='white',
        height=1000,
        showlegend=False,
        hovermode='closest',
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        },
        autosize=False,
        width=1700,  # or match your style
    )

    return fig

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Create the layout with two pages
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.H1("Housing Market Simulation"),
        html.Div([
            html.A("With Rent Cap", href="/with-cap", style={'marginRight': '20px'}),
            html.A("Without Rent Cap", href="/without-cap", style={'marginRight': '20px'}),
            html.A("About the Model", href="/about")
        ], style={'marginBottom': '20px'})
    ]),
    # Add interval and store components to main layout
    dcc.Store(id='prev-month', data=0),
    dcc.Store(id='scenario-type', data='cap'),
    dcc.Interval(
        id='auto-stepper',
        interval=1000,  # in milliseconds (1 second per step)
        n_intervals=0,
        disabled=True
    ),
    html.Div(id='page-content')
])

def create_page_layout(is_cap_scenario):
    title = "Housing Market Simulation (With Rent Cap)" if is_cap_scenario else "Housing Market Simulation (Without Rent Cap)"
    frames = frames_cap if is_cap_scenario else frames_nocap
    movement_logs = movement_logs_cap if is_cap_scenario else movement_logs_nocap
    
    # Calculate total number of periods (2 periods per year for 10 years)
    total_periods = len(frames)
    
    # Create marks for the slider (show every year)
    slider_marks = {i: f'Year {i//2 + 1}, Period {i%2 + 1}' 
                   for i in range(0, total_periods, 2)}  # Show every year
    
    return html.Div([
        html.H1(title),
        html.Div([
            html.Div([
                dcc.Graph(
                    id='graph', 
                    style={
                        'height': '1000px', 
                        'width': '1700px',
                        'margin': '0',
                        'padding': '0'
                    },
                    config={
                        'displayModeBar': False,  # Hide plotly toolbar
                        'staticPlot': False,
                        'responsive': False  # Disable responsive behavior
                    }
                )
            ], style={
                'width': '70vw', 
                'height': '80vh',
                'overflow': 'hidden',  # Prevent scrollbars from affecting layout
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center'
            }),
            html.Div([
                html.Div(id='sidebar-stats', style={'marginBottom': '20px'}),
                html.H4("Movement Log", style={'marginBottom': '10px'}),
                html.Div(id='movement-log', style={
                    'maxHeight': '200px', 
                    'overflowY': 'auto',
                    'fontFamily': 'monospace',
                    'whiteSpace': 'pre-wrap',
                    'padding': '10px',
                    'backgroundColor': '#fafafa',
                    'border': '1px solid #ccc',
                    'borderRadius': '5px'
                })
            ], style={
                'width': '28vw', 
                'padding': '1vw', 
                'marginLeft': '1vw',
                'height': '80vh',
                'overflow': 'auto'
            })
        ], style={
            'display': 'flex', 
            'flex-direction': 'row',
            'height': '80vh',
            'width': '100vw'
        }),
        dcc.Slider(
            id='period-slider',
            min=0,
            max=total_periods-1,
            value=0,
            marks=slider_marks,
            step=1,
            updatemode='drag'
        ),
        html.Button('Play/Pause', id='play-button', style={'marginTop': '10px'}),
        dcc.Interval(
            id='auto-stepper',
            interval=1000,  # in milliseconds (1 second per step)
            n_intervals=0,
            disabled=True
        )
    ])

def create_about_page():
    return html.Div([
        html.H1("About the Housing Market Simulation Model", style={'marginBottom': '30px'}),
        
        html.Div([
            # Introduction Section
            html.Div([
                html.H2("How the Model Works", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                
                # Visual representation of key components
                html.Div([
                    html.Div([
                        html.Div(style={
                            'width': '100px',
                            'height': '100px',
                            'backgroundColor': 'royalblue',
                            'margin': '10px',
                            'position': 'relative',
                            'display': 'inline-block'
                        }, children=[
                            html.Div(style={
                                'width': '0',
                                'height': '0',
                                'borderLeft': '50px solid transparent',
                                'borderRight': '50px solid transparent',
                                'borderBottom': '40px solid #d95f02',
                                'position': 'absolute',
                                'top': '-40px',
                                'left': '0'
                            })
                        ]),
                        html.P("Owner-Occupied", style={'textAlign': 'center'})
                    ], style={'display': 'inline-block', 'margin': '10px'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '100px',
                            'height': '100px',
                            'backgroundColor': 'limegreen',
                            'margin': '10px',
                            'position': 'relative',
                            'display': 'inline-block'
                        }, children=[
                            html.Div(style={
                                'width': '0',
                                'height': '0',
                                'borderLeft': '50px solid transparent',
                                'borderRight': '50px solid transparent',
                                'borderBottom': '40px solid #d95f02',
                                'position': 'absolute',
                                'top': '-40px',
                                'left': '0'
                            })
                        ]),
                        html.P("Rented", style={'textAlign': 'center'})
                    ], style={'display': 'inline-block', 'margin': '10px'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '100px',
                            'height': '100px',
                            'backgroundColor': 'lightgray',
                            'margin': '10px',
                            'position': 'relative',
                            'display': 'inline-block'
                        }, children=[
                            html.Div(style={
                                'width': '0',
                                'height': '0',
                                'borderLeft': '50px solid transparent',
                                'borderRight': '50px solid transparent',
                                'borderBottom': '40px solid #d95f02',
                                'position': 'absolute',
                                'top': '-40px',
                                'left': '0'
                            })
                        ]),
                        html.P("Vacant", style={'textAlign': 'center'})
                    ], style={'display': 'inline-block', 'margin': '10px'})
                ], style={'textAlign': 'center', 'marginBottom': '30px'}),

                html.H3("Key Components:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Housing Units: Each square represents a housing unit that can be either owner-occupied (blue), rented (green), or vacant (gray)"),
                    html.Li("Households: Represented by stick figures - owners (blue), renters (green), and unhoused (red)"),
                    html.Li("Monthly Simulation: The model advances month by month, simulating various market interactions"),
                ], style={'marginBottom': '30px'}),
            ]),

            # New Section: Tenant Search Process
            html.Div([
                html.H2("Tenant Search Process", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                html.P([
                    "The tenant search process occurs simultaneously for all households at each time step. Here's how it works:",
                    html.Ul([
                        html.Li("All households evaluate their current situation at the same time"),
                        html.Li("Each household calculates their satisfaction score based on multiple factors"),
                        html.Li("Households then search for new housing in parallel, with the following priority:"),
                        html.Ul([
                            html.Li("Unhoused households get first priority in unit selection"),
                            html.Li("Households with lower satisfaction scores get higher priority"),
                            html.Li("When multiple households want the same unit, the one with the best matching criteria (income, size, preferences) gets priority")
                        ])
                    ])
                ], style={'marginBottom': '20px'}),
            ]),

            # New Section: Tenant Movement Motivations
            html.Div([
                html.H2("What Motivates Tenants to Move?", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                html.Div([
                    # Visual representation of tenant motivations
                    html.Div([
                        html.Div(style={
                            'border': '2px solid #3498db',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Financial Factors", style={'color': '#3498db'}),
                            html.Ul([
                                html.Li("High rent burden (>50% of income)"),
                                html.Li("Significant rent increases"),
                                html.Li("Better affordability elsewhere")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #2ecc71',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Quality of Life", style={'color': '#2ecc71'}),
                            html.Ul([
                                html.Li("Low housing quality"),
                                html.Li("Inadequate unit size for household"),
                                html.Li("Poor location score")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #e74c3c',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Life Changes", style={'color': '#e74c3c'}),
                            html.Ul([
                                html.Li("Changes in household size"),
                                html.Li("Income changes"),
                                html.Li("Life stage transitions")
                            ])
                        ])
                    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'})
                ])
            ]),

            # New Section: Landlord Pricing Motivations
            html.Div([
                html.H2("What Drives Landlord Pricing?", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                html.Div([
                    # Visual representation of landlord motivations
                    html.Div([
                        html.Div(style={
                            'border': '2px solid #9b59b6',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Market Conditions", style={'color': '#9b59b6'}),
                            html.Ul([
                                html.Li("Local vacancy rates"),
                                html.Li("Average market rents"),
                                html.Li("Seasonal demand changes")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #f1c40f',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Property Factors", style={'color': '#f1c40f'}),
                            html.Ul([
                                html.Li("Unit quality and amenities"),
                                html.Li("Recent renovations"),
                                html.Li("Location desirability")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #e67e22',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Regulatory Environment", style={'color': '#e67e22'}),
                            html.Ul([
                                html.Li("Rent control policies"),
                                html.Li("Property tax rates"),
                                html.Li("Inspection requirements")
                            ])
                        ])
                    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'})
                ])
            ]),

            # Original Parameters Section
            html.H2("Key Parameters", style={'marginBottom': '20px', 'color': '#2c3e50'}),
            html.Div([
                html.H3("Housing Unit Parameters:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Quality: Affects property value and tenant satisfaction"),
                    html.Li("Rent: Monthly payment for tenants"),
                    html.Li("Property Value: Current market value of the unit"),
                ], style={'marginBottom': '20px'}),
                
                html.H3("Household Parameters:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Income: Monthly household income"),
                    html.Li("Wealth: Accumulated savings and assets"),
                    html.Li("Size: Number of household members"),
                    html.Li("Life Stage: Affects housing preferences and decisions"),
                    html.Li("Satisfaction: Measure of contentment with current housing situation"),
                ], style={'marginBottom': '20px'}),
                
                html.H3("Market Parameters:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Rent Cap (in cap scenario): Maximum allowed rent increase"),
                    html.Li("Mortgage Rates: Affects monthly payments for buyers"),
                    html.Li("Market Demand: Overall housing demand in the area")
                ])
            ])
        ], style={
            'maxWidth': '1200px',
            'margin': '0 auto',
            'padding': '20px',
            'lineHeight': '1.6',
            'fontSize': '16px',
            'backgroundColor': 'white',
            'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
            'borderRadius': '10px'
        })
    ], style={'backgroundColor': '#f5f6fa', 'minHeight': '100vh', 'padding': '20px'})

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/with-cap':
        return create_page_layout(True)
    elif pathname == '/without-cap':
        return create_page_layout(False)
    elif pathname == '/about':
        return create_about_page()
    else:
        return create_page_layout(True)  # Default to with-cap scenario

@app.callback(
    Output('scenario-type', 'data'),
    Input('url', 'pathname')
)
def update_scenario_type(pathname):
    if pathname == '/without-cap':
        return 'nocap'
    return 'cap'  # Default to cap scenario for all other pages

@app.callback(
    Output('auto-stepper', 'disabled'),
    Input('play-button', 'n_clicks'),
    Input('period-slider', 'value'),
    State('auto-stepper', 'disabled'),
    State('period-slider', 'max')
)
def toggle_animation(n_clicks, current_value, current_state, max_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return True
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'play-button':
        # Toggle play/pause when button is clicked
        if n_clicks is None:
            return True
        return not current_state
    elif trigger_id == 'period-slider':
        # Stop animation if we've reached the end
        if current_value is not None and current_value >= max_value:
            return True
        # Otherwise maintain current state unless manually toggled
        return current_state
    
    return True

@app.callback(
    Output('period-slider', 'value'),
    Input('auto-stepper', 'n_intervals'),
    State('period-slider', 'value'),
    State('period-slider', 'max'),
    prevent_initial_call=True
)
def update_slider(n_intervals, current_value, max_value):
    if current_value is None:
        return 0
    if current_value >= max_value:
        # Stop at the end instead of looping
        return max_value
    return current_value + 1 if current_value is not None else 0

@app.callback(
    Output('graph', 'figure'),
    Output('sidebar-stats', 'children'),
    Output('movement-log', 'children'),
    Output('prev-month', 'data'),
    Input('period-slider', 'value'),
    Input('prev-month', 'data'),
    Input('scenario-type', 'data'),
    prevent_initial_call=True
)
def update_figure(period_idx, prev_period_idx, scenario_type):
    if period_idx is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
    frames = frames_cap if scenario_type == 'cap' else frames_nocap
    movement_logs = movement_logs_cap if scenario_type == 'cap' else movement_logs_nocap
    unhoused_data = unhoused_data_cap if scenario_type == 'cap' else unhoused_data_nocap
    
    frame = frames[period_idx]
    prev_frame = frames[prev_period_idx] if prev_period_idx < period_idx else None
    current_unhoused = unhoused_data[period_idx] if period_idx < len(unhoused_data) else {'count': 0, 'households': []}
    
    fig = make_figure(frame, grid_size, prev_frame, scenario_type == 'cap', movement_logs, period_idx, current_unhoused, unhoused_data[prev_period_idx] if prev_period_idx < len(unhoused_data) else {'count': 0, 'households': []})

    # Calculate detailed metrics for sidebar
    year = period_idx // 2 + 1
    period = period_idx % 2 + 1

    # Housing Market Metrics
    owner_share = sum(u['is_owner_occupied'] for u in frame) / len(frame)
    avg_mortgage = np.mean([u['owner_mortgage'] for u in frame if u['is_owner_occupied']]) if any(u['is_owner_occupied'] for u in frame) else 0
    avg_satisfaction = np.mean([u['tenant_satisfaction'] for u in frame if u['tenant_satisfaction'] is not None])
    avg_rent = np.mean([u['rent'] for u in frame if u['occupied']])
    avg_quality = np.mean([u['quality'] for u in frame])
    
    # Population Metrics
    housed_count = sum(1 for u in frame if u['occupied'] or u['is_owner_occupied'])
    unhoused_count = current_unhoused['count']
    total_households = housed_count + unhoused_count
    vacancy_count = sum(1 for u in frame if not u['occupied'] and not u['is_owner_occupied'])
    
    # Financial Metrics
    avg_tenant_income = np.mean([u['tenant_income'] for u in frame if u['occupied'] and not u['is_owner_occupied']])
    avg_tenant_wealth = np.mean([u['tenant_wealth'] for u in frame if u['occupied'] and not u['is_owner_occupied']])
    avg_owner_income = np.mean([u['owner_income'] for u in frame if u['is_owner_occupied']])
    avg_owner_wealth = np.mean([u['owner_wealth'] for u in frame if u['is_owner_occupied']])
    avg_rent_burden = np.mean([u['tenant_rent_burden'] for u in frame if u['occupied'] and not u['is_owner_occupied']])
    
    # Life Stage Distribution
    life_stages = {}
    for u in frame:
        if u['occupied'] and u['tenant_life_stage']:
            life_stages[u['tenant_life_stage']] = life_stages.get(u['tenant_life_stage'], 0) + 1

    # Create sidebar stats with sections
    sidebar_stats = html.Div([
        # Time Period
        html.Div([
            html.H4("Time Period", style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.Pre(f"Year {year}, Period {period}", 
                    style={'backgroundColor': '#f8f9fa', 'padding': '5px', 'borderRadius': '3px'})
        ], style={'marginBottom': '20px'}),
        
        # Housing Market Overview
        html.Div([
            html.H4("Housing Market Overview", style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.Pre(
                f"Average Rent: ${avg_rent:.0f}\n"
                f"Average Quality: {avg_quality:.2f}\n"
                f"Vacancy Rate: {vacancy_count/len(frame):.1%}\n"
                f"Owner-Occupier Share: {owner_share:.1%}\n"
                f"Average Satisfaction: {avg_satisfaction:.2f}",
                style={'backgroundColor': '#f8f9fa', 'padding': '5px', 'borderRadius': '3px'}
            )
        ], style={'marginBottom': '20px'}),
        
        # Population Statistics
        html.Div([
            html.H4("Population Statistics", style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.Pre(
                f"Total Households: {total_households}\n"
                f"Housed: {housed_count}\n"
                f"Unhoused: {unhoused_count}\n"
                f"Vacant Units: {vacancy_count}",
                style={'backgroundColor': '#f8f9fa', 'padding': '5px', 'borderRadius': '3px'}
            )
        ], style={'marginBottom': '20px'}),
        
        # Financial Metrics
        html.Div([
            html.H4("Financial Metrics", style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.Pre(
                f"Tenant Metrics:\n"
                f"  Average Income: ${avg_tenant_income:.0f}\n"
                f"  Average Wealth: ${avg_tenant_wealth:.0f}\n"
                f"  Average Rent Burden: {avg_rent_burden:.1%}\n\n"
                f"Owner Metrics:\n"
                f"  Average Income: ${avg_owner_income:.0f}\n"
                f"  Average Wealth: ${avg_owner_wealth:.0f}\n"
                f"  Average Mortgage: ${avg_mortgage:.0f}",
                style={'backgroundColor': '#f8f9fa', 'padding': '5px', 'borderRadius': '3px'}
            )
        ], style={'marginBottom': '20px'}),
        
        # Life Stage Distribution
        html.Div([
            html.H4("Life Stage Distribution", style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.Pre(
                "\n".join(f"{stage}: {count}" for stage, count in sorted(life_stages.items())),
                style={'backgroundColor': '#f8f9fa', 'padding': '5px', 'borderRadius': '3px'}
            )
        ], style={'marginBottom': '20px'})
    ], style={
        'backgroundColor': 'white',
        'padding': '15px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    })

    # Movement logs
    movement_log = []
    if period_idx < len(movement_logs):
        for move in movement_logs[period_idx]:
            movement_log.append(html.Pre(move, style={'margin': '5px 0'}))

    return fig, sidebar_stats, movement_log, period_idx

if __name__ == '__main__':
    app.run(debug=True)
