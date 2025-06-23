from dash import html, dcc
from app.components.sidebar import create_sidebar
from app.components.graph import create_graph
from app.components.controls import create_controls

def simulation_page_layout():
    return html.Div([
        html.Div([
            create_sidebar(),
            html.Div([
                create_graph(),
                create_controls()
            ], style={'flex': '1', 'marginLeft': '20px'})
        ], style={'display': 'flex', 'margin': '20px'})
    ]) 