export type Year = 1990 | 2000 | 2024;
export type PropertyType = 'owner' | 'rental';

export interface Person {
  id: number;
  name: string;
  age: number;
  yearOfReference: number;
  monthlyIncome: number;
  wealth: number;
  description: string;
  creditScore: number;
  employmentYears: number;
  hasStudentDebt: boolean;
  monthlyDebts: number;
}

export interface House {
  id: number;
  name: string;
  description: string;
  basePrice: number;
  yearBuilt: number;
  squareMeters: number;
  bedrooms: number;
  bathrooms: number;
  neighborhood: string;
  rentalYield: number;
  availableFrom: number;
  availableTo: number;
  imageUrl: string;
  features: string[];
}

export interface Bank {
  id: string;
  title: string;
  description: string;
  interestRates: {
    [key in Year]: number;
  };
  imageUrl: string;
  loanToValue: number;
  maxLoanTerm: number;
}

export interface MortgageStats {
  totalCost: number;
  totalInterest: number;
  monthlyPayment: number;
  yearlyPayment: number;
  breakEvenYear: number;
  affordabilityRatio: number;
  debtToIncomeRatio: number;
  taxSavings?: number;
  maintenanceCosts: number;
  propertyTax: number;
  insuranceCosts: number;
  // Rental specific fields
  rentalIncome?: number;
  netRentalYield?: number;
  rentalExpenses?: number;
  vacancyRate?: number;
  propertyManagementFee?: number;
  netOperatingIncome?: number;
  cashOnCashReturn?: number;
  capitalizationRate?: number;
}

export interface YearlyData {
  year: number;
  interest: number;
  principal: number;
  remainingBalance: number;
  propertyValue: number;
  netEquity: number;
  // Rental specific fields
  rentalIncome?: number;
  netOperatingIncome?: number;
  cashFlow?: number;
}

export interface AffordabilityStatus {
  color: 'success' | 'warning' | 'error';
  text: string;
}

export interface SelectedOptions {
  person: string;
  house: string;
  bank: string;
} 