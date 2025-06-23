from dash import html, dcc

def create_landlord_page():
    return html.Div([
        html.H2("Landlord Investment Calculator", 
                style={
                    'textAlign': 'center', 
                    'marginBottom': '30px',
                    'color': '#2c3e50',
                    'fontSize': '2.5rem',
                    'fontWeight': '300',
                    'borderBottom': '3px solid #3498db',
                    'paddingBottom': '10px'
                }),
        
        # Calculator form
        html.Div([
            # Input fields
            html.Div([
                html.H3("Property Details", style={'color': '#2c3e50', 'marginBottom': '20px'}),
                
                # Property Information
                html.Div([
                    html.Label("Property Value", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='property-value',
                        type='number',
                        value=500000,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Current Rent", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='current-rent',
                        type='number',
                        value=2000,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Number of Units", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='num-units',
                        type='number',
                        value=1,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Vacancy Rate (%)", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='vacancy-rate',
                        type='number',
                        value=5.0,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    )
                ], style={'marginBottom': '30px'}),
                
                # Operating Expenses
                html.H3("Operating Expenses", style={'color': '#2c3e50', 'marginBottom': '20px'}),
                html.Div([
                    html.Label("Annual Maintenance Cost", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='maintenance-cost',
                        type='number',
                        value=5000,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Property Tax Rate (%)", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='tax-rate',
                        type='number',
                        value=2.0,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Insurance Cost", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='insurance-cost',
                        type='number',
                        value=2000,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Property Management Fee (%)", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='management-fee',
                        type='number',
                        value=8.0,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    )
                ], style={'marginBottom': '30px'}),
                
                # Market Conditions
                html.H3("Market Conditions", style={'color': '#2c3e50', 'marginBottom': '20px'}),
                html.Div([
                    html.Label("Rent Cap (%)", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='rent-cap',
                        type='number',
                        value=5.0,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Expected Appreciation (%)", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='appreciation-rate',
                        type='number',
                        value=3.0,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    ),
                    
                    html.Label("Mortgage Rate (%)", style={'fontWeight': 'bold', 'color': '#34495e'}),
                    dcc.Input(
                        id='mortgage-rate',
                        type='number',
                        value=4.5,
                        style={'width': '100%', 'padding': '12px', 'marginBottom': '15px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}
                    )
                ])
            ], style={
                'flex': '1', 
                'padding': '30px', 
                'backgroundColor': 'white', 
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
                'marginRight': '20px'
            }),
            
            # Results
            html.Div([
                html.H3("Investment Analysis", style={'color': '#2c3e50', 'marginBottom': '20px'}),
                
                # Revenue Section
                html.Div([
                    html.H4("Revenue", style={'color': '#27ae60', 'marginBottom': '15px'}),
                    html.Div([
                        html.Div([
                            html.H5("Gross Annual Revenue", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='gross-revenue', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#27ae60', 'marginBottom': '20px'})
                        ]),
                        html.Div([
                            html.H5("Effective Annual Revenue", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='effective-revenue', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#27ae60', 'marginBottom': '20px'})
                        ])
                    ])
                ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
                
                # Expenses Section
                html.Div([
                    html.H4("Expenses", style={'color': '#e74c3c', 'marginBottom': '15px'}),
                    html.Div([
                        html.Div([
                            html.H5("Total Annual Expenses", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='total-expenses', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#e74c3c', 'marginBottom': '20px'})
                        ]),
                        html.Div([
                            html.H5("Monthly Mortgage Payment", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='mortgage-payment', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#e74c3c', 'marginBottom': '20px'})
                        ])
                    ])
                ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
                
                # Returns Section
                html.Div([
                    html.H4("Returns", style={'color': '#3498db', 'marginBottom': '15px'}),
                    html.Div([
                        html.Div([
                            html.H5("Net Operating Income", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='net-income', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#3498db', 'marginBottom': '20px'})
                        ]),
                        html.Div([
                            html.H5("Cash Flow", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='cash-flow', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#3498db', 'marginBottom': '20px'})
                        ]),
                        html.Div([
                            html.H5("Return on Investment", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='roi', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#3498db', 'marginBottom': '20px'})
                        ]),
                        html.Div([
                            html.H5("Total Return (with Appreciation)", style={'color': '#34495e', 'marginBottom': '5px'}),
                            html.Div(id='total-return', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#3498db'})
                        ])
                    ])
                ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
            ], style={
                'flex': '1', 
                'padding': '30px', 
                'backgroundColor': 'white', 
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })
        ], style={
            'display': 'flex', 
            'gap': '20px', 
            'maxWidth': '1400px', 
            'margin': '0 auto'
        })
    ], style={
        'padding': '40px',
        'backgroundColor': '#f5f6fa',
        'minHeight': '100vh'
    }) 