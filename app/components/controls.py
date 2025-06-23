from dash import html, dcc

def create_controls():
    button_base_style = {
        'padding': '10px 20px',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer',
        'marginRight': '10px',
        'transition': 'all 0.3s ease',
        'width': '100px',
    }
    
    play_style = {
        **button_base_style,
        'backgroundColor': '#28a745',
        'color': 'white',
    }
    
    pause_style = {
        **button_base_style,
        'backgroundColor': '#dc3545',
        'color': 'white',
    }
    
    reset_style = {
        **button_base_style,
        'backgroundColor': '#6c757d',
        'color': 'white',
        'marginRight': '0'
    }

    return html.Div([
        # Period slider
        html.Div([
            html.Label("Time Period"),
            dcc.Slider(
                id='period-slider',
                min=0,
                max=12,  # 12 months
                step=1,
                value=0,
                marks={i: f'Month {i}' for i in range(13)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'marginBottom': '20px'}),
        
        # Control buttons
        html.Div([
            html.Button('▶ Play', 
                       id='play-button',
                       n_clicks=0,
                       style=play_style),
            html.Button('⏸ Pause',
                       id='pause-button',
                       n_clicks=0,
                       style=pause_style),
            html.Button('⟲ Reset',
                       id='reset-button',
                       n_clicks=0,
                       style=reset_style)
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        # Simulation status
        html.Div("Simulation Ready", 
                 id='simulation-status',
                 style={
                     'textAlign': 'center',
                     'marginBottom': '20px',
                     'padding': '10px',
                     'backgroundColor': '#e9ecef',
                     'borderRadius': '5px',
                     'fontWeight': 'bold'
                 }),
        
        # Auto-stepper interval
        dcc.Interval(
            id='auto-stepper',
            interval=3000,  # Increased to 3 seconds to ensure steps complete
            n_intervals=0,
            disabled=True
        ),
        
        # Scenario selector
        html.Div([
            html.Label("Scenario", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
            dcc.RadioItems(
                id='scenario-selector',
                options=[
                    {'label': ' Rent Cap', 'value': 'capped'},
                    {'label': ' No Cap', 'value': 'uncapped'}
                ],
                value='capped',
                labelStyle={'display': 'block', 'marginBottom': '10px'},
                style={'marginLeft': '20px'}
            )
        ], style={'marginBottom': '20px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '5px'}),

        # Simulation parameters
        html.Div([
            html.Label("Initial Number of Households", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
            dcc.Input(
                id='initial-households-input',
                type='number',
                value=20,
                min=1,
                style={'width': '100%', 'padding': '8px', 'marginBottom': '15px', 'borderRadius': '4px', 'border': '1px solid #ced4da'}
            ),
            html.Label("Migration Rate", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
            dcc.Slider(
                id='migration-rate-slider',
                min=0,
                max=1,
                step=0.01,
                value=0.1,
                marks={0: '0', 0.25: '0.25', 0.5: '0.5', 0.75: '0.75', 1: '1'},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'marginTop': '20px', 'backgroundColor': '#ffffff', 'padding': '15px', 'borderRadius': '5px'})
    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}) 