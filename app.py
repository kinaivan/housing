import dash
from dash import dcc, html, Input, Output
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
with open('movement_logs_cap.pkl', 'rb') as f:
    movement_logs_cap = pickle.load(f)
with open('movement_logs_nocap.pkl', 'rb') as f:
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
            'royalblue' if u['is_owner_occupied']
            else 'limegreen' if u['occupied']
            else 'lightgray'
        )
        shapes.append(dict(
            type="rect",
            x0=x-0.2, y0=y-0.2, x1=x+0.2, y1=y+0.2,
            line=dict(color="black", width=2),
            fillcolor=color,
            layer="below"
        ))
        # Roof (triangle)
        shapes.append(dict(
            type="path",
            path=f'M {x-0.22},{y+0.2} L{x},{y+0.4} L{x+0.22},{y+0.2} Z',
            line=dict(color="black", width=2),
            fillcolor="#d95f02",
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
        fillcolor="rgba(255, 240, 240, 0.5)",
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

def make_figure(frame, grid_size, prev_frame=None, is_cap_scenario=True):
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
        house_hover.append(
            f"Unit {u['unit_id']}<br>"
            f"{'Owner-Occupied' if u['is_owner_occupied'] else ('Rented' if u['occupied'] else 'Vacant')}<br>"
            f"Rent: ${u['rent']:.0f}<br>"
            f"Quality: {u['quality']:.2f}<br>"
            f"Property Value: ${u['property_value']:.0f}<br>"
            f"Tenant Size: {u['tenant_size']}<br>"
            f"Tenant Income: {u['tenant_income']}<br>"
            f"Tenant Wealth: {u['tenant_wealth']}<br>"
            f"Tenant Satisfaction: {u['tenant_satisfaction']}<br>"
            f"Tenant Life Stage: {u['tenant_life_stage']}<br>"
            f"Tenant Rent Burden: {u['tenant_rent_burden']}<br>"
            f"Owner Income: {u['owner_income']}<br>"
            f"Owner Wealth: {u['owner_wealth']}<br>"
            f"Owner Mortgage: {u['owner_mortgage']}<br>"
            f"Owner Monthly Payment: {u['owner_monthly_payment']}<br>"
            f"Owner Satisfaction: {u['owner_satisfaction']}<br>"
        )
        
        # Add households in houses
        if u['occupied'] or u['is_owner_occupied']:
            size = u['tenant_size'] if not u['is_owner_occupied'] else 1
            for j in range(size):
                offset_x = (j - (size - 1) / 2) * 0.15
                household_x.append(x + offset_x)
                household_y.append(y - 0.05)
                status = "Owner" if u['is_owner_occupied'] else "Tenant"
                # Detailed hover info for households
                household_text.append(
                    f"{status} in Unit {u['unit_id']}<br>"
                    f"{'Owner-Occupied' if u['is_owner_occupied'] else 'Rented'}<br>"
                    f"Rent: ${u['rent']:.0f}<br>"
                    f"Quality: {u['quality']:.2f}<br>"
                    f"Property Value: ${u['property_value']:.0f}<br>"
                    f"Tenant Size: {u['tenant_size']}<br>"
                    f"Tenant Income: {u['tenant_income']}<br>"
                    f"Tenant Wealth: {u['tenant_wealth']}<br>"
                    f"Tenant Satisfaction: {u['tenant_satisfaction']}<br>"
                    f"Tenant Life Stage: {u['tenant_life_stage']}<br>"
                    f"Tenant Rent Burden: {u['tenant_rent_burden']}<br>"
                    f"Owner Income: {u['owner_income']}<br>"
                    f"Owner Wealth: {u['owner_wealth']}<br>"
                    f"Owner Mortgage: {u['owner_mortgage']}<br>"
                    f"Owner Monthly Payment: {u['owner_monthly_payment']}<br>"
                    f"Owner Satisfaction: {u['owner_satisfaction']}<br>"
                )
                household_colors.append('#1b9e77' if not u['is_owner_occupied'] else '#3777c2')

    # Add unhoused households on the right
    waiting_area_x = grid_size + 1
    unhoused_count = sum(1 for u in frame if not u['occupied'] and not u['is_owner_occupied'])
    for i in range(unhoused_count):
        row = i // 2  # 2 households per row
        col = i % 2
        household_x.append(waiting_area_x + col * 0.5)
        household_y.append(grid_size - 1 - row * 0.5)
        household_text.append("Unhoused Household")
        household_colors.append('#e41a1c')  # Red for unhoused

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
    
    # Add households as scatter points
    fig.add_trace(go.Scatter(
        x=household_x,
        y=household_y,
        mode='markers',
        marker=dict(
            size=15,
            color=household_colors,
            symbol='circle'
        ),
        text=household_text,
        hoverinfo='text',
        name='Households'
    ))

    # Add movement arrows if we have a previous frame
    if prev_frame is not None:
        for i, (curr, prev) in enumerate(zip(frame, prev_frame)):
            if curr['occupied'] != prev['occupied'] or (curr['occupied'] and prev['occupied'] and curr['tenant_size'] != prev['tenant_size']):
                # Get positions
                curr_row, curr_col = divmod(i, grid_size)
                curr_x = curr_col
                curr_y = grid_size - curr_row - 1

                # If household moved out, show arrow to waiting area
                if not curr['occupied'] and prev['occupied']:
                    fig.add_trace(go.Scatter(
                        x=[curr_x, waiting_area_x],
                        y=[curr_y, grid_size - 1],
                        mode='lines+markers',
                        line=dict(
                            color='red',
                            width=2,
                            dash='dot'
                        ),
                        marker=dict(symbol=['circle', 'arrow-right']),
                        showlegend=False
                    ))
                # If household moved in, show arrow from waiting area
                elif curr['occupied'] and not prev['occupied']:
                    fig.add_trace(go.Scatter(
                        x=[waiting_area_x, curr_x],
                        y=[grid_size - 1, curr_y],
                        mode='lines+markers',
                        line=dict(
                            color='green',
                            width=2,
                            dash='dot'
                        ),
                        marker=dict(symbol=['circle', 'arrow-right']),
                        showlegend=False
                    ))

    # Update layout with shapes and annotations
    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-1, grid_size + 3]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-1, grid_size + 0.5]),
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='white',
        height=700,
        showlegend=False,
        hovermode='closest'
    )

    return fig

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Housing Market Simulation: Side-by-Side"),
    html.Div([
        dcc.Graph(id='graph-cap', style={'height': '80vh', 'width': '40vw'}),
        dcc.Graph(id='graph-nocap', style={'height': '80vh', 'width': '40vw'}),
        html.Div([
            html.Div(id='sidebar-stats', style={'marginBottom': '20px'}),
            html.H4("Movement Log (With Rent Cap)", style={'marginBottom': '10px'}),
            html.Div(id='movement-log-cap', style={'marginBottom': '20px', 'maxHeight': '200px', 'overflowY': 'auto'}),
            html.H4("Movement Log (No Rent Cap)", style={'marginBottom': '10px'}),
            html.Div(id='movement-log-nocap', style={'maxHeight': '200px', 'overflowY': 'auto'})
        ], style={'width': '18vw', 'padding': '2vw'})
    ], style={'display': 'flex', 'flex-direction': 'row'}),
    dcc.Slider(
        id='month-slider',
        min=0,
        max=n_months-1,
        value=0,
        marks={i: f'Month {i+1}' for i in range(0, n_months, max(1, n_months//10))},
        step=1
    ),
    # Store previous frame indices
    dcc.Store(id='prev-month', data=0)
])

@app.callback(
    Output('graph-cap', 'figure'),
    Output('graph-nocap', 'figure'),
    Output('sidebar-stats', 'children'),
    Output('movement-log-cap', 'children'),
    Output('movement-log-nocap', 'children'),
    Output('prev-month', 'data'),
    Input('month-slider', 'value'),
    Input('prev-month', 'data')
)
def update_figures(month_idx, prev_month_idx):
    frame_cap = frames_cap[month_idx]
    frame_nocap = frames_nocap[month_idx]
    
    # Get previous frames if available
    prev_frame_cap = frames_cap[prev_month_idx] if prev_month_idx < month_idx else None
    prev_frame_nocap = frames_nocap[prev_month_idx] if prev_month_idx < month_idx else None
    
    fig_cap = make_figure(frame_cap, grid_size, prev_frame_cap, True)
    fig_nocap = make_figure(frame_nocap, grid_size, prev_frame_nocap, False)

    # Sidebar metrics
    owner_share_cap = sum(u['is_owner_occupied'] for u in frame_cap) / len(frame_cap)
    owner_share_nocap = sum(u['is_owner_occupied'] for u in frame_nocap) / len(frame_nocap)
    avg_mortgage_cap = np.mean([u['property_value'] for u in frame_cap if u['is_owner_occupied']]) if any(u['is_owner_occupied'] for u in frame_cap) else 0
    avg_mortgage_nocap = np.mean([u['property_value'] for u in frame_nocap if u['is_owner_occupied']]) if any(u['is_owner_occupied'] for u in frame_nocap) else 0

    sidebar_stats = html.Div([
        html.H3(f"Month: {month_idx+1}"),
        html.H4("With Rent Cap"),
        html.P(f"Owner-Occupier Share: {owner_share_cap:.1%}"),
        html.P(f"Avg Property Value (owners): ${avg_mortgage_cap:.0f}"),
        html.P(f"Avg Satisfaction: {np.mean([u['tenant_satisfaction'] for u in frame_cap if u['tenant_satisfaction'] is not None]):.2f}"),
        html.H4("No Rent Cap"),
        html.P(f"Owner-Occupier Share: {owner_share_nocap:.1%}"),
        html.P(f"Avg Property Value (owners): ${avg_mortgage_nocap:.0f}"),
    ])

    # Movement logs
    movement_log_cap = []
    if month_idx < len(movement_logs_cap):
        for move in movement_logs_cap[month_idx]:
            movement_log_cap.append(html.P(move, style={'margin': '5px 0'}))

    movement_log_nocap = []
    if month_idx < len(movement_logs_nocap):
        for move in movement_logs_nocap[month_idx]:
            movement_log_nocap.append(html.P(move, style={'margin': '5px 0'}))

    return fig_cap, fig_nocap, sidebar_stats, movement_log_cap, movement_log_nocap, month_idx

if __name__ == '__main__':
    app.run(debug=True)
