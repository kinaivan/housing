from dash import html, dcc
from app.pages.simulation_page import simulation_page_layout
from app.pages.landlord_page import landlord_page_layout
from app.pages.about_page import about_page_layout

layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Navigation bar
    html.Div([
        html.H1("Housing Market Simulation", style={"textAlign": "center", "margin": "0"}),
        html.Div([
            html.Button("Simulation", id="nav-simulation", className="nav-button active"),
            html.Button("Landlord Calculator", id="nav-landlord", className="nav-button"),
            html.Button("About", id="nav-about", className="nav-button")
        ], style={"textAlign": "center", "margin": "10px 0"})
    ], style={"backgroundColor": "#f8f9fa", "padding": "10px", "marginBottom": "20px"}),
    # Page content
    html.Div(id="page-content", children=simulation_page_layout())
]) 