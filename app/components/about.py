from dash import html, dcc

def create_about_page():
    return html.Div([
        html.H1("About the Housing Market Simulation Model", style={'marginBottom': '30px'}),
        
        html.Div([
            # Introduction Section
            html.Div([
                html.H2("How the Model Works", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                
                # Visual representation of key components
                html.Div([
                    html.Div([
                        html.Div(style={
                            'width': '100px',
                            'height': '100px',
                            'backgroundColor': 'royalblue',
                            'margin': '10px',
                            'position': 'relative',
                            'display': 'inline-block'
                        }, children=[
                            html.Div(style={
                                'width': '0',
                                'height': '0',
                                'borderLeft': '50px solid transparent',
                                'borderRight': '50px solid transparent',
                                'borderBottom': '40px solid #d95f02',
                                'position': 'absolute',
                                'top': '-40px',
                                'left': '0'
                            })
                        ]),
                        html.P("Owner-Occupied", style={'textAlign': 'center'})
                    ], style={'display': 'inline-block', 'margin': '10px'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '100px',
                            'height': '100px',
                            'backgroundColor': 'limegreen',
                            'margin': '10px',
                            'position': 'relative',
                            'display': 'inline-block'
                        }, children=[
                            html.Div(style={
                                'width': '0',
                                'height': '0',
                                'borderLeft': '50px solid transparent',
                                'borderRight': '50px solid transparent',
                                'borderBottom': '40px solid #d95f02',
                                'position': 'absolute',
                                'top': '-40px',
                                'left': '0'
                            })
                        ]),
                        html.P("Rented", style={'textAlign': 'center'})
                    ], style={'display': 'inline-block', 'margin': '10px'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '100px',
                            'height': '100px',
                            'backgroundColor': 'lightgray',
                            'margin': '10px',
                            'position': 'relative',
                            'display': 'inline-block'
                        }, children=[
                            html.Div(style={
                                'width': '0',
                                'height': '0',
                                'borderLeft': '50px solid transparent',
                                'borderRight': '50px solid transparent',
                                'borderBottom': '40px solid #d95f02',
                                'position': 'absolute',
                                'top': '-40px',
                                'left': '0'
                            })
                        ]),
                        html.P("Vacant", style={'textAlign': 'center'})
                    ], style={'display': 'inline-block', 'margin': '10px'})
                ], style={'textAlign': 'center', 'marginBottom': '30px'}),

                html.H3("Key Components:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Housing Units: Each square represents a housing unit that can be either owner-occupied (blue), rented (green), or vacant (gray)"),
                    html.Li("Households: Represented by stick figures - owners (blue), renters (green), and unhoused (red)"),
                    html.Li("Monthly Simulation: The model advances month by month, simulating various market interactions"),
                ], style={'marginBottom': '30px'}),
            ]),

            # New Section: Tenant Search Process
            html.Div([
                html.H2("Tenant Search Process", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                html.P([
                    "The tenant search process occurs simultaneously for all households at each time step. Here's how it works:",
                    html.Ul([
                        html.Li("All households evaluate their current situation at the same time"),
                        html.Li("Each household calculates their satisfaction score based on multiple factors"),
                        html.Li("Households then search for new housing in parallel, with the following priority:"),
                        html.Ul([
                            html.Li("Unhoused households get first priority in unit selection"),
                            html.Li("Households with lower satisfaction scores get higher priority"),
                            html.Li("When multiple households want the same unit, the one with the best matching criteria (income, size, preferences) gets priority")
                        ])
                    ])
                ], style={'marginBottom': '20px'}),
            ]),

            # New Section: Tenant Movement Motivations
            html.Div([
                html.H2("What Motivates Tenants to Move?", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                html.Div([
                    # Visual representation of tenant motivations
                    html.Div([
                        html.Div(style={
                            'border': '2px solid #3498db',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Financial Factors", style={'color': '#3498db'}),
                            html.Ul([
                                html.Li("High rent burden (>50% of income)"),
                                html.Li("Significant rent increases"),
                                html.Li("Better affordability elsewhere")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #2ecc71',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Quality of Life", style={'color': '#2ecc71'}),
                            html.Ul([
                                html.Li("Low housing quality"),
                                html.Li("Inadequate unit size for household"),
                                html.Li("Poor location score")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #e74c3c',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Life Changes", style={'color': '#e74c3c'}),
                            html.Ul([
                                html.Li("Changes in household size"),
                                html.Li("Income changes"),
                                html.Li("Life stage transitions")
                            ])
                        ])
                    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'})
                ])
            ]),

            # New Section: Landlord Pricing Motivations
            html.Div([
                html.H2("What Drives Landlord Pricing?", style={'marginBottom': '20px', 'color': '#2c3e50'}),
                html.Div([
                    # Visual representation of landlord motivations
                    html.Div([
                        html.Div(style={
                            'border': '2px solid #9b59b6',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Market Conditions", style={'color': '#9b59b6'}),
                            html.Ul([
                                html.Li("Local vacancy rates"),
                                html.Li("Average market rents"),
                                html.Li("Seasonal demand changes")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #f1c40f',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Property Factors", style={'color': '#f1c40f'}),
                            html.Ul([
                                html.Li("Unit quality and amenities"),
                                html.Li("Recent renovations"),
                                html.Li("Location desirability")
                            ])
                        ]),
                        html.Div(style={
                            'border': '2px solid #e67e22',
                            'borderRadius': '10px',
                            'padding': '15px',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa'
                        }, children=[
                            html.H4("Regulatory Environment", style={'color': '#e67e22'}),
                            html.Ul([
                                html.Li("Rent control policies"),
                                html.Li("Property tax rates"),
                                html.Li("Inspection requirements")
                            ])
                        ])
                    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'})
                ])
            ]),

            # Original Parameters Section
            html.H2("Key Parameters", style={'marginBottom': '20px', 'color': '#2c3e50'}),
            html.Div([
                html.H3("Housing Unit Parameters:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Quality: Affects property value and tenant satisfaction"),
                    html.Li("Rent: Monthly payment for tenants"),
                    html.Li("Property Value: Current market value of the unit"),
                ], style={'marginBottom': '20px'}),
                
                html.H3("Household Parameters:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Income: Monthly household income"),
                    html.Li("Wealth: Accumulated savings and assets"),
                    html.Li("Size: Number of household members"),
                    html.Li("Life Stage: Affects housing preferences and decisions"),
                    html.Li("Satisfaction: Measure of contentment with current housing situation"),
                ], style={'marginBottom': '20px'}),
                
                html.H3("Market Parameters:", style={'marginBottom': '15px', 'color': '#2c3e50'}),
                html.Ul([
                    html.Li("Rent Cap (in cap scenario): Maximum allowed rent increase"),
                    html.Li("Mortgage Rates: Affects monthly payments for buyers"),
                    html.Li("Market Demand: Overall housing demand in the area")
                ])
            ])
        ], style={
            'maxWidth': '1200px',
            'margin': '0 auto',
            'padding': '20px',
            'lineHeight': '1.6',
            'fontSize': '16px',
            'backgroundColor': 'white',
            'boxShadow': '0 0 10px rgba(0,0,0,0.1)',
            'borderRadius': '10px'
        })
    ], style={'backgroundColor': '#f5f6fa', 'minHeight': '100vh', 'padding': '20px'}) 