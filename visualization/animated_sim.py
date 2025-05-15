import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle, Polygon, Circle, PathPatch
from matplotlib.path import Path
import random
from matplotlib import cm

class HousingVisualization:
    def __init__(self, simulation):
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
        self.fig, self.ax = plt.subplots(figsize=(18, 12))
        self.ax.set_facecolor('#eaeaf2')
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
        self.ax.set_xlim(-0.5, grid_size*self.spacing + 6)
        self.ax.set_ylim(-0.5, grid_size*self.spacing)

        # Sidebar background
        sidebar_x = grid_size*self.spacing + 0.5
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
        color = self.cmap(self.norm(rent)) if occupied else '#dddddd'
        body = Rectangle(
            (x-0.45/2, y-0.36/2), 0.45, 0.36,
            facecolor=color, edgecolor='#333', linewidth=1.5, zorder=5, picker=True
        )
        roof = Polygon(
            [(x-0.54/2, y+0.36/2),
             (x, y+0.36/2+0.18),
             (x+0.54/2, y+0.36/2)],
            facecolor='#d95f02', edgecolor='#333', linewidth=1.5, zorder=6
        )
        self.ax.add_patch(body)
        self.ax.add_patch(roof)
        self.house_patches.append((body, idx, x, y))
        return body, roof

    def _update(self, frame):
        if self.paused:
            return
        self.ax.cla()
        self._setup_plot()
        self.house_patches = []  # Reset for this frame
        # Re-create tooltip for this frame
        self.tooltip = self.ax.text(0, 0, "", visible=False,
                                    ha='center', va='bottom',
                                    fontsize=9,
                                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.95),
                                    zorder=200)

        m = self.sim.metrics[frame]
        occ = self.sim.occupancy_history[frame]
        n_units = len(self.sim.rental_market.units)

        for i in range(n_units):
            unit = self.sim.rental_market.units[i]
            x, y = self.house_positions[i]

            # draw house
            self._draw_house(x, y, unit.rent, unit.occupied, i)

            # draw tiny stick figures
            if unit.occupied:
                _, hh_id, hh_size = occ[i]
                for j in range(hh_size):
                    px = x + (j - (hh_size - 1) / 2) * 0.15
                    py = y - 0.05
                    head = Circle((px, py + 0.06), 0.04,
                                  facecolor='#1b9e77', edgecolor='#222', lw=1, zorder=20)
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

            # rent label
            self.ax.text(x, y - 0.34, f"${unit.rent:.0f}",
                         ha='center', va='center', fontsize=8, zorder=30)

        # sidebar
        stats_x = self.grid_size * self.spacing + 0.6
        stats_y = self.grid_size * self.spacing - 0.5
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
            f"Renovations: {m['renovation_count']}\n"
            f"Housed: {m['housed']} / {len(self.sim.households)}\n"
            f"Violations: {m['violations']}"
        )
        self.ax.text(
            stats_x, stats_y, sidebar,
            ha='left', va='top',
            fontsize=10, color='#222',
            family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', fc='#fafafa', ec='#888', lw=1),
            zorder=100
        )

        self.current_frame = frame

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
                info = f"Rent: ${unit.rent:.0f}\nQuality: {unit.quality:.2f}\nLocation: {getattr(unit, 'location', 'N/A'):.2f}"
                amenities = getattr(unit, 'amenities', None)
                if amenities:
                    amen_list = [k for k, v in amenities.items() if v]
                    if amen_list:
                        info += f"\nAmenities: {', '.join(amen_list)}"
                if hh_id is not None:
                    tenant = next((h for h in self.sim.households if h.id == hh_id), None)
                    if tenant:
                        info += (f"\n--- Tenant ---"
                                 f"\nIncome: ${tenant.income:.0f}"
                                 f"\nWealth: ${tenant.wealth:.0f}"
                                 f"\nLife stage: {getattr(tenant, 'life_stage', 'N/A')}"
                                 f"\nSatisfaction: {tenant.satisfaction:.2f}"
                                 f"\nHousehold size: {tenant.size}")
                else:
                    info += "\n(Vacant)"
                self.tooltip.set_text(info)
                self.tooltip.set_position((x, y+0.5))
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