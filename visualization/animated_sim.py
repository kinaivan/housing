import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle, Polygon, Circle, Path, PathPatch
import random
from collections import Counter

class HousingVisualization:
    def __init__(self, simulation):
        self.sim = simulation
        self.fig, self.ax = plt.subplots(figsize=(20, 15))
        self.paused = False
        self.anim = None
        self.house_patches = []  # For hover detection
        self.tooltip = None
        self.current_frame = 0
        self.sidebar_text = None
        self.setup_plot()
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)

    def setup_plot(self):
        n = len(self.sim.rental_market.units)
        grid_size = int(np.ceil(np.sqrt(n)))
        self.grid_size = grid_size
        margin = 2
        max_grid = max(grid_size, 6)
        self.spacing = min(1.1, (12-margin)/max_grid)
        self.ax.set_xlim(-1, grid_size * self.spacing + 7)  # More space for sidebar
        self.ax.set_ylim(-1, grid_size * self.spacing)
        self.ax.set_title("Housing Market Simulation")
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        self.ax.add_patch(Rectangle((-1, -1), grid_size * self.spacing + 8, grid_size * self.spacing + 2, facecolor='#b6e3a1', zorder=0))
        self._draw_neighbourhood_background(grid_size)

        self.house_positions = []
        for i in range(n):
            row = i // grid_size
            col = i % grid_size
            x = col * self.spacing + 0.5
            y = grid_size * self.spacing - row * self.spacing - 0.5
            self.house_positions.append((x, y))

        self.houses = []
        self.tenants = []
        self.rent_labels = []
        self.satisfaction_labels = []
        self.house_patches = []

    def _draw_neighbourhood_background(self, grid_size):
        n_trees = grid_size * 2
        for _ in range(n_trees):
            tx = random.uniform(0, grid_size * self.spacing + 2)
            ty = random.uniform(0, grid_size * self.spacing)
            if 0.5 < tx < grid_size * self.spacing - 0.5 and 0.5 < ty < grid_size * self.spacing - 0.5:
                if random.random() < 0.7:
                    self.ax.add_patch(Rectangle((tx-0.03, ty-0.12), 0.06, 0.12, facecolor='#8b5a2b', edgecolor='none', zorder=1))
                    self.ax.add_patch(Circle((tx, ty), 0.13, facecolor='#228B22', edgecolor='none', zorder=2))
        n_parking = grid_size
        for _ in range(n_parking):
            px = random.uniform(0, grid_size * self.spacing + 2)
            py = random.uniform(0, grid_size * self.spacing)
            if 0.5 < px < grid_size * self.spacing - 0.5 and 0.5 < py < grid_size * self.spacing - 0.5:
                self.ax.add_patch(Rectangle((px-0.18, py-0.05), 0.36, 0.1, facecolor='#bbbbbb', edgecolor='#888888', linewidth=1, zorder=1))

    def draw_house(self, x, y, occupied, unit_idx):
        body_w, body_h = 0.45, 0.36
        roof_w, roof_h = 0.54, 0.18
        house_body = Rectangle((x-body_w/2, y-body_h/2), body_w, body_h, facecolor='white', edgecolor='black', linewidth=2, zorder=10, picker=True)
        roof = Polygon([(x-roof_w/2, y+body_h/2), (x, y+body_h/2+roof_h), (x+roof_w/2, y+body_h/2)], facecolor='red', edgecolor='black', linewidth=2, zorder=11)
        self.ax.add_patch(house_body)
        self.ax.add_patch(roof)
        self.house_patches.append((house_body, unit_idx, x, y))
        return [house_body, roof]

    def draw_stick_figure(self, x, y, color='black'):
        head = Circle((x, y+0.05), 0.025, facecolor=color, edgecolor='black', linewidth=1, zorder=20)
        body = PathPatch(Path([(x, y+0.03), (x, y-0.03)], [Path.MOVETO, Path.LINETO]), edgecolor='black', linewidth=1, zorder=20)
        arm1 = PathPatch(Path([(x, y+0.01), (x-0.025, y-0.01)], [Path.MOVETO, Path.LINETO]), edgecolor='black', linewidth=1, zorder=20)
        arm2 = PathPatch(Path([(x, y+0.01), (x+0.025, y-0.01)], [Path.MOVETO, Path.LINETO]), edgecolor='black', linewidth=1, zorder=20)
        leg1 = PathPatch(Path([(x, y-0.03), (x-0.02, y-0.07)], [Path.MOVETO, Path.LINETO]), edgecolor='black', linewidth=1, zorder=20)
        leg2 = PathPatch(Path([(x, y-0.03), (x+0.02, y-0.07)], [Path.MOVETO, Path.LINETO]), edgecolor='black', linewidth=1, zorder=20)
        for part in [head, body, arm1, arm2, leg1, leg2]:
            self.ax.add_patch(part)
        return [head, body, arm1, arm2, leg1, leg2]

    def update(self, frame):
        if self.paused:
            return
        self.current_frame = frame
        for house in self.houses:
            for part in house:
                part.remove()
        for tenant in self.tenants:
            for part in tenant:
                part.remove()
        for label in self.rent_labels + self.satisfaction_labels:
            label.remove()
        self.houses = []
        self.tenants = []
        self.rent_labels = []
        self.satisfaction_labels = []
        self.house_patches = []
        if self.sidebar_text:
            self.sidebar_text.remove()
            self.sidebar_text = None

        current_metrics = self.sim.metrics[frame]
        occupancy = self.sim.occupancy_history[frame]
        unit_id_to_people = {unit_id: (hh_id, hh_size) for unit_id, hh_id, hh_size in occupancy}

        # --- Compute extra metrics for sidebar ---
        households = self.sim.households
        units = self.sim.rental_market.units
        housed = [h for h in households if h.housed]
        vacant_units = [u for u in units if not u.occupied]
        avg_burden = current_metrics.get('avg_burden', 0)
        avg_income = current_metrics.get('avg_income', 0)
        avg_wealth = current_metrics.get('avg_wealth', 0)
        avg_quality = current_metrics.get('avg_quality', 0)
        avg_unit_size = np.mean([getattr(u, 'size', 1) for u in units])
        avg_unit_location = np.mean([getattr(u, 'location', 0.5) for u in units])
        renovation_count = current_metrics.get('renovation_count', 0)
        profit = current_metrics.get('profit', 0)
        n_housed = current_metrics.get('housed', 0)
        n_unhoused = len(households) - n_housed
        n_vacant = len(vacant_units)

        for i, unit in enumerate(self.sim.rental_market.units):
            x, y = self.house_positions[i]
            house = self.draw_house(x, y, unit.occupied, i)
            self.houses.append(house)
            hh_id, n_people = unit_id_to_people.get(unit.id, (None, 0))
            if hh_id is not None and n_people > 0:
                for j in range(n_people):
                    px = x - 0.06 + 0.12 * (j / max(1, n_people-1)) if n_people > 1 else x
                    py = y - 0.03
                    color = 'black'
                    self.tenants.append(self.draw_stick_figure(px, py, color=color))
            rent_label = self.ax.text(x, y-0.32, f"${unit.rent:.0f}", ha='center', va='center', fontsize=9, zorder=30)
            self.rent_labels.append(rent_label)

        # --- Sidebar legend ---
        stats_x = self.grid_size * self.spacing + 0.7
        stats_y = self.grid_size * self.spacing - 0.5
        sidebar = (
            f"Month: {current_metrics['year']}-{current_metrics['month']:02d}"
            f"\nAvg Satisfaction: {current_metrics['satisfaction']:.2f}"
            f"\nAvg Rent: ${current_metrics['avg_rent']:.0f}"
            f"\nAvg Rent Burden: {avg_burden:.2f}"
            f"\nAvg Income: ${avg_income:.0f}"
            f"\nAvg Wealth: ${avg_wealth:.0f}"
            f"\nAvg Quality: {avg_quality:.2f}"
            f"\nAvg Unit Size: {avg_unit_size:.2f}"
            f"\nAvg Location: {avg_unit_location:.2f}"
            f"\nVacancy Rate: {current_metrics['vacancy_rate']:.1%}"
            f"\nMobility Rate: {current_metrics['mobility_rate']:.1%}"
            f"\nTotal Profit: ${profit:.0f}"
            f"\nHoused: {n_housed}"
            f"\nUnhoused: {n_unhoused}"
            f"\nVacant Units: {n_vacant}"
            f"\nViolations: {current_metrics['violations']}"
        )
        self.sidebar_text = self.ax.text(stats_x, stats_y, sidebar, ha='left', va='top', fontsize=11, zorder=100)
        if self.tooltip:
            self.tooltip.remove()
            self.tooltip = None

    def on_key_press(self, event):
        if event.key == ' ':  # Spacebar toggles pause
            self.paused = not self.paused
            if not self.paused and self.anim is not None:
                self.anim.event_source.start()
            elif self.paused and self.anim is not None:
                self.anim.event_source.stop()

    def on_hover(self, event):
        if not event.inaxes:
            if self.tooltip:
                self.tooltip.remove()
                self.tooltip = None
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
                if self.tooltip:
                    self.tooltip.remove()
                self.tooltip = self.ax.text(x, y+0.5, info, ha='center', va='bottom', fontsize=9,
                                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.95), zorder=200)
                self.fig.canvas.draw_idle()
                return
        if self.tooltip:
            self.tooltip.remove()
            self.tooltip = None
            self.fig.canvas.draw_idle()

    def animate(self):
        self.anim = animation.FuncAnimation(
            self.fig, self.update,
            frames=len(self.sim.metrics),
            interval=1500,  # 1.5 seconds per frame (slower)
            repeat=False
        )
        plt.show()
        return self.anim

# Usage example:
if __name__ == "__main__":
    from models.household import Household
    from models.unit import RentalUnit, Landlord
    from models.market import RentalMarket
    from models.policy import RentCapPolicy
    from simulation.runner import Simulation
    import random
    
    # Create a small test simulation
    households = [Household(id=i, age=30, size=2, income=2000, wealth=5000) 
                 for i in range(50)]
    units = [RentalUnit(id=i, quality=0.8, base_rent=1000) 
             for i in range(50)]
    landlords = [Landlord(id=0, units=units, is_compliant=True)]
    market = RentalMarket(units)
    policy = RentCapPolicy(rent_cap_ratio=0.3, max_increase_rate=0.05, inspection_rate=0.1)
    
    sim = Simulation(households, landlords, market, policy, years=1)
    sim.run()
    
    # Create and run visualization
    vis = HousingVisualization(sim)
    vis.animate() 