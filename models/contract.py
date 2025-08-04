"""
Contract class for managing rental agreements between tenants and units.
"""

class Contract:
    def __init__(self, tenant, unit):
        self.tenant = tenant
        self.unit = unit
        self.months = 0
        self.start_rent = unit.rent
        self.history = []  # Track rent changes

    def update(self):
        """Update contract state for one month."""
        self.months += 1
        # Record rent history
        self.history.append({
            'month': self.months,
            'rent': self.unit.rent,
            'tenant_satisfaction': self.tenant.satisfaction if hasattr(self.tenant, 'satisfaction') else None
        })

    def get_duration(self):
        """Get contract duration in months."""
        return self.months

    def get_rent_change(self):
        """Calculate total rent change since contract start."""
        if self.start_rent > 0:
            return (self.unit.rent - self.start_rent) / self.start_rent
        return 0

    def is_long_term(self):
        """Check if this is a long-term contract (>12 months)."""
        return self.months >= 12 