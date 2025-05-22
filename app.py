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

def make_house_shapes(frame, grid_size):
    shapes = []
    annotations = []
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
        # Optionally, add stick figures or icons here as more shapes/annotations

        # Tooltip annotation (hidden, but used for hover)
        annotations.append(dict(
            x=x, y=y+0.45, text=(
                f"Unit {u['unit_id']}<br>"
                f"{'Owner-Occupied' if u['is_owner_occupied'] else ('Rented' if u['occupied'] else 'Vacant')}<br>"
                f"Rent: ${u['rent']:.0f}<br>"
                f"Quality: {u['quality']:.2f}<br>"
                f"Property Value: ${u['property_value']:.0f}<br>"
                f"Tenant Size: {u['tenant_size']}"
            ),
            showarrow=False,
            font=dict(size=10),
            align="left",
            opacity=0  # Hide by default, used for hover
        ))
    return shapes, annotations

def make_figure(frame, grid_size):
    shapes, annotations = make_house_shapes(frame, grid_size)
    # Add invisible scatter for hover
    x = []
    y = []
    hover = []
    for i, u in enumerate(frame):
        row, col = divmod(i, grid_size)
        x.append(col)
        y.append(grid_size - row - 1)
        hover.append(
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
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode='markers',
        marker=dict(size=1, color='rgba(0,0,0,0)'),  # invisible, just for hover
        text=hover, hoverinfo='text'
    ))
    fig.update_layout(
        shapes=shapes,
        annotations=[],  # You can use for static labels if you want
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-1, grid_size]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-1, grid_size]),
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='white',
        height=700
    )
    return fig

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Housing Market Simulation: Side-by-Side"),
    html.Div([
        dcc.Graph(id='graph-cap', style={'height': '80vh', 'width': '40vw'}),
        dcc.Graph(id='graph-nocap', style={'height': '80vh', 'width': '40vw'}),
        html.Div(id='sidebar', style={'width': '18vw', 'padding': '2vw'})
    ], style={'display': 'flex', 'flex-direction': 'row'}),
    dcc.Slider(
        id='month-slider',
        min=0,
        max=n_months-1,
        value=0,
        marks={i: f'Month {i+1}' for i in range(0, n_months, max(1, n_months//10))},
        step=1
    )
])

@app.callback(
    Output('graph-cap', 'figure'),
    Output('graph-nocap', 'figure'),
    Output('sidebar', 'children'),
    Input('month-slider', 'value')
)
def update_figures(month_idx):
    frame_cap = frames_cap[month_idx]
    frame_nocap = frames_nocap[month_idx]
    fig_cap = make_figure(frame_cap, grid_size)
    fig_nocap = make_figure(frame_nocap, grid_size)

    # Sidebar metrics (example, you can add more)
    owner_share_cap = sum(u['is_owner_occupied'] for u in frame_cap) / len(frame_cap)
    owner_share_nocap = sum(u['is_owner_occupied'] for u in frame_nocap) / len(frame_nocap)
    avg_mortgage_cap = np.mean([u['property_value'] for u in frame_cap if u['is_owner_occupied']]) if any(u['is_owner_occupied'] for u in frame_cap) else 0
    avg_mortgage_nocap = np.mean([u['property_value'] for u in frame_nocap if u['is_owner_occupied']]) if any(u['is_owner_occupied'] for u in frame_nocap) else 0

    sidebar = html.Div([
        html.H3(f"Month: {month_idx+1}"),
        html.H4("With Rent Cap"),
        html.P(f"Owner-Occupier Share: {owner_share_cap:.1%}"),
        html.P(f"Avg Property Value (owners): ${avg_mortgage_cap:.0f}"),
        html.P(f"Avg Satisfaction: {np.mean([u['tenant_satisfaction'] for u in frame_cap if u['tenant_satisfaction'] is not None]):.2f}"),
        html.H4("No Rent Cap"),
        html.P(f"Owner-Occupier Share: {owner_share_nocap:.1%}"),
        html.P(f"Avg Property Value (owners): ${avg_mortgage_nocap:.0f}"),
        # Add more metrics as you wish!
    ])
    return fig_cap, fig_nocap, sidebar

if __name__ == '__main__':
    app.run(debug=True)
