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

def make_figure(frame, grid_size, prev_frame=None, is_cap_scenario=True, movement_logs=None, current_month=None):
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

    # Add unhoused households on the right
    waiting_area_x = grid_size + 1
    unhoused_count = sum(1 for u in frame if not u['occupied'] and not u['is_owner_occupied'])
    for i in range(unhoused_count):
        row = i // 2  # 2 households per row
        col = i % 2
        px = waiting_area_x + col * 0.5
        py = grid_size - 1 - row * 0.5
        
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
        
        # Parse each movement log entry to get source and destination units
        for log_entry in movement_logs[current_month]:
            # Parse the movement log entry to extract unit numbers
            # Example format: "HH X moved from Unit Y to Unit Z" or "HH X moved from Unhoused to Unit Z"
            parts = log_entry.split(", ")[0]  # Get the first part with movement info
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
                
                movements.append({
                    'from_x': waiting_area_x,
                    'from_y': grid_size - 1,
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

# Create the layout with two pages
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.H1("Housing Market Simulation"),
        html.Div([
            html.A("With Rent Cap", href="/with-cap", style={'marginRight': '20px'}),
            html.A("Without Rent Cap", href="/without-cap")
        ], style={'marginBottom': '20px'})
    ]),
    html.Div(id='page-content')
])

def create_page_layout(is_cap_scenario):
    title = "Housing Market Simulation (With Rent Cap)" if is_cap_scenario else "Housing Market Simulation (Without Rent Cap)"
    frames = frames_cap if is_cap_scenario else frames_nocap
    movement_logs = movement_logs_cap if is_cap_scenario else movement_logs_nocap
    
    return html.Div([
        html.H1(title),
        html.Div([
            dcc.Graph(id='graph', style={'height': '80vh', 'width': '70vw'}),
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
            ], style={'width': '28vw', 'padding': '1vw', 'marginLeft': '1vw'})
        ], style={'display': 'flex', 'flex-direction': 'row'}),
        dcc.Slider(
            id='month-slider',
            min=0,
            max=n_months-1,
            value=0,
            marks={i: f'Month {i+1}' for i in range(0, n_months, max(1, n_months//10))},
            step=1,
            updatemode='drag'  # This makes the animation smoother
        ),
        dcc.Store(id='prev-month', data=0),
        dcc.Store(id='scenario-type', data='cap' if is_cap_scenario else 'nocap'),
        # Add interval component for automatic playback
        dcc.Interval(
            id='auto-stepper',
            interval=2000,  # in milliseconds
            n_intervals=0,
            disabled=True
        ),
        html.Button('Play/Pause', id='play-button', style={'marginTop': '10px'})
    ])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/with-cap':
        return create_page_layout(True)
    elif pathname == '/without-cap':
        return create_page_layout(False)
    else:
        return create_page_layout(True)  # Default to with-cap scenario

@app.callback(
    Output('auto-stepper', 'disabled'),
    Input('play-button', 'n_clicks'),
    State('auto-stepper', 'disabled')
)
def toggle_animation(n_clicks, current_state):
    if n_clicks is None:
        return True
    return not current_state

@app.callback(
    Output('month-slider', 'value'),
    Input('auto-stepper', 'n_intervals'),
    State('month-slider', 'value'),
    State('month-slider', 'max')
)
def update_slider(n_intervals, current_value, max_value):
    if current_value >= max_value:
        return 0
    return current_value + 1 if current_value is not None else 0

@app.callback(
    Output('graph', 'figure'),
    Output('sidebar-stats', 'children'),
    Output('movement-log', 'children'),
    Output('prev-month', 'data'),
    Input('month-slider', 'value'),
    Input('prev-month', 'data'),
    Input('scenario-type', 'data')
)
def update_figure(month_idx, prev_month_idx, scenario_type):
    frames = frames_cap if scenario_type == 'cap' else frames_nocap
    movement_logs = movement_logs_cap if scenario_type == 'cap' else movement_logs_nocap
    
    frame = frames[month_idx]
    prev_frame = frames[prev_month_idx] if prev_month_idx < month_idx else None
    
    fig = make_figure(frame, grid_size, prev_frame, scenario_type == 'cap', movement_logs, month_idx)

    # Calculate metrics for sidebar
    owner_share = sum(u['is_owner_occupied'] for u in frame) / len(frame)
    avg_mortgage = np.mean([u['owner_mortgage'] for u in frame if u['is_owner_occupied']]) if any(u['is_owner_occupied'] for u in frame) else 0
    avg_satisfaction = np.mean([u['tenant_satisfaction'] for u in frame if u['tenant_satisfaction'] is not None])
    avg_rent = np.mean([u['rent'] for u in frame if u['occupied']])
    housed_count = sum(1 for u in frame if u['occupied'] or u['is_owner_occupied'])
    total_households = housed_count + sum(1 for u in frame if not u['occupied'] and not u['is_owner_occupied'])

    # Create sidebar stats in monospace format
    sidebar_stats = html.Pre([
        f"Month: {month_idx+1}\n",
        f"Owner-Occupier Share: {owner_share:.1%}\n",
        f"Avg Property Value (owners): ${avg_mortgage:.0f}\n",
        f"Avg Satisfaction: {avg_satisfaction:.2f}\n",
        f"Avg Rent: ${avg_rent:.0f}\n",
        f"Housed: {housed_count} / {total_households}\n",
        f"Unhoused: {total_households - housed_count}\n",
    ], style={
        'backgroundColor': '#fafafa',
        'padding': '10px',
        'border': '1px solid #ccc',
        'borderRadius': '5px',
        'whiteSpace': 'pre-wrap'
    })

    # Movement logs
    movement_log = []
    if month_idx < len(movement_logs):
        for move in movement_logs[month_idx]:
            movement_log.append(html.Pre(move, style={'margin': '5px 0'}))

    return fig, sidebar_stats, movement_log, month_idx

if __name__ == '__main__':
    app.run(debug=True)
