from dash import html, dcc

def create_comparison_page():
    return html.Div([
        html.H2("Market Comparison", style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # Main content area
        html.Div([
            # Left panel - Capped market
            html.Div([
                html.H3("Rent Cap Scenario"),
                html.Div([
                    # Market statistics
                    html.Div([
                        html.H4("Market Statistics"),
                        html.Div(id='capped-stats')
                    ], style={'marginBottom': '20px'}),
                    
                    # Price trends
                    html.Div([
                        html.H4("Price Trends"),
                        dcc.Graph(id='capped-price-trend')
                    ], style={'marginBottom': '20px'}),
                    
                    # Occupancy rates
                    html.Div([
                        html.H4("Occupancy Rates"),
                        dcc.Graph(id='capped-occupancy')
                    ])
                ])
            ], style={'flex': '1', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '5px', 'marginRight': '20px'}),
            
            # Right panel - Uncapped market
            html.Div([
                html.H3("No Cap Scenario"),
                html.Div([
                    # Market statistics
                    html.Div([
                        html.H4("Market Statistics"),
                        html.Div(id='uncapped-stats')
                    ], style={'marginBottom': '20px'}),
                    
                    # Price trends
                    html.Div([
                        html.H4("Price Trends"),
                        dcc.Graph(id='uncapped-price-trend')
                    ], style={'marginBottom': '20px'}),
                    
                    # Occupancy rates
                    html.Div([
                        html.H4("Occupancy Rates"),
                        dcc.Graph(id='uncapped-occupancy')
                    ])
                ])
            ], style={'flex': '1', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '5px'})
        ], style={'display': 'flex', 'marginBottom': '30px'}),
        
        # Bottom panel - Key metrics comparison
        html.Div([
            html.H3("Key Metrics Comparison"),
            html.Div([
                html.Div([
                    html.H4("Average Rent"),
                    html.Div(id='avg-rent-comparison')
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '20px'}),
                
                html.Div([
                    html.H4("Vacancy Rate"),
                    html.Div(id='vacancy-comparison')
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '20px'}),
                
                html.Div([
                    html.H4("Unhoused Population"),
                    html.Div(id='unhoused-comparison')
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '20px'})
            ], style={'display': 'flex', 'justifyContent': 'space-around'})
        ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '5px'})
    ], style={'padding': '20px'}) 