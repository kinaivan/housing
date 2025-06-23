from dash import Output, Input, State, callback_context, no_update
from dash import dcc
from app.pages.simulation_page import simulation_page_layout
from app.pages.landlord_page import landlord_page_layout
from app.pages.about_page import about_page_layout

def register_navigation_callbacks(app):
    @app.callback(
        Output('page-content', 'children'),
        Output('nav-simulation', 'className'),
        Output('nav-landlord', 'className'),
        Output('nav-about', 'className'),
        Input('nav-simulation', 'n_clicks'),
        Input('nav-landlord', 'n_clicks'),
        Input('nav-about', 'n_clicks'),
        prevent_initial_call=True
    )
    def navigate(sim_click, landlord_click, about_click):
        ctx = callback_context
        if not ctx.triggered:
            # Default to simulation page
            return simulation_page_layout(), 'nav-button active', 'nav-button', 'nav-button'
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'nav-simulation':
            return simulation_page_layout(), 'nav-button active', 'nav-button', 'nav-button'
        elif button_id == 'nav-landlord':
            return landlord_page_layout(), 'nav-button', 'nav-button active', 'nav-button'
        elif button_id == 'nav-about':
            return about_page_layout(), 'nav-button', 'nav-button', 'nav-button active'
        else:
            return simulation_page_layout(), 'nav-button active', 'nav-button', 'nav-button'

    # ... move navigation callbacks here ...
    pass 