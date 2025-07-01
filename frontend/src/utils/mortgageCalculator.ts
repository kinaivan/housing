import { MortgageStats, YearlyData, House, Bank, PropertyType } from '../types';

const MORTGAGE_INTEREST_DEDUCTION_RATE = 0.37; // 37% tax deduction on mortgage interest
const PROPERTY_TAX_RATE = 0.0284; // 2.84% yearly property tax
const MAINTENANCE_RATE = 0.01; // 1% yearly maintenance cost
const INSURANCE_RATE = 0.0035; // 0.35% yearly insurance cost
const PROPERTY_MANAGEMENT_FEE_RATE = 0.08; // 8% of rental income
const AVERAGE_VACANCY_RATE = 0.08; // 8% vacancy rate

export function calculateMortgage(
  housePrice: number,
  interestRate: number,
  loanTerm: number = 30,
  yearlyIncome: number,
  propertyType: PropertyType,
  house: House,
): { stats: MortgageStats; yearlyData: YearlyData[] } {
  const monthlyInterestRate = interestRate / 100 / 12;
  const totalPayments = loanTerm * 12;
  
  // Calculate base mortgage payment using PMT formula
  const monthlyPayment =
    (housePrice * monthlyInterestRate * Math.pow(1 + monthlyInterestRate, totalPayments)) /
    (Math.pow(1 + monthlyInterestRate, totalPayments) - 1);
  
  const yearlyPayment = monthlyPayment * 12;
  
  // Calculate yearly costs
  const yearlyPropertyTax = housePrice * PROPERTY_TAX_RATE;
  const yearlyMaintenance = housePrice * MAINTENANCE_RATE;
  const yearlyInsurance = housePrice * INSURANCE_RATE;
  
  // Initialize rental-specific variables
  let yearlyRentalIncome = 0;
  let yearlyRentalExpenses = 0;
  let netRentalYield = 0;
  let vacancyRate = 0;
  let propertyManagementFee = 0;
  let netOperatingIncome = 0;
  let cashOnCashReturn = 0;
  let capitalizationRate = 0;

  if (propertyType === 'rental') {
    yearlyRentalIncome = house.monthlyRent! * 12;
    vacancyRate = AVERAGE_VACANCY_RATE;
    propertyManagementFee = yearlyRentalIncome * PROPERTY_MANAGEMENT_FEE_RATE;
    yearlyRentalExpenses = yearlyPropertyTax + yearlyMaintenance + yearlyInsurance + propertyManagementFee;
    netOperatingIncome = yearlyRentalIncome * (1 - vacancyRate) - yearlyRentalExpenses;
    netRentalYield = (netOperatingIncome / housePrice) * 100;
    capitalizationRate = (netOperatingIncome / housePrice) * 100;
    cashOnCashReturn = (netOperatingIncome - yearlyPayment) / (housePrice * 0.2) * 100; // Assuming 20% down payment
  }

  // Calculate yearly amortization schedule
  const yearlyData: YearlyData[] = [];
  let remainingBalance = housePrice;
  let totalInterest = 0;
  let propertyValue = housePrice;
  const propertyAppreciationRate = 0.03; // 3% yearly appreciation

  for (let year = 1; year <= loanTerm; year++) {
    const yearlyInterest = remainingBalance * (interestRate / 100);
    const yearlyPrincipal = yearlyPayment - yearlyInterest;
    remainingBalance -= yearlyPrincipal;
    totalInterest += yearlyInterest;
    propertyValue *= (1 + propertyAppreciationRate);
    
    const yearData: YearlyData = {
      year,
      interest: yearlyInterest,
      principal: yearlyPrincipal,
      remainingBalance: Math.max(0, remainingBalance),
      propertyValue,
      netEquity: propertyValue - Math.max(0, remainingBalance),
    };

    if (propertyType === 'rental') {
      yearData.rentalIncome = yearlyRentalIncome * (1 - vacancyRate);
      yearData.netOperatingIncome = netOperatingIncome;
      yearData.cashFlow = netOperatingIncome - yearlyPayment;
    }

    yearlyData.push(yearData);
  }

  // Calculate tax savings for owner-occupied homes
  const taxSavings = propertyType === 'owner' 
    ? totalInterest * MORTGAGE_INTEREST_DEDUCTION_RATE 
    : undefined;

  // Calculate affordability metrics
  const affordabilityRatio = yearlyPayment / yearlyIncome;
  const debtToIncomeRatio = housePrice / yearlyIncome;
  
  // Find break-even point (when net equity exceeds total payments)
  const totalPaymentsByYear = yearlyData.map((data, index) => 
    yearlyPayment * (index + 1) + 
    (yearlyPropertyTax + yearlyMaintenance + yearlyInsurance) * (index + 1)
  );
  
  const breakEvenYear = yearlyData.findIndex(
    (data, index) => data.netEquity > totalPaymentsByYear[index]
  ) + 1;

  const stats: MortgageStats = {
    totalCost: yearlyPayment * loanTerm,
    totalInterest,
    monthlyPayment,
    yearlyPayment,
    breakEvenYear,
    affordabilityRatio,
    debtToIncomeRatio,
    taxSavings,
    maintenanceCosts: yearlyMaintenance,
    propertyTax: yearlyPropertyTax,
    insuranceCosts: yearlyInsurance,
    // Rental specific fields
    rentalIncome: yearlyRentalIncome,
    netRentalYield,
    rentalExpenses: yearlyRentalExpenses,
    vacancyRate,
    propertyManagementFee,
    netOperatingIncome,
    cashOnCashReturn,
    capitalizationRate,
  };

  return { stats, yearlyData };
} 