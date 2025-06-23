from dash import html, dcc
# Import or define your landlord calculator layout here

def landlord_page_layout():
    return html.Div([
        html.H1("Landlord Investment Calculator", style={
            'fontFamily': 'Helvetica Neue, Arial, sans-serif',
            'fontSize': '2rem',
            'fontWeight': '300',
            'color': '#2c3e50',
            'marginBottom': '20px',
            'textAlign': 'center'
        }),
        dcc.Store(id='landlord-history-store', data=[]),
        html.Div([
            # Main calculator container
            html.Div([
                # Investment Input Section
                html.Div([
                    html.H3("Investment Parameters", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Number of Units:", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Input(
                            id='units-input',
                            type='number',
                            value=5,
                            style={'width': '100%', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Average Purchase Price per Unit (€):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Input(
                            id='purchase-price-input',
                            type='number',
                            value=350000,
                            style={'width': '100%', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Average Monthly Rent per Unit (€):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Input(
                            id='monthly-rent-input',
                            type='number',
                            value=1800,
                            style={'width': '100%', 'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ddd'}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Down Payment (%):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Slider(
                            id='down-payment-slider',
                            min=0,
                            max=100,
                            step=1,
                            value=35,
                            marks={0: '0%', 10: '10%', 20: '20%', 30: '30%', 40: '40%', 50: '50%', 100: '100%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Interest Rate (%):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Slider(
                            id='mortgage-rate-slider',
                            min=0,
                            max=10,
                            step=0.05,
                            value=3.5,
                            marks={0: '0%', 2: '2%', 3: '3%', 4: '4%', 5: '5%', 6: '6%', 10: '10%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Loan Term (Years):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Slider(
                            id='loan-term-slider',
                            min=5,
                            max=40,
                            step=1,
                            value=30,
                            marks={10: '10', 15: '15', 20: '20', 25: '25', 30: '30', 40: '40'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Property Tax Rate (%):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Slider(
                            id='property-tax-slider',
                            min=0.0,
                            max=2.0,
                            step=0.01,
                            value=0.6,
                            marks={0.0: '0%', 0.5: '0.5%', 1.0: '1%', 1.5: '1.5%', 2.0: '2%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Maintenance & Management (% of rent):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Slider(
                            id='maintenance-rate-slider',
                            min=0,
                            max=20,
                            step=0.1,
                            value=8,
                            marks={0: '0%', 5: '5%', 8: '8%', 10: '10%', 15: '15%', 20: '20%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'marginBottom': '15px'}),
                    html.Div([
                        html.Label("Annual Appreciation Rate (%):", style={'fontWeight': '500', 'marginBottom': '5px'}),
                        dcc.Slider(
                            id='appreciation-rate-slider',
                            min=0,
                            max=10,
                            step=0.01,
                            value=2.0,
                            marks={0: '0%', 1: '1%', 2: '2%', 3: '3%', 4: '4%', 5: '5%', 10: '10%'},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'marginBottom': '20px'}),
                    html.Button('Calculate Investment', id='calculate-button', style={
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'padding': '12px 24px',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'fontWeight': '500',
                        'fontSize': '16px',
                        'width': '100%',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                        'transition': 'background-color 0.3s ease'
                    })
                ])
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '10px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.1)',
                'marginRight': '20px'
            }),
            # Results Section
            html.Div([
                html.H3("Investment Analysis", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                dcc.Dropdown(id='landlord-history-dropdown', placeholder='Select a previous calculation to view', style={'marginBottom': '10px'}),
                html.Div(id='landlord-calculator-results', style={
                    'backgroundColor': '#f8f9fa',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'fontFamily': 'monospace',
                    'fontSize': '14px',
                    'lineHeight': '1.6',
                    'marginBottom': '20px'
                }),
                dcc.Graph(id='cash-flow-chart', style={'height': '400px', 'marginBottom': '20px'}),
                dcc.Graph(id='roi-chart', style={'height': '400px'})
            ], style={
                'flex': '1',
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '10px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
            })
        ], style={
            'display': 'flex',
            'margin': '20px',
            'gap': '20px'
        })
    ], style={
        'backgroundColor': '#f5f6fa',
        'minHeight': '100vh',
        'padding': '20px'
    }) 