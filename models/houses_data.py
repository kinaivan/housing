"""
Predefined house data for simulation
"""

HOUSES = [
    {
        "id": 1,
        "name": "Amsterdam Canal House",
        "description": "Historic canal house in the heart of Amsterdam with original features",
        "base_price": 350000,
        "neighborhood": "Amsterdam",
        "square_meters": 35,
        "bedrooms": 1,
        "bathrooms": 1,
        "year_built": 1906,
        "rental_yield": 0.067,
        "base_rent": 1800,  # Calculated from base_price * rental_yield / 12
        "quality": 0.85,  # High quality due to historic value and renovation
    },
    {
        "id": 2,
        "name": "Rotterdam Modern Apartment",
        "description": "Contemporary apartment in Rotterdam's trendy Kop van Zuid district",
        "base_price": 350000,
        "square_meters": 89,
        "bedrooms": 2,
        "bathrooms": 1,
        "neighborhood": "Rotterdam",
        "rental_yield": 0.065,
        "base_rent": 1600,
        "quality": 0.9,  # Very high quality due to modern amenities
    },
    {
        "id": 3,
        "name": "Eindhoven Smart Villa",
        "description": "Tech-enabled suburban home with modern amenities",
        "base_price": 1675000,
        "square_meters": 507,
        "bedrooms": 4,
        "bathrooms": 2,
        "neighborhood": "Eindhoven",
        "rental_yield": 0.067,
        "base_rent": 3500,
        "quality": 0.95,  # Highest quality due to smart features
    },
    {
        "id": 4,
        "name": "Amsterdam Suburb House",
        "description": "Spacious family home in Amsterdam's growing suburbs",
        "base_price": 220000,
        "square_meters": 160,
        "bedrooms": 4,
        "bathrooms": 2,
        "neighborhood": "Amstelveen",
        "rental_yield": 0.058,
        "base_rent": 1200,
        "quality": 0.75,  # Good quality suburban home
    },
    {
        "id": 5,
        "name": "Rotterdam Harbor View",
        "description": "Modern apartment overlooking the bustling Rotterdam harbor",
        "base_price": 180000,
        "square_meters": 85,
        "bedrooms": 2,
        "bathrooms": 1,
        "neighborhood": "Maritime District",
        "rental_yield": 0.062,
        "base_rent": 1100,
        "quality": 0.8,  # High quality with good views
    },
    {
        "id": 6,
        "name": "Traditional Dutch Row House",
        "description": "Classic Dutch row house in a established neighborhood",
        "base_price": 95000,
        "square_meters": 120,
        "bedrooms": 3,
        "bathrooms": 1,
        "neighborhood": "Old South",
        "rental_yield": 0.071,
        "base_rent": 900,
        "quality": 0.6,  # Average quality, older building
    },
    {
        "id": 7,
        "name": "Suburban Family Home",
        "description": "Comfortable family home in a quiet suburban area",
        "base_price": 85000,
        "square_meters": 140,
        "bedrooms": 4,
        "bathrooms": 2,
        "neighborhood": "Green District",
        "rental_yield": 0.068,
        "base_rent": 850,
        "quality": 0.65,  # Above average quality
    },
    {
        "id": 8,
        "name": "City Center Apartment",
        "description": "Compact but well-located apartment in the heart of the city",
        "base_price": 78000,
        "square_meters": 65,
        "bedrooms": 2,
        "bathrooms": 1,
        "neighborhood": "City Center",
        "rental_yield": 0.075,
        "base_rent": 800,
        "quality": 0.7,  # Good quality due to location
    }
] 