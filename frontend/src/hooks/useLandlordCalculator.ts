import { useState, useCallback } from 'react';

interface CalculatorInputs {
  numUnits: number;
  purchasePrice: number;
  monthlyRent: number;
  downPayment: number;
  interestRate: number;
  loanTerm: number;
  propertyTax: number;
  maintenanceRate: number;
  appreciationRate: number;
  vacancyRate: number;
  insuranceRate: number;
  utilityRate: number;
  location: 'central' | 'suburban' | 'remote';
  pointSystemRent: number;
}

interface CalculatorResults {
  monthlyMortgage: number;
  monthlyPropertyTax: number;
  monthlyMaintenance: number;
  monthlyInsurance: number;
  monthlyUtilities: number;
  monthlyVacancyLoss: number;
  monthlyGrossIncome: number;
  monthlyNetIncome: number;
  annualCashFlow: number;
  cashOnCashReturn: number;
  totalInvestment: number;
  capRate: number;
  grossRentMultiplier: number;
  debtServiceCoverageRatio: number;
  breakEvenOccupancy: number;
  yearlyData: Array<{
    year: number;
    propertyValue: number;
    equity: number;
    loanBalance: number;
    cashFlow: number;
    roi: number;
    netOperatingIncome: number;
    operatingExpenseRatio: number;
    debtCoverageRatio: number;
  }>;
  riskMetrics: {
    vacancyRiskScore: number;
    cashFlowRiskScore: number;
    appreciationRiskScore: number;
    overallRiskScore: number;
    breakEvenMonths: number;
  };
  locationMetrics: {
    priceToPointRentRatio: number;
    marketRentPremium: number;
    relativeROI: number;
    locationProfitabilityScore: number;
    pointSystemImpact: number;
  };
}

const DEFAULT_INPUTS: CalculatorInputs = {
  numUnits: 1,
  purchasePrice: 300000,
  monthlyRent: 1800,
  downPayment: 35,
  interestRate: 3.5,
  loanTerm: 30,
  propertyTax: 0.6,
  maintenanceRate: 8,
  appreciationRate: 2.0,
  vacancyRate: 5,
  insuranceRate: 0.5,
  utilityRate: 2,
  location: 'central',
  pointSystemRent: 1500
};

export const useLandlordCalculator = () => {
  const [inputs, setInputs] = useState<CalculatorInputs>(DEFAULT_INPUTS);
  const [results, setResults] = useState<CalculatorResults | null>(null);

  const calculateMortgage = (principal: number, rate: number, years: number): number => {
    const monthlyRate = rate / 100 / 12;
    const numPayments = years * 12;
    return (
      (principal * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
      (Math.pow(1 + monthlyRate, numPayments) - 1)
    );
  };

  const calculateRiskScores = (
    vacancyRate: number,
    cashFlow: number,
    totalInvestment: number,
    appreciationRate: number
  ) => {
    // Vacancy risk (higher vacancy rate = higher risk)
    const vacancyRiskScore = Math.min(100, (vacancyRate / 10) * 100);

    // Cash flow risk (lower cash on cash return = higher risk)
    const cashOnCash = (cashFlow / totalInvestment) * 100;
    const cashFlowRiskScore = Math.max(0, 100 - (cashOnCash * 10));

    // Appreciation risk (lower appreciation = higher risk)
    const appreciationRiskScore = Math.max(0, 100 - (appreciationRate * 20));

    // Overall risk score (weighted average)
    const overallRiskScore = (
      vacancyRiskScore * 0.3 +
      cashFlowRiskScore * 0.4 +
      appreciationRiskScore * 0.3
    );

    return {
      vacancyRiskScore,
      cashFlowRiskScore,
      appreciationRiskScore,
      overallRiskScore,
    };
  };

  const calculateLocationMetrics = (
    purchasePrice: number,
    pointSystemRent: number,
    monthlyRent: number,
    location: string,
    cashOnCashReturn: number
  ) => {
    // Calculate location-specific metrics
    const priceToPointRentRatio = purchasePrice / (pointSystemRent * 12);
    const marketRentPremium = ((monthlyRent - pointSystemRent) / pointSystemRent) * 100;
    
    // Location-based ROI factors
    const locationFactors = {
      central: { roiBase: 4, appreciationBonus: 2 },
      suburban: { roiBase: 5, appreciationBonus: 1 },
      remote: { roiBase: 6, appreciationBonus: 0 }
    };
    
    const factor = locationFactors[location as keyof typeof locationFactors];
    const relativeROI = (cashOnCashReturn / factor.roiBase) * 100;
    
    // Calculate profitability score (higher for remote locations due to point system)
    const locationProfitabilityScore = (
      (relativeROI * 0.4) +
      ((1 / priceToPointRentRatio) * 100 * 0.4) +
      (marketRentPremium * 0.2)
    );
    
    // Calculate point system impact (higher means more impact)
    const pointSystemImpact = Math.min(
      100,
      Math.abs(marketRentPremium) * 0.7 +
      (location === 'central' ? 30 : location === 'suburban' ? 20 : 10)
    );
    
    return {
      priceToPointRentRatio,
      marketRentPremium,
      relativeROI,
      locationProfitabilityScore,
      pointSystemImpact
    };
  };

  const calculate = useCallback(() => {
    const totalPurchasePrice = inputs.numUnits * inputs.purchasePrice;
    const downPaymentAmount = (totalPurchasePrice * inputs.downPayment) / 100;
    const loanAmount = totalPurchasePrice - downPaymentAmount;
    
    const monthlyMortgage = calculateMortgage(loanAmount, inputs.interestRate, inputs.loanTerm);
    const monthlyPropertyTax = (totalPurchasePrice * inputs.propertyTax) / 100 / 12;
    const totalMonthlyRent = inputs.numUnits * inputs.monthlyRent;
    const monthlyMaintenance = (totalMonthlyRent * inputs.maintenanceRate) / 100;
    const monthlyInsurance = (totalPurchasePrice * inputs.insuranceRate) / 100 / 12;
    const monthlyUtilities = (totalMonthlyRent * inputs.utilityRate) / 100;
    const monthlyVacancyLoss = (totalMonthlyRent * inputs.vacancyRate) / 100;
    
    const monthlyGrossIncome = totalMonthlyRent;
    const monthlyOperatingExpenses = monthlyPropertyTax + monthlyMaintenance + monthlyInsurance + monthlyUtilities + monthlyVacancyLoss;
    const monthlyNetIncome = monthlyGrossIncome - monthlyOperatingExpenses - monthlyMortgage;
    const annualCashFlow = monthlyNetIncome * 12;
    const cashOnCashReturn = (annualCashFlow / downPaymentAmount) * 100;

    // Additional financial metrics
    const annualGrossIncome = monthlyGrossIncome * 12;
    const annualOperatingExpenses = monthlyOperatingExpenses * 12;
    const netOperatingIncome = annualGrossIncome - annualOperatingExpenses;
    const capRate = (netOperatingIncome / totalPurchasePrice) * 100;
    const grossRentMultiplier = totalPurchasePrice / annualGrossIncome;
    const debtServiceCoverageRatio = netOperatingIncome / (monthlyMortgage * 12);
    
    // Break-even calculations
    const monthlyExpensesPerUnit = (monthlyMortgage + monthlyOperatingExpenses) / inputs.numUnits;
    const breakEvenOccupancy = (monthlyExpensesPerUnit / inputs.monthlyRent) * 100;
    const breakEvenMonths = Math.ceil(downPaymentAmount / monthlyNetIncome);

    const yearlyData = Array.from({ length: inputs.loanTerm }, (_, i) => {
      const year = i + 1;
      const propertyValue = totalPurchasePrice * Math.pow(1 + inputs.appreciationRate / 100, year);
      
      // Calculate remaining loan balance
      const monthlyRate = inputs.interestRate / 100 / 12;
      const remainingPayments = (inputs.loanTerm - year) * 12;
      const loanBalance = remainingPayments > 0 
        ? (monthlyMortgage * (1 - Math.pow(1 + monthlyRate, -remainingPayments))) / monthlyRate
        : 0;
      
      const equity = propertyValue - loanBalance;
      const cashFlow = annualCashFlow;
      const roi = ((equity - downPaymentAmount + cashFlow * year) / downPaymentAmount) * 100;
      
      // Calculate year-specific operating metrics
      const yearlyGrossIncome = monthlyGrossIncome * 12 * Math.pow(1.02, year); // Assume 2% annual rent increase
      const yearlyOperatingExpenses = monthlyOperatingExpenses * 12 * Math.pow(1.03, year); // Assume 3% annual expense increase
      const yearlyNetOperatingIncome = yearlyGrossIncome - yearlyOperatingExpenses;
      const operatingExpenseRatio = (yearlyOperatingExpenses / yearlyGrossIncome) * 100;
      const debtCoverageRatio = yearlyNetOperatingIncome / (monthlyMortgage * 12);

      return {
        year,
        propertyValue,
        equity,
        loanBalance,
        cashFlow,
        roi,
        netOperatingIncome: yearlyNetOperatingIncome,
        operatingExpenseRatio,
        debtCoverageRatio,
      };
    });

    const riskScores = calculateRiskScores(
      inputs.vacancyRate,
      annualCashFlow,
      downPaymentAmount,
      inputs.appreciationRate
    );

    const locationMetrics = calculateLocationMetrics(
      totalPurchasePrice,
      inputs.pointSystemRent,
      inputs.monthlyRent,
      inputs.location,
      cashOnCashReturn
    );

    setResults({
      monthlyMortgage,
      monthlyPropertyTax,
      monthlyMaintenance,
      monthlyInsurance,
      monthlyUtilities,
      monthlyVacancyLoss,
      monthlyGrossIncome,
      monthlyNetIncome,
      annualCashFlow,
      cashOnCashReturn,
      totalInvestment: downPaymentAmount,
      capRate,
      grossRentMultiplier,
      debtServiceCoverageRatio,
      breakEvenOccupancy,
      yearlyData,
      riskMetrics: {
        ...riskScores,
        breakEvenMonths,
      },
      locationMetrics
    });
  }, [inputs]);

  const updateInput = (name: keyof CalculatorInputs, value: number | string) => {
    setInputs(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return {
    inputs,
    results,
    updateInput,
    calculate,
  };
}; 