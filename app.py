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

        # Add household event indicators (breakup/merger) - ENHANCED
        if u.get('household_event') == 'breakup':
            # Add larger exclamation mark
            shapes.append(dict(
                type="line",
                x0=x, y0=y+0.6, x1=x, y1=y+0.35,  # Made taller
                line=dict(color="red", width=3),  # Made thicker
                layer="above"
            ))
            shapes.append(dict(
                type="circle",
                x0=x-0.03, y0=y+0.25, x1=x+0.03, y1=y+0.31,  # Made larger
                line=dict(color="red", width=3),  # Made thicker
                fillcolor="red",
                layer="above"
            ))
        elif u.get('household_event') == 'merger':
            # Add larger check mark
            shapes.append(dict(
                type="path",
                path=f'M {x-0.15},{y+0.4} L {x},{y+0.25} L {x+0.2},{y+0.5}',  # Made larger
                line=dict(color="green", width=3),  # Made thicker
                layer="above"
            ))

    # Add unhoused households on the right - with proper tracking
    waiting_area_x = grid_size + 1
    unhoused_count = unhoused_data['count'] if unhoused_data else 0
    unhoused_households = unhoused_data['households'] if unhoused_data else []
    
    # Create a mapping of household IDs to their positions for movement tracking
    unhoused_positions = {}
    
    # Calculate positions for unhoused households
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
            
            # Add hover info for unhoused households
            household_x.append(px)
            household_y.append(py)
            household_text.append(f"Unhoused HH {household_id} - Size: {unhoused_households[i]['size']}, Income: ${unhoused_households[i]['income']:.0f}")
            household_colors.append("rgba(0,0,0,0)")  # Invisible markers for hover only

    # Add movement arrows if we have previous frame data and movement logs
    if prev_frame is not None and movement_logs:
        for log in movement_logs:
            if "moved from" in log:
                parts = log.split()
                hh_id = int(parts[1])  # "HH X moved from..."
                from_unit = None if "Unhoused" in log else int(parts[4])  # "... from Unit X to..."
                to_unit = int(parts[7])  # "... to Unit X, ..."
                
                # Get source position
                if from_unit is None:
                    # Moving from unhoused area - get position from prev_unhoused_data
                    if prev_unhoused_data and 'households' in prev_unhoused_data:
                        for i, hh in enumerate(prev_unhoused_data['households']):
                            if hh['id'] == hh_id:
                                row = i // 2
                                col = i % 2
                                start_x = waiting_area_x + col * 0.5
                                start_y = grid_size - 1 - row * 0.5
                                break
                else:
                    # Moving from a unit
                    row, col = divmod(from_unit - 1, grid_size)
                    start_x = col
                    start_y = grid_size - row - 1
                
                # Get destination position (always a unit)
                row, col = divmod(to_unit - 1, grid_size)
                end_x = col
                end_y = grid_size - row - 1
                
                # Add arrow if we have valid start and end positions
                if 'start_x' in locals():
                    # Calculate curve control points
                    dx = end_x - start_x
                    dy = end_y - start_y
                    dist = np.sqrt(dx*dx + dy*dy)
                    
                    if dist > 0:
                        # Make curve more pronounced for longer distances
                        curve_height = min(1.0, dist * 0.3)
                        mid_x = (start_x + end_x) / 2
                        mid_y = (start_y + end_y) / 2
                        
                        # Perpendicular vector for curve control
                        perp_x = -dy / dist * curve_height
                        perp_y = dx / dist * curve_height
                        
                        # Control point
                        ctrl_x = mid_x + perp_x
                        ctrl_y = mid_y + perp_y
                        
                        # Draw curved path
                        path = f"M {start_x},{start_y} Q {ctrl_x},{ctrl_y} {end_x},{end_y}"
                        shapes.append(dict(
                            type="path",
                            path=path,
                            line=dict(
                                color="rgba(0,0,0,0.6)",  # Made more visible
                                width=2,
                                dash="dot"
                            ),
                            layer="below"
                        ))
                        
                        # Add arrowhead at end
                        # Calculate direction at end point
                        end_dx = end_x - ctrl_x
                        end_dy = end_y - ctrl_y
                        end_dist = np.sqrt(end_dx*end_dx + end_dy*end_dy)
                        
                        if end_dist > 0:
                            end_dx /= end_dist
                            end_dy /= end_dist
                            
                            # Calculate arrow points
                            arrow_size = 0.2
                            arrow_angle = np.pi/6  # 30 degrees
                            
                            ax = end_x - arrow_size * (end_dx*np.cos(arrow_angle) + end_dy*np.sin(arrow_angle))
                            ay = end_y - arrow_size * (end_dy*np.cos(arrow_angle) - end_dx*np.sin(arrow_angle))
                            bx = end_x - arrow_size * (end_dx*np.cos(arrow_angle) - end_dy*np.sin(arrow_angle))
                            by = end_y - arrow_size * (end_dy*np.cos(arrow_angle) + end_dx*np.sin(arrow_angle))
                            
                            # Add arrowhead
                            shapes.append(dict(
                                type="path",
                                path=f"M {end_x},{end_y} L {ax},{ay} M {end_x},{end_y} L {bx},{by}",
                                line=dict(
                                    color="rgba(0,0,0,0.6)",  # Made more visible
                                    width=2
                                ),
                                layer="below"
                            ))

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
        showlegend=False,
        hovermode='closest',
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        },
        autosize=True  # Let the container control the size
    )

    return fig

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Create the layout with two pages
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        # Enhanced header with modern styling
        html.Div([
            html.H1("Housing Market Simulation", 
                   style={
                       'fontFamily': 'Helvetica Neue, Arial, sans-serif',
                       'fontSize': '2.5rem',
                       'fontWeight': '300',
                       'color': '#2c3e50',
                       'marginBottom': '20px',
                       'textAlign': 'center',
                       'letterSpacing': '0.05em',
                       'borderBottom': '2px solid #3498db',
                       'paddingBottom': '10px'
                   }),
            # Navigation menu with modern styling
            html.Div([
                html.A("With Rent Cap", 
                      href="/with-cap", 
                      style={
                          'backgroundColor': '#3498db',
                          'color': 'white',
                          'padding': '10px 20px',
                          'borderRadius': '5px',
                          'textDecoration': 'none',
                          'marginRight': '15px',
                          'transition': 'background-color 0.3s ease',
                          'fontWeight': '500',
                          'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                      }),
                html.A("Without Rent Cap", 
                      href="/without-cap", 
                      style={
                          'backgroundColor': '#2ecc71',
                          'color': 'white',
                          'padding': '10px 20px',
                          'borderRadius': '5px',
                          'textDecoration': 'none',
                          'marginRight': '15px',
                          'transition': 'background-color 0.3s ease',
                          'fontWeight': '500',
                          'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                      }),
                html.A("About the Model", 
                      href="/about", 
                      style={
                          'backgroundColor': '#e74c3c',
                          'color': 'white',
                          'padding': '10px 20px',
                          'borderRadius': '5px',
                          'textDecoration': 'none',
                          'transition': 'background-color 0.3s ease',
                          'fontWeight': '500',
                          'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                      })
            ], style={
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center',
                'marginBottom': '30px'
            })
        ], style={
            'backgroundColor': 'white',
            'padding': '20px',
            'boxShadow': '0 2px 10px rgba(0,0,0,0.1)',
            'marginBottom': '30px'
        }),
    ]),
    # Add interval and store components to main layout
    dcc.Store(id='prev-month', data=0),
    dcc.Store(id='scenario-type', data='cap'),
    dcc.Interval(
        id='auto-stepper',
        interval=2000,  # Changed to 2000ms (2 seconds)
        n_intervals=0,
        disabled=True
    ),
    html.Div(id='page-content', style={'height': '100vh'})
], style={
    'backgroundColor': '#f5f6fa',
    'minHeight': '100vh',
    'margin': '0',
    'padding': '0'
})

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
        html.H1(title, style={
            'fontFamily': 'Helvetica Neue, Arial, sans-serif',
            'fontSize': '2rem',
            'fontWeight': '300',
            'color': '#2c3e50',
            'marginBottom': '20px',
            'textAlign': 'center'
        }),
        html.Div([
            # Main visualization container
            html.Div([
                dcc.Graph(
                    id='graph',
                    style={
                        'width': '100%',
                        'height': '100%'  # Take full height of container
                    },
                    config={
                        'displayModeBar': False,
                        'responsive': True
                    }
                )
            ], style={
                'flex': '3',
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.1)',
                'padding': '20px',
                'marginRight': '20px',
                'height': 'calc(100vh - 250px)',  # Fixed height based on viewport
                'minHeight': '600px'  # Minimum height
            }),
            
            # Sidebar container
            html.Div([
                html.Div(id='sidebar-stats', style={
                    'marginBottom': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'padding': '15px',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.1)'
                }),
                html.H4("Movement Log", style={
                    'color': '#2c3e50',
                    'marginBottom': '10px',
                    'fontFamily': 'Helvetica Neue, Arial, sans-serif'
                }),
                html.Div(id='movement-log', style={
                    'maxHeight': 'calc(100vh - 500px)',
                    'overflowY': 'auto',
                    'fontFamily': 'monospace',
                    'whiteSpace': 'pre-wrap',
                    'padding': '15px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 6px rgba(0,0,0,0.1)'
                })
            ], style={
                'flex': '1',
                'minWidth': '300px',
                'maxWidth': '400px'
            })
        ], style={
            'display': 'flex',
            'margin': '20px',
            'height': 'calc(100vh - 250px)'  # Match container height
        }),
        
        # Controls container
        html.Div([
            html.Div([
                dcc.Slider(
                    id='period-slider',
                    min=0,
                    max=total_periods-1,
                    value=0,
                    marks=slider_marks,
                    step=1,
                    updatemode='drag'
                )
            ], style={'marginBottom': '20px'}),
            html.Button('Play/Pause', 
                       id='play-button', 
                       style={
                           'backgroundColor': '#3498db',
                           'color': 'white',
                           'padding': '10px 20px',
                           'border': 'none',
                           'borderRadius': '5px',
                           'cursor': 'pointer',
                           'fontWeight': '500',
                           'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                           'transition': 'background-color 0.3s ease'
                       })
        ], style={
            'padding': '20px',
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 2px 10px rgba(0,0,0,0.1)',
            'margin': '20px'
        }),
        
        # Add interval with 2-second duration
        dcc.Interval(
            id='auto-stepper',
            interval=2000,  # Changed to 2000ms (2 seconds)
            n_intervals=0,
            disabled=True
        )
    ], style={
        'backgroundColor': '#f5f6fa',
        'minHeight': '100vh',
        'padding': '20px'
    })

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
