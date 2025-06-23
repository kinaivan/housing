# # from .controls import register_control_callbacks  # Commented out to prevent conflicts
# # from .graph import register_graph_callbacks  # Commented out to prevent conflicts
# from .sidebar import register_sidebar_callbacks
# # from .navigation import register_navigation_callbacks  # Commented out to prevent conflicts
# from .landlord import register_landlord_callbacks

# def register_callbacks(app):
#     """Register all callbacks with the app"""
#     # register_control_callbacks(app)  # Commented out to prevent conflicts
#     # register_graph_callbacks(app)  # Commented out to prevent conflicts
#     register_sidebar_callbacks(app)
#     # register_navigation_callbacks(app)  # Commented out to prevent conflicts
#     register_landlord_callbacks(app)
#     from .simulation_callbacks import register_simulation_callbacks
#     from .navigation_callbacks import register_navigation_callbacks
#     register_simulation_callbacks(app)
#     register_navigation_callbacks(app)

def register_callbacks(app):
    from .simulation_callbacks import register_simulation_callbacks
    from .landlord_callbacks import register_landlord_callbacks
    from .navigation_callbacks import register_navigation_callbacks
    register_simulation_callbacks(app)
    register_landlord_callbacks(app)
    register_navigation_callbacks(app)