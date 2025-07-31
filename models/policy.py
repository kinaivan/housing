# models/policy.py
class RentCapPolicy:
    def __init__(self):
        self.inspection_rate = 0.05  # 5% chance of inspection per period
        self.max_increase_rate = 0.10  # 10% max rent increase
        self.violations_found = 0
        self.improvements_required = 0
        self.rent_increases_prevented = 0
        self.total_savings = 0  # Track total tenant savings from prevented increases

    def inspect(self, unit):
        """Inspect unit for violations"""
        if unit.quality < 0.4:
            unit.violations += 1
            self.violations_found += 1
            if unit.violations >= 3:
                self.improvements_required += 1
                # Force renovation
                unit.last_renovation = 0
                unit.quality = max(0.4, unit.quality)  # Bring up to minimum standard
                unit.violations = 0  # Reset violations after improvement

    def check_rent_increase(self, old_rent, new_rent):
        """Check if rent increase is within allowed limits"""
        if old_rent == 0:
            return new_rent  # Allow initial rent setting
            
        increase_rate = (new_rent - old_rent) / old_rent
        if increase_rate > self.max_increase_rate:
            # Track prevented increase
            self.rent_increases_prevented += 1
            self.total_savings += (new_rent - (old_rent * (1 + self.max_increase_rate)))
            # Return maximum allowed rent
            return old_rent * (1 + self.max_increase_rate)
        return new_rent

    def get_metrics(self):
        """Get policy metrics"""
        return {
            "violations_found": self.violations_found,
            "improvements_required": self.improvements_required,
            "rent_increases_prevented": self.rent_increases_prevented,
            "total_tenant_savings": round(self.total_savings, 2),
            "max_increase_rate": self.max_increase_rate,
            "inspection_rate": self.inspection_rate
        }

class LandValueTaxPolicy:
    def __init__(self, lvt_rate=0.10):  # 10% annual rate
        self.lvt_rate = lvt_rate
        self.inspection_rate = 0.05  # Keep some basic inspection rate
        self.max_increase_rate = 0.10  # Allow 10% max rent increase
        self.total_lvt_collected = 0
        self.violations_found = 0
        self.improvements_required = 0
        
    def calculate_tax(self, unit, period_length=0.5):  # period_length in years
        """Calculate land value tax for a period"""
        # Update land value based on current market conditions
        unit.update_land_value(unit.landlord.market_conditions if hasattr(unit.landlord, 'market_conditions') else {})
        
        # Calculate tax on land value only
        tax = unit.land_value * self.lvt_rate * period_length
        
        # Track total tax collected
        self.total_lvt_collected += tax
        
        return tax
        
    def inspect(self, unit):
        """Inspect unit for violations"""
        if unit.quality < 0.4:
            unit.violations += 1
            self.violations_found += 1
            if unit.violations >= 3:
                self.improvements_required += 1
                # Force renovation
                unit.last_renovation = 0
                unit.quality = max(0.4, unit.quality)  # Bring up to minimum standard
                unit.violations = 0  # Reset violations after improvement
                
    def get_metrics(self):
        """Get policy metrics"""
        return {
            "total_lvt_collected": self.total_lvt_collected,
            "violations_found": self.violations_found,
            "improvements_required": self.improvements_required,
            "lvt_rate": self.lvt_rate
        }