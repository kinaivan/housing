from dash import Dash

from app.layout import layout
from app.callbacks import register_callbacks

app = Dash(
    __name__, 
    suppress_callback_exceptions=True,
    update_title=None  # Prevents the "Updating..." browser title
)

app.title = "Housing Market Simulation"
app.layout = layout
register_callbacks(app)

if __name__ == '__main__':
    app.run_server(
        debug=False,  # Disable debug mode to prevent auto-reloads
        dev_tools_hot_reload=False,  # Explicitly disable hot-reloading
        dev_tools_props_check=False  # Disable props validation which can cause reloads
    )