import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle, Polygon, Circle, PathPatch
from matplotlib.path import Path
import random
from matplotlib import cm
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pickle

class HousingVisualization:
    def __init__(self, simulation, ax=None):
        # global style
        plt.rcParams.update({
            'font.family': 'DejaVu Sans',
            'font.size': 12,
            'axes.titlesize': 24,
            'axes.titleweight': 'bold',
            'axes.labelsize': 14,
            'figure.facecolor': '#f0f0f0'
        })
        self.sim = simulation
        if ax is None:
            self.fig, self.ax = plt.subplots(figsize=(18, 12))
        else:
            self.ax = ax
            self.fig = ax.figure
        self.paused = False
        self.anim = None
        self.house_patches = []
        self.current_frame = 0

        # one tooltip Text, hidden until needed
        self.tooltip = self.ax.text(0, 0, "", visible=False,
                                    ha='center', va='bottom',
                                    fontsize=9,
                                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.95),
                                    zorder=200)

        self._setup_plot()
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)

    def _setup_plot(self):
        n = len(self.sim.rental_market.units)
        grid_size = int(np.ceil(np.sqrt(n)))
        self.grid_size = grid_size
        self.spacing = 1.0

        # Title
        self.ax.set_title("Housing Market Simulation", pad=20)
        self.ax.axis('off')
        self.ax.set_xlim(-0.5, grid_size*self.spacing + 8)  # Increased right limit
        self.ax.set_ylim(-0.5, grid_size*self.spacing)

        # Sidebar background
        sidebar_x = grid_size*self.spacing + 2.5  # Moved further right
        self.ax.add_patch(Rectangle(
            (sidebar_x, -0.5),
            5, grid_size*self.spacing + 0.5,
            facecolor='#ffffff', edgecolor='#cccccc', lw=1.5, zorder=0
        ))

        # Positions
        self.house_positions = []
        for i in range(n):
            row, col = divmod(i, grid_size)
            x = col*self.spacing + 0.5
            y = grid_size*self.spacing - row*self.spacing - 0.5
            self.house_positions.append((x, y))

        # colormap
        rents = [u.rent for u in self.sim.rental_market.units]
        self.norm = plt.Normalize(min(rents), max(rents))
        self.cmap = cm.get_cmap('viridis')

    def _draw_house(self, x, y, rent, occupied, idx):
        unit = self.sim.rental_market.units[idx]
        # Distinguish owner-occupied houses
        if getattr(unit, 'is_owner_occupied', False):
            color = '#b3c6ff'  # light blue for owner-occupied
            roof_color = '#3777c2'  # blue roof
        else:
            color = self.cmap(self.norm(rent)) if occupied else '#dddddd'
            roof_color = '#d95f02'
        body = Rectangle(
            (x-0.45/2, y-0.36/2), 0.45, 0.36,
            facecolor=color, edgecolor='#333', linewidth=1.5, zorder=5, picker=True
        )
        roof = Polygon(
            [(x-0.54/2, y+0.36/2),
             (x, y+0.36/2+0.18),
             (x+0.54/2, y+0.36/2)],
            facecolor=roof_color, edgecolor='#333', linewidth=1.5, zorder=6
        )
        self.ax.add_patch(body)
        self.ax.add_patch(roof)
        self.house_patches.append((body, idx, x, y))
        return body, roof

    def _update(self, frame):
        if self.paused:
            return

        # Clear the plot
        self.ax.clear()
        self._setup_plot()  # Restore plot settings

        # Get current metrics
        m = self.sim.metrics[frame]

        # Draw grid
        for i in range(self.grid_size + 1):
            self.ax.axhline(y=i * self.spacing, color='gray', alpha=0.2)
            self.ax.axvline(x=i * self.spacing, color='gray', alpha=0.2)

        # Draw houses and households
        self.house_patches = []  # Reset house patches for hover
        for i, unit in enumerate(self.sim.rental_market.units):
            row, col = divmod(i, self.grid_size)
            x = col * self.spacing
            y = (self.grid_size - row - 1) * self.spacing

            # Draw house (square)
            color = (
                'royalblue' if getattr(unit, 'is_owner_occupied', False)
                else 'limegreen' if unit.occupied
                else 'lightgray'
            )
            house = plt.Rectangle(
                (x - 0.2, y - 0.2),
                0.4, 0.4,
                facecolor=color,
                edgecolor='black'
            )
            self.ax.add_patch(house)
            self.house_patches.append((house, i, x, y))

            # Draw roof (triangle)
            self.ax.add_patch(plt.Polygon(
                [[x - 0.22, y + 0.2], [x, y + 0.4], [x + 0.22, y + 0.2]],
                facecolor='#d95f02',
                edgecolor='black'
            ))

            # Add house number
            self.ax.text(x, y - 0.34, f"Unit {unit.id}", ha='center', va='center', fontsize=8)

            # Draw household if occupied
            if unit.occupied:
                size = unit.tenant.size if not getattr(unit, 'is_owner_occupied', False) else 1
                for j in range(size):
                    offset_x = (j - (size - 1) / 2) * 0.15
                    px = x + offset_x
                    py = y - 0.05
                    # Draw stick figure
                    head = Circle((px, py + 0.06), 0.04,
                                facecolor='#1b9e77' if not getattr(unit, 'is_owner_occupied', False) else '#3777c2',
                                edgecolor='#222', lw=1, zorder=20)
                    body_line = PathPatch(
                        Path([(px, py + 0.02), (px, py - 0.02)], [Path.MOVETO, Path.LINETO]),
                        edgecolor='#222', lw=1.5, zorder=20
                    )
                    arm1 = PathPatch(
                        Path([(px, py), (px - 0.04, py - 0.04)], [Path.MOVETO, Path.LINETO]),
                        edgecolor='#222', lw=1.5, zorder=20
                    )
                    arm2 = PathPatch(
                        Path([(px, py), (px + 0.04, py - 0.04)], [Path.MOVETO, Path.LINETO]),
                        edgecolor='#222', lw=1.5, zorder=20
                    )
                    leg1 = PathPatch(
                        Path([(px, py - 0.02), (px - 0.03, py - 0.08)], [Path.MOVETO, Path.LINETO]),
                        edgecolor='#222', lw=1.5, zorder=20
                    )
                    leg2 = PathPatch(
                        Path([(px, py - 0.02), (px + 0.03, py - 0.08)], [Path.MOVETO, Path.LINETO]),
                        edgecolor='#222', lw=1.5, zorder=20
                    )
                    for part in (head, body_line, arm1, arm2, leg1, leg2):
                        self.ax.add_patch(part)

        # Draw unhoused area on the right
        waiting_area_x = self.grid_size * self.spacing + 0.5
        self.ax.add_patch(plt.Rectangle(
            (waiting_area_x, -0.5),
            2, self.grid_size * self.spacing + 1,
            facecolor=(1.0, 0.94, 0.94, 0.5),  # Light red with transparency
            edgecolor='black',
            alpha=0.3
        ))
        self.ax.text(
            waiting_area_x + 1,
            self.grid_size * self.spacing,
            "Unhoused\nHouseholds",
            ha='center',
            va='top',
            fontsize=12
        )

        # Draw unhoused households as stick figures
        unhoused = [h for h in self.sim.households if not h.housed]
        for i, household in enumerate(unhoused):
            row = i // 2  # 2 households per row
            col = i % 2
            px = waiting_area_x + col * 0.5
            py = self.grid_size * self.spacing - 1 - row * 0.5
            # Draw stick figure
            head = Circle((px, py + 0.06), 0.04,
                        facecolor='#e41a1c',
                        edgecolor='#222', lw=1, zorder=20)
            body_line = PathPatch(
                Path([(px, py + 0.02), (px, py - 0.02)], [Path.MOVETO, Path.LINETO]),
                edgecolor='#222', lw=1.5, zorder=20
            )
            arm1 = PathPatch(
                Path([(px, py), (px - 0.04, py - 0.04)], [Path.MOVETO, Path.LINETO]),
                edgecolor='#222', lw=1.5, zorder=20
            )
            arm2 = PathPatch(
                Path([(px, py), (px + 0.04, py - 0.04)], [Path.MOVETO, Path.LINETO]),
                edgecolor='#222', lw=1.5, zorder=20
            )
            leg1 = PathPatch(
                Path([(px, py - 0.02), (px - 0.03, py - 0.08)], [Path.MOVETO, Path.LINETO]),
                edgecolor='#222', lw=1.5, zorder=20
            )
            leg2 = PathPatch(
                Path([(px, py - 0.02), (px + 0.03, py - 0.08)], [Path.MOVETO, Path.LINETO]),
                edgecolor='#222', lw=1.5, zorder=20
            )
            for part in (head, body_line, arm1, arm2, leg1, leg2):
                self.ax.add_patch(part)

        # sidebar
        stats_x = self.grid_size * self.spacing + 2.5  # Moved further right
        stats_y = self.grid_size * self.spacing - 0.5

        # Owner-occupier metrics
        owner_units = [u for u in self.sim.rental_market.units if getattr(u, 'is_owner_occupied', False)]
        owner_share = len(owner_units) / len(self.sim.rental_market.units)
        avg_mortgage = np.mean([
            getattr(u.owner, 'mortgage_balance', 0) for u in owner_units if u.owner is not None
        ]) if owner_units else 0

        # Get movement logs for current frame
        movement_logs = []
        for household in self.sim.households:
            if household.timeline:
                # Get events from this month
                current_month_events = [
                    event for event in household.timeline 
                    if event.year == self.sim.metrics[frame]['year'] 
                    and event.month == self.sim.metrics[frame]['month']
                    and event.record.get('type') == 'MOVED_IN'
                ]
                for event in current_month_events:
                    # Determine the most important reason
                    move_reason = event.record.get('move_reason', 'Unknown')
                    from_unit = event.record.get('from_unit_id')
                    is_house_to_house = event.record.get('is_house_to_house', False)
                    
                    # Create move info with source unit if it's a house-to-house move
                    if is_house_to_house:
                        move_info = (
                            f"HH {household.id} moved from Unit {from_unit} to Unit {event.record['unit_id']}\n"
                            f"Reason: {move_reason}\n"
                            f"New Rent: ${event.record['rent']:.0f}"
                        )
                    else:
                        source = "Unhoused" if from_unit is None else f"Unit {from_unit}"
                        move_info = (
                            f"HH {household.id} moved from {source} to Unit {event.record['unit_id']}\n"
                            f"Reason: {move_reason}\n"
                            f"New Rent: ${event.record['rent']:.0f}"
                        )
                    movement_logs.append(move_info)

        # Combine stats and movement logs
        sidebar = (
            f"Month: {m['year']}-{m['month']:02d}\n\n"
            f"Avg Satisfaction: {m['satisfaction']:.2f}\n"
            f"Avg Rent: ${m['avg_rent']:.0f}\n"
            f"Avg Rent Burden: {m['avg_burden']:.2f}\n"
            f"Avg Income: ${m['avg_income']:.0f}\n"
            f"Avg Wealth: ${m['avg_wealth']:.0f}\n"
            f"Avg Quality: {m['avg_quality']:.2f}\n"
            f"Avg Unit Size: {np.mean([getattr(u,'size',1) for u in self.sim.rental_market.units]):.2f}\n"
            f"Avg Location: {np.mean([getattr(u,'location',0.5) for u in self.sim.rental_market.units]):.2f}\n"
            f"Vacancy Rate: {m['vacancy_rate']:.1%}\n"
            f"Mobility Rate: {m['mobility_rate']:.1%}\n"
            f"Total Profit: ${m['profit']:.0f}\n"
            f"Housed: {m['housed']} / {len(self.sim.households)}\n"
            f"Unhoused: {len(self.sim.households) - m['housed']}\n"
            f"Vacant Units: {len([u for u in self.sim.rental_market.units if not u.occupied])}\n"
            f"Violations: {m['violations']}\n"
            f"Property Tax Paid: ${m.get('property_tax', 0):.0f}\n"
            f"Wealth Tax Paid: ${m.get('wealth_tax', 0):.0f}\n"
            f"Owner-Occupier Share: {owner_share:.1%}\n"
            f"Avg Mortgage Balance: ${avg_mortgage:.0f}\n\n"
            f"Movement Log:\n" + "\n".join(movement_logs) if movement_logs else ""
        )
        self.ax.text(
            stats_x, stats_y, sidebar,
            ha='left', va='top',
            fontsize=10, color='#222',
            family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', fc='#fafafa', ec='#888', lw=1),
            zorder=100
        )

        # Set up hover tooltip
        self.tooltip = self.ax.text(0, 0, "", visible=False,
                                  ha='center', va='bottom',
                                  fontsize=9,
                                  bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.95),
                                  zorder=200)

        # Update current frame
        self.current_frame = frame

        # Update axis limits to accommodate the moved sidebar
        self.ax.set_xlim(-0.5, self.grid_size * self.spacing + 8)  # Increased right limit

        # Draw
        self.fig.canvas.draw()

    def on_hover(self, event):
        if not event.inaxes:
            self.tooltip.set_visible(False)
            self.fig.canvas.draw_idle()
            return
        for patch, unit_idx, x, y in self.house_patches:
            contains, _ = patch.contains(event)
            if contains:
                frame = self.current_frame
                unit = self.sim.rental_market.units[unit_idx]
                occ = self.sim.occupancy_history[frame][unit_idx]
                unit_id, hh_id, hh_size = occ
                # Property tax for this unit
                property_value = unit.base_rent * 12 * 20
                property_tax = (0.02 / 12) * property_value
                if getattr(unit, 'is_owner_occupied', False):
                    owner = getattr(unit, 'owner', None)
                    info = f"OWNER-OCCUPIED\n"
                    info += f"Quality: {unit.quality:.2f}\nLocation: {getattr(unit, 'location', 'N/A'):.2f}\nProperty value: ${property_value:.0f}\nProperty tax: ${property_tax:.0f}/mo"
                    if owner:
                        info += f"\n--- Owner ---"
                        info += f"\nIncome: ${owner.income:.0f}"
                        info += f"\nWealth: ${owner.wealth:.0f}"
                        info += f"\nMortgage: ${getattr(owner, 'mortgage_balance', 0):.0f}"
                        info += f"\nMonthly Payment: ${getattr(owner, 'monthly_payment', 0):.0f}"
                        info += f"\nInterest Deduction: ${getattr(owner, 'mortgage_interest_paid', 0):.0f}/yr"
                        info += f"\nLife stage: {getattr(owner, 'life_stage', 'N/A')}"
                        info += f"\nSatisfaction: {getattr(owner, 'satisfaction', 0):.2f}"
                        info += f"\nHousehold size: {owner.size}"
                else:
                    info = f"Rent: ${unit.rent:.0f}\nQuality: {unit.quality:.2f}\nLocation: {getattr(unit, 'location', 'N/A'):.2f}\nProperty value: ${property_value:.0f}\nProperty tax: ${property_tax:.0f}/mo"
                    amenities = getattr(unit, 'amenities', None)
                    if amenities:
                        amen_list = [k for k, v in amenities.items() if v]
                        if amen_list:
                            info += f"\nAmenities: {', '.join(amen_list)}"
                    if hh_id is not None:
                        tenant = next((h for h in self.sim.households if h.id == hh_id), None)
                        if tenant:
                            # Wealth tax for this tenant
                            taxable_wealth = max(0, tenant.wealth - 50000)
                            wealth_tax = (0.012 / 12) * taxable_wealth
                            info += (f"\n--- Tenant ---"
                                     f"\nIncome: ${tenant.income:.0f}"
                                     f"\nWealth: ${tenant.wealth:.0f}"
                                     f"\nLife stage: {getattr(tenant, 'life_stage', 'N/A')}"
                                     f"\nSatisfaction: {tenant.satisfaction:.2f}"
                                     f"\nHousehold size: {tenant.size}"
                                     f"\nWealth tax: ${wealth_tax:.0f}/mo")
                    else:
                        info += "\n(Vacant)"
                self.tooltip.set_text(info)
                self.tooltip.set_position((x, y + 0.7))
                self.tooltip.set_visible(True)
                self.fig.canvas.draw_idle()
                return
        self.tooltip.set_visible(False)
        self.fig.canvas.draw_idle()

    def _on_key_press(self, event):
        if event.key == ' ':
            self.paused = not self.paused
            if self.anim:
                (self.anim.event_source.stop() if self.paused
                 else self.anim.event_source.start())

    def animate(self):
        self.anim = animation.FuncAnimation(
            self.fig, self._update,
            frames=len(self.sim.metrics),
            interval=1000,
            repeat=False
        )
        plt.show()
        return self.anim

    def animate_on_existing_axis(self, interval=1000):
        """
        Create the animation for this visualization on its axis, but do NOT call plt.show().
        Returns the FuncAnimation object.
        Usage for side-by-side comparison:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(36, 15))
            vis1 = HousingVisualization(sim1, ax=ax1)
            vis2 = HousingVisualization(sim2, ax=ax2)
            ani1 = vis1.animate_on_existing_axis()
            ani2 = vis2.animate_on_existing_axis()
            plt.show()
        """
        self.anim = animation.FuncAnimation(
            self.fig, self._update,
            frames=len(self.sim.metrics),
            interval=interval,
            repeat=False
        )
        return self.anim

    @classmethod
    def with_new_figure(cls, simulation, figsize=(18, 12)):
        fig, ax = plt.subplots(figsize=figsize)
        return cls(simulation, ax=ax)

def show_housing_visualization(*simulations):
    visualizations = []
    for sim in simulations:
        # Create a new figure for each simulation
        fig, ax = plt.subplots(figsize=(18, 12))
        vis = HousingVisualization(sim, ax=ax)
        vis.animate()  # This will show each figure
        visualizations.append(vis)
    return visualizations

def get_positions(n):
    grid_size = int(np.ceil(np.sqrt(n)))
    grid = []
    for i in range(n):
        row, col = divmod(i, grid_size)
        x = col
        y = grid_size - row - 1
        grid.append((x, y))
    return grid

def export_frames(sim, filename):
    frames = []
    movement_logs = []

    for frame_idx, metrics in enumerate(sim.metrics):
        frame = []
        logs = []

        # Build lookup from occupancy history for this frame
        occupancy = {uid: (hh_id, hh_size) for uid, hh_id, hh_size in sim.occupancy_history[frame_idx]}

        # Build lookup for households and their stats
        hh_map = {hh.id: hh for hh in sim.households}

        # Log movements this month
        for hh in sim.households:
            for event in hh.timeline:
                if (event.year == metrics["year"] and event.month == metrics["month"]
                    and event.record.get("type") == "MOVED_IN"):
                    from_unit = event.record.get('from_unit_id')
                    is_house_to_house = event.record.get('is_house_to_house', False)
                    
                    if is_house_to_house:
                        logs.append(
                            f"HH {hh.id} moved from Unit {from_unit} to Unit {event.record['unit_id']}, "
                            f"Reason: {event.record['move_reason']}, "
                            f"New Rent: ${event.record['rent']:.0f}"
                        )
                    else:
                        source = "Unhoused" if from_unit is None else f"Unit {from_unit}"
                        logs.append(
                            f"HH {hh.id} moved from {source} to Unit {event.record['unit_id']}, "
                            f"Reason: {event.record['move_reason']}, "
                            f"New Rent: ${event.record['rent']:.0f}"
                        )

        for unit in sim.rental_market.units:
            unit_id = unit.id
            is_owner_occupied = getattr(unit, 'is_owner_occupied', False)
            occupied = unit_id in occupancy and occupancy[unit_id][0] is not None

            # Get tenant if occupied
            tenant_id, hh_size = occupancy.get(unit_id, (None, 0))
            tenant = hh_map.get(tenant_id, None) if tenant_id is not None else None

            # Get owner (if any)
            owner = getattr(unit, 'owner', None)

            frame.append({
                'unit_id': unit_id,
                'rent': unit.rent,
                'quality': unit.quality,
                'occupied': occupied,
                'is_owner_occupied': is_owner_occupied,
                'property_value': unit.base_rent * 12 * 20,
                'tenant_size': tenant.size if tenant else 0,
                'tenant_income': tenant.income if tenant else 0,
                'tenant_wealth': tenant.wealth if tenant else 0,
                'tenant_satisfaction': tenant.satisfaction if tenant else None,
                'tenant_life_stage': tenant.life_stage if tenant else None,
                'tenant_rent_burden': tenant.current_rent_burden() if tenant else 0,
                'owner_income': owner.income if owner else 0,
                'owner_wealth': owner.wealth if owner else 0,
                'owner_mortgage': getattr(owner, 'mortgage_balance', 0) if owner else 0,
                'owner_monthly_payment': getattr(owner, 'monthly_payment', 0) if owner else 0,
                'owner_satisfaction': getattr(owner, 'satisfaction', 0) if owner else 0,
            })

        frames.append(frame)
        movement_logs.append(logs)

    # Save frames
    with open(filename, 'wb') as f:
        pickle.dump(frames, f)

    # Save movement logs
    movement_logs_filename = filename.replace('.pkl', '_movement_logs.pkl')
    with open(movement_logs_filename, 'wb') as f:
        pickle.dump(movement_logs, f)

