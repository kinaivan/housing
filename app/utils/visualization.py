import plotly.graph_objects as go
import numpy as np

# Constants for visualization
HOUSE_MARGIN = 1.8  # Reduced from 2.4
HOUSE_WIDTH = 1.2  # Reduced from 1.6
ROOF_WIDTH = HOUSE_WIDTH  # Match roof width to house width
ROOF_HEIGHT = 0.4  # Height of the roof peak
PERSON_WIDTH = 0.2  # Reduced from 0.3
PERSON_SPACING = 0.1  # Reduced from 0.15

def get_positions(n, columns=None):
    """Calculate grid positions for n items with margin to avoid overlap.

    If `columns` is provided, use that many columns (fixed grid width). Otherwise, use a square grid.
    Returns list of (x, y) positions and a tuple (cols, rows).
    """
    if columns is None:
        columns = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / columns))
    positions = []
    for i in range(n):
        row = i // columns
        col = i % columns
        # Invert the y-axis calculation to start from top and go down
        positions.append((col * (1 + HOUSE_MARGIN), -row * (1 + HOUSE_MARGIN)))
    return positions, (columns, rows)

def make_figure(frame, grid_size, prev_frame=None, is_cap_scenario=True, layers=None, show_unhoused=True):
    """Create the visualization figure"""
    if frame is None:
        return go.Figure()
    n = len(frame['units'])
    # Fixed 5 columns for nicer aspect (4 rows for 20 units)
    positions, (n_cols, n_rows) = get_positions(n, columns=5)
    fig = go.Figure()
    
    # Create occupancy dictionary for easier lookup
    occupancy_dict = {}
    for unit_id, hh_id, _ in frame['occupancy']:
        if hh_id is not None:
            # Find all households in this unit
            unit = next((u for u in frame['units'] if u.id == unit_id), None)
            if unit and unit.tenants:
                # Sum up the sizes of all households in the unit
                total_size = sum(tenant.size for tenant in unit.tenants if tenant and hasattr(tenant, 'size'))
                occupancy_dict[unit_id] = (hh_id, total_size)
            else:
                occupancy_dict[unit_id] = (hh_id, 0)
        else:
            occupancy_dict[unit_id] = (None, 0)
    
    prev_hh_locations = {}
    if prev_frame is not None:
        prev_occ = {unit_id: hh_id for unit_id, hh_id, _ in prev_frame['occupancy']}
        for unit_id, hh_id in prev_occ.items():
            prev_hh_locations[hh_id] = unit_id

    current_hh_locations = {hh_id: unit_id for unit_id, hh_id, _ in frame['occupancy']}
    
    # Get events from households
    events = []
    for household in frame.get('households', []):
        if hasattr(household, 'timeline') and household.timeline:
            latest_events = [event for event in household.timeline if event.record.get('type') in ['MOVED_IN', 'HOUSEHOLD_BREAKUP', 'HOUSEHOLD_MERGER']]
            if latest_events:
                latest_event = latest_events[-1]  # Get most recent event
                events.append((household.id, latest_event.record))

    # Add houses with hover information
    for i, unit in enumerate(frame['units']):
        x, y = positions[i]
        
        # Get occupancy info
        hh_id, size = occupancy_dict.get(unit.id, (None, 0))
        
        # House color based on status
        if unit.landlord is None:  # Owner-occupied
            color = 'royalblue'
            status = 'Owner-occupied'
        elif hh_id is not None:  # Rented
            color = 'limegreen'
            status = 'Rented'
        else:  # Vacant
            color = 'lightgray'
            status = 'Vacant'
            
        # Create hover text with detailed information
        hover_text = f"Unit {unit.id}<br>"
        hover_text += f"Status: {status}<br>"
        hover_text += f"Base Rent: €{unit.base_rent:.2f}<br>"
        hover_text += f"Current Rent: €{unit.rent:.2f}<br>"
        hover_text += f"Quality: {unit.quality:.2f}<br>"
        
        if hh_id is not None:
            # Find the household(s) living in this unit
            tenants = unit.tenants if hasattr(unit, 'tenants') else []
            for tenant in tenants:
                if tenant:
                    hover_text += f"<br>Household {tenant.id}:<br>"
                    hover_text += f"- Size: {tenant.size}<br>"
                    hover_text += f"- Income: €{tenant.income:.2f}<br>"
                    hover_text += f"- Age: {tenant.age}<br>"
                    hover_text += f"- Wealth: €{tenant.wealth:.2f}<br>"
        
        # Add house rectangle with hover
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                symbol='square',
                size=60,  # Reduced from 80
                color=color,
                line=dict(color="black", width=2)
            ),
            text=hover_text,
            hoverinfo='text',
            showlegend=False
        ))
            
        # Add roof (triangle) - matched to house width
        half_width = ROOF_WIDTH / 2
        fig.add_shape(
            type="path",
            path=f'M {x-half_width},{y+0.6} L {x},{y+0.6+ROOF_HEIGHT} L {x+half_width},{y+0.6} Z',
            line=dict(color="black", width=2),
            fillcolor="#d95f02",  # Orange roof
            layer="below"
        )
        
        # Add people if unit is occupied
        if hh_id is not None or unit.landlord is None:
            # Calculate starting position for centered group of people
            total_width = size * PERSON_WIDTH
            start_x = x - total_width / 2 + PERSON_SPACING
            
            for j in range(size):
                px = start_x + j * PERSON_WIDTH
                py = y - 0.05
                
                # Add stick figure
                # Head
                fig.add_shape(
                    type="circle",
                    x0=px-0.06, y0=py+0.03, x1=px+0.06, y1=py+0.15,
                    line=dict(color="black", width=1),
                    fillcolor="rgba(27,158,119,1)" if unit.landlord is not None else "rgba(55,119,194,1)",
                    layer="above"
                )
                # Body
                fig.add_shape(
                    type="line",
                    x0=px, y0=py+0.03, x1=px, y1=py-0.03,
                    line=dict(color="black", width=1.5),
                    layer="above"
                )
                # Arms
                fig.add_shape(
                    type="line",
                    x0=px-0.06, y0=py-0.06, x1=px, y1=py,
                    line=dict(color="black", width=1.5),
                    layer="above"
                )
                fig.add_shape(
                    type="line",
                    x0=px, y0=py, x1=px+0.06, y1=py-0.06,
                    line=dict(color="black", width=1.5),
                    layer="above"
                )
                # Legs
                fig.add_shape(
                    type="line",
                    x0=px, y0=py-0.03, x1=px-0.045, y1=py-0.12,
                    line=dict(color="black", width=1.5),
                    layer="above"
                )
                fig.add_shape(
                    type="line",
                    x0=px, y0=py-0.03, x1=px+0.045, y1=py-0.12,
                    line=dict(color="black", width=1.5),
                    layer="above"
                )

    # Draw event symbols and arrows
    for hh_id, event in events:
        event_type = event.get('type')
        unit_id = event.get('unit_id')
        
        if unit_id is not None:
            # Find unit position
            unit_idx = next((i for i, u in enumerate(frame['units']) if u.id == unit_id), None)
            if unit_idx is not None:
                x, y = positions[unit_idx]
                
                if event_type == 'MOVED_IN':
                    # Arrow is already handled by existing code
                    pass
                elif event_type == 'HOUSEHOLD_BREAKUP':
                    # Add exclamation mark
                    fig.add_annotation(
                        x=x + 0.3,
                        y=y + 0.3,
                        text="❗",  # Exclamation mark
                        showarrow=False,
                        font=dict(size=20, color="red"),
                        align="center"
                    )
                elif event_type == 'HOUSEHOLD_MERGER':
                    # Add check mark
                    fig.add_annotation(
                        x=x + 0.3,
                        y=y + 0.3,
                        text="✓",  # Check mark
                        showarrow=False,
                        font=dict(size=20, color="green"),
                        align="center"
                    )

    # Draw arrows for moved households
    arrow_color = "#e67e22"
    for hh_id, new_unit_id in current_hh_locations.items():
        old_unit_id = prev_hh_locations.get(hh_id)
        if old_unit_id is not None and old_unit_id != new_unit_id:
            old_idx = next(i for i, u in enumerate(frame['units']) if u.id == old_unit_id)
            new_idx = next(i for i, u in enumerate(frame['units']) if u.id == new_unit_id)
            old_x, old_y = positions[old_idx]
            new_x, new_y = positions[new_idx]
            fig.add_annotation(
                x=new_x,
                y=new_y,
                ax=old_x,
                ay=old_y,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=arrow_color
            )

    # Add unhoused area if enabled
    if show_unhoused:
        # Move unhoused area below the grid
        waiting_area_y = -(n_rows + 1) * (1 + HOUSE_MARGIN)  # Position below the last row
        fig.add_shape(
            type="rect",
            x0=-0.5,
            y0=waiting_area_y - 1,
            x1=n_cols * (1 + HOUSE_MARGIN),
            y1=waiting_area_y + 0.5,
            line=dict(color="black", width=1),
            fillcolor="rgba(255,240,240,0.5)",
            layer="below"
        )
        fig.add_annotation(
            x=2,  # Center of the unhoused area
            y=waiting_area_y + 0.7,
            text="Unhoused Households",
            showarrow=False,
            font=dict(size=12),
            align="center"
        )
        
        # Add unhoused households with their sizes
        unhoused_households = frame.get('unhoused_households', [])
        if isinstance(unhoused_households, list):
            x_offset = 0
            for i, hh in enumerate(unhoused_households):
                hh_size = getattr(hh, 'size', 1)  # Get household size or default to 1
                # Calculate starting position for centered group
                total_width = hh_size * PERSON_WIDTH
                start_x = x_offset + PERSON_SPACING
                
                for j in range(hh_size):
                    px = start_x + j * PERSON_WIDTH
                    py = waiting_area_y
                    
                    # Add stick figure for unhoused
                    # Head
                    fig.add_shape(
                        type="circle",
                        x0=px-0.04, y0=py+0.02, x1=px+0.04, y1=py+0.10,
                        line=dict(color="black", width=1),
                        fillcolor="rgba(228,26,28,1)",  # Red for unhoused
                        layer="above"
                    )
                    # Body
                    fig.add_shape(
                        type="line",
                        x0=px, y0=py+0.02, x1=px, y1=py-0.02,
                        line=dict(color="black", width=1.5),
                        layer="above"
                    )
                    # Arms
                    fig.add_shape(
                        type="line",
                        x0=px-0.04, y0=py-0.04, x1=px, y1=py,
                        line=dict(color="black", width=1.5),
                        layer="above"
                    )
                    fig.add_shape(
                        type="line",
                        x0=px, y0=py, x1=px+0.04, y1=py-0.04,
                        line=dict(color="black", width=1.5),
                        layer="above"
                    )
                    # Legs
                    fig.add_shape(
                        type="line",
                        x0=px, y0=py-0.02, x1=px-0.03, y1=py-0.08,
                        line=dict(color="black", width=1.5),
                        layer="above"
                    )
                    fig.add_shape(
                        type="line",
                        x0=px, y0=py-0.02, x1=px+0.03, y1=py-0.08,
                        line=dict(color="black", width=1.5),
                        layer="above"
                    )
                
                # Add household size label
                fig.add_annotation(
                    x=start_x + total_width/2,
                    y=waiting_area_y - 0.2,
                    text=f"Size: {hh_size}",
                    showarrow=False,
                    font=dict(size=10)
                )
                
                x_offset += total_width + 0.3  # Space between household groups

    # Set the figure layout
    width = (n_cols + 1) * 100  # Width based on columns
    height = (n_rows + 3) * 100  # Height includes space for unhoused area
    
    fig.update_layout(
        showlegend=False,
        width=width,
        height=height,
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-1, n_cols * (1 + HOUSE_MARGIN)]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1,
            range=[waiting_area_y - 1.5, 1]  # Extend range to include unhoused area
        )
    )
    
    return fig 