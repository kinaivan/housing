from dash import html, dcc

def create_graph():
    return html.Div([
        html.H2("Housing Market Simulation", style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#2c3e50', 'fontWeight': '400'}),
        dcc.Graph(
            id='sim-graph',
            style={'height': '700px', 'maxWidth': '900px', 'margin': '0 auto'},
            config={'displayModeBar': True}
        )
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '5px', 'boxShadow': '0 2px 10px rgba(0,0,0,0.1)', 'maxWidth': '950px', 'margin': '0 auto'}) 