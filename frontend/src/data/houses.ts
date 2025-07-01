import { House } from '../types';

export const houses: House[] = [
  // 2024 Modern Houses
  {
    id: 1,
    name: 'Amsterdam Canal House',
    description: 'Historic canal house in the heart of Amsterdam with original features',
    basePrice: 350000,
    imageUrl: '/houses/amsterdam-canal.jpg',
    neighborhood: 'Amsterdam',
    squareMeters: 35,
    bedrooms: 1,
    bathrooms: 1,
    yearBuilt: 1906,
    rentalYield: 0.067,
    availableFrom: 2015,
    availableTo: 2024,
    features: ["Historic", "Canal View", "Renovated", "High Ceilings"]
  },
  {
    id: 2,
    name: "Rotterdam Modern Apartment",
    description: "Contemporary apartment in Rotterdam's trendy Kop van Zuid district",
    basePrice: 350000,
    yearBuilt: 1974,
    squareMeters: 89,
    bedrooms: 2,
    bathrooms: 1,
    neighborhood: "Rotterdam",
    rentalYield: 0.065, // 6.5%
    availableFrom: 2015,
    availableTo: 2024,
    imageUrl: "/houses/rotterdam-modern.jpg",
    features: ["Modern", "River View", "Parking", "Balcony"]
  },
  {
    id: 3,
    name: "Eindhoven Smart Villa",
    description: "Tech-enabled suburban home with modern amenities",
    basePrice: 1675000,
    yearBuilt: 1978,
    squareMeters: 507,
    bedrooms: 4,
    bathrooms: 2,
    neighborhood: "Eindhoven",
    rentalYield: 0.067, // 6.7%
    availableFrom: 2020,
    availableTo: 2024,
    imageUrl: "/houses/eindhoven-smart.jpg",
    features: ["Smart Home", "Energy Efficient", "Garden", "Open Plan"]
  },

  // 2000s Houses
  {
    id: 4,
    name: "Amsterdam Suburb House",
    description: "Spacious family home in Amsterdam's growing suburbs",
    basePrice: 220000,
    yearBuilt: 1995,
    squareMeters: 160,
    bedrooms: 4,
    bathrooms: 2,
    neighborhood: "Amstelveen",
    rentalYield: 0.058,
    availableFrom: 1995,
    availableTo: 2005,
    imageUrl: "/houses/amsterdam-villa.jpg",
    features: ["Family-Friendly", "Garden", "Quiet Area", "Near Schools"]
  },
  {
    id: 5,
    name: "Rotterdam Harbor View",
    description: "Modern apartment overlooking the bustling Rotterdam harbor",
    basePrice: 180000,
    yearBuilt: 1998,
    squareMeters: 85,
    bedrooms: 2,
    bathrooms: 1,
    neighborhood: "Maritime District",
    rentalYield: 0.062,
    availableFrom: 1998,
    availableTo: 2005,
    imageUrl: "/houses/rotterdam-harbor.jpg",
    features: ["Harbor View", "Recently Built", "Security", "Parking"]
  },

  // 1990s Houses
  {
    id: 6,
    name: "Traditional Dutch Row House",
    description: "Classic Dutch row house in a established neighborhood",
    basePrice: 95000,
    yearBuilt: 1960,
    squareMeters: 120,
    bedrooms: 3,
    bathrooms: 1,
    neighborhood: "Old South",
    rentalYield: 0.071,
    availableFrom: 1960,
    availableTo: 1995,
    imageUrl: "/houses/dutch-row.jpg",
    features: ["Traditional", "Garden", "Storage", "Brick Construction"]
  },
  {
    id: 7,
    name: "Suburban Family Home",
    description: "Comfortable family home in a quiet suburban area",
    basePrice: 85000,
    yearBuilt: 1975,
    squareMeters: 140,
    bedrooms: 4,
    bathrooms: 2,
    neighborhood: "Green District",
    rentalYield: 0.068,
    availableFrom: 1975,
    availableTo: 1995,
    imageUrl: "/houses/suburban-home.jpg",
    features: ["Family-Sized", "Large Garden", "Garage", "Near Park"]
  },
  {
    id: 8,
    name: "City Center Apartment",
    description: "Compact but well-located apartment in the heart of the city",
    basePrice: 78000,
    yearBuilt: 1965,
    squareMeters: 65,
    bedrooms: 2,
    bathrooms: 1,
    neighborhood: "City Center",
    rentalYield: 0.075,
    availableFrom: 1965,
    availableTo: 1995,
    imageUrl: "/houses/city-apartment.jpg",
    features: ["Central Location", "Public Transport", "Balcony", "Storage"]
  }
]; 