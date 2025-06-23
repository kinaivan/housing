from dash import html, dcc

def create_sidebar():
    return html.Div([
        # Stats section
        html.Div([
            html.Div(id='sidebar-stats')
        ], style={'marginBottom': '20px'}),
        
        # Movement log
        html.Div([
            html.H4("Recent Activity"),
            html.Div(id='movement-log', style={'maxHeight': '200px', 'overflowY': 'auto', 'backgroundColor': '#f8f9fa', 'border': '2px solid #3498db', 'borderRadius': '8px', 'padding': '10px', 'fontFamily': 'monospace', 'fontSize': '13px', 'color': '#222'})
        ]),
        
        # Back button (hidden by default)
        html.Button(
            '← Back to Overview',
            id={'type': 'back-button', 'index': 'main'},
            style={
                'display': 'none',
                'backgroundColor': '#6c757d',
                'color': 'white',
                'padding': '10px 20px',
                'border': 'none',
                'borderRadius': '5px',
                'cursor': 'pointer',
                'marginTop': '20px'
            }
        )
    ], style={
        'width': '300px',
        'padding': '20px',
        'backgroundColor': '#f8f9fa',
        'borderRadius': '5px',
        'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
    }) 