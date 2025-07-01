import React, { useState, useMemo } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Button,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Modal,
  Alert,
  Tabs,
  Tab,
  CircularProgress,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
  Stack,
  Card,
  CardContent,
  Chip,
  Grid,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  PieLabelRenderProps,
} from 'recharts';
import InfoIcon from '@mui/icons-material/Info';
import { Person } from '../types';
import { people } from '../data/people';
import { houses } from '../data/houses';
import { bankOptions } from '../data/banks';
import { colors } from '../theme';
import { formatCurrency } from '../utils/formatters';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import RestartAltIcon from '@mui/icons-material/RestartAlt';

interface Option {
  id: string;
  title: string;
  description: string;
  imageUrl: string;
}

// Historical interest rates for Dutch banks (example data)
type Year = 1990 | 2000 | 2024;
type Bank = 'ing' | 'abnamro' | 'rabobank';
type BankRates = {
  [key in Year]: {
    [key in Bank]: number;
  };
};

const bankRates: BankRates = {
  1990: {
    ing: 8.5,
    abnamro: 8.7,
    rabobank: 8.3,
  },
  2000: {
    ing: 6.2,
    abnamro: 6.4,
    rabobank: 6.1,
  },
  2024: {
    ing: 4.1,
    abnamro: 4.3,
    rabobank: 4.0,
  },
};

const peopleOptions: Option[] = [
  {
    id: 'person1',
    title: '50 year old in 1990',
    description: 'Middle-aged professional with established career and savings',
    imageUrl: '/people/person1.jpg',
  },
  {
    id: 'person2',
    title: '23 year old in 2024',
    description: 'Young professional starting their career in the modern market',
    imageUrl: '/people/person2.jpg',
  },
  {
    id: 'person3',
    title: '75 year old in 2000',
    description: 'Retiree with pension and investment income',
    imageUrl: '/people/person3.jpg',
  },
];

interface HouseOption extends Option {
  basePrice: number;
}

const houseOptions: HouseOption[] = [
  {
    id: 'house1',
    title: 'Amsterdam Canal House',
    description: 'Historic 17th century canal house in central Amsterdam. Features original details, 3 floors, and canal views.',
    imageUrl: '/houses/canal-house.jpg',
    basePrice: 450000,
  },
  {
    id: 'house2',
    title: 'Rotterdam Modern Apartment',
    description: 'Contemporary high-rise apartment in Rotterdam with panoramic city views. Modern amenities and excellent location.',
    imageUrl: '/houses/rotterdam-apartment.jpg',
    basePrice: 350000,
  },
  {
    id: 'house3',
    title: 'Eindhoven Suburban Home',
    description: 'Family home in a quiet Eindhoven neighborhood. Spacious garden and close to tech campus.',
    imageUrl: '/houses/eindhoven-home.jpg',
    basePrice: 300000,
  },
  {
    id: 'house4',
    title: 'Drenthe Farmhouse',
    description: 'Traditional Dutch farmhouse with 2 hectares of land in peaceful Drenthe countryside. Perfect for sustainable living.',
    imageUrl: '/houses/drenthe-farm.jpg',
    basePrice: 275000,
  },
  {
    id: 'house5',
    title: 'Groningen Townhouse',
    description: 'Traditional Dutch townhouse in Groningen city center. Walking distance to markets and cultural attractions.',
    imageUrl: '/houses/groningen-house.jpg',
    basePrice: 280000,
  },
];

const getBankOptions = (selectedPersonId: string): Option[] => {
  let year: Year = 2024;
  if (selectedPersonId === 'person1') year = 1990;
  if (selectedPersonId === 'person3') year = 2000;

  const rates = bankRates[year];

  return [
    {
      id: 'ing',
      title: 'ING Bank',
      description: `Interest rate: ${rates.ing}% (${year})`,
      imageUrl: '/banks/ing.jpg',
    },
    {
      id: 'abnamro',
      title: 'ABN AMRO',
      description: `Interest rate: ${rates.abnamro}% (${year})`,
      imageUrl: '/banks/abnamro.jpg',
    },
    {
      id: 'rabobank',
      title: 'Rabobank',
      description: `Interest rate: ${rates.rabobank}% (${year})`,
      imageUrl: '/banks/rabobank.jpg',
    },
  ];
};

interface CostBreakdownProps {
  open: boolean;
  onClose: () => void;
  selectedOptions: {
    person: string;
    house: string;
    bank: string;
  };
}

type HouseId = 'house1' | 'house2' | 'house3' | 'house4' | 'house5';
type BasePrices = {
  [key in HouseId]: number;
};
type PriceMultiplier = {
  [key in Year]: number;
};

const getHousePrice = (houseId: HouseId, year: Year): number => {
  // Example price mapping (you can adjust these)
  const basePrices: BasePrices = {
    house1: 450000, // Amsterdam Canal House
    house2: 350000, // Rotterdam Modern Apartment
    house3: 300000, // Eindhoven Suburban Home
    house4: 200000, // Utrecht Student Studio
    house5: 280000, // Groningen Townhouse
  };

  // Apply historical price adjustment
  const priceMultiplier: PriceMultiplier = {
    1990: 0.25, // Prices were roughly 25% of current prices
    2000: 0.45, // Prices were roughly 45% of current prices
    2024: 1.0,  // Current prices
  };

  return basePrices[houseId] * priceMultiplier[year];
};

type PropertyType = 'owner' | 'rental';

interface MortgageStats {
  totalCost: number;
  totalInterest: number;
  monthlyPayment: number;
  yearlyPayment: number;
  breakEvenYear: number;
  affordabilityRatio: number;
  debtToIncomeRatio: number;
  taxSavings?: number;
  maintenanceCosts?: number;
  propertyTax?: number;
  insuranceCosts?: number;
  rentalIncome?: number;
  netRentalYield?: number;
}

interface YearlyData {
  year: number;
  payment: number;
  principal: number;
  interest: number;
  remainingBalance: number;
  totalPaidToDate: number;
  totalInterestToDate: number;
  propertyValue: number;
  netEquity: number;
  taxSavings?: number;
  propertyTax?: number;
  maintenanceCost?: number;
  insuranceCost?: number;
  rentalIncome?: number;
}

const calculateDetailedMortgage = (
  principal: number, 
  rate: number, 
  years: number = 20,
  yearlyIncome: number,
  yearlyAppreciation: number = 0.03,
  propertyType: PropertyType = 'owner',
  year: number = 2024
): { yearlyData: YearlyData[], stats: MortgageStats } => {
  const monthlyRate = rate / 100 / 12;
  const numberOfPayments = years * 12;
  const monthlyPayment = (principal * monthlyRate * Math.pow(1 + monthlyRate, numberOfPayments)) / 
                        (Math.pow(1 + monthlyRate, numberOfPayments) - 1);
  
  const yearlyData: YearlyData[] = [];
  let remainingPrincipal = principal;
  let totalPaid = 0;
  let totalInterest = 0;
  let breakEvenYear = 0;
  let propertyValue = principal;
  let totalTaxSavings = 0;
  
  // Dutch-specific costs and tax rates based on historical periods
  const getHistoricalRates = (year: number) => {
    if (year <= 1995) {
      return {
        propertyTaxRate: 0.008, // Lower OZB rates in 1990s
        maintenanceRate: 0.012, // Higher maintenance due to older building standards
        insuranceRate: 0.002, // Lower insurance costs
        rentalYield: 0.055, // Higher rental yields in 1990s
        incomeTaxRate: propertyType === 'owner' ? 0.42 : 0.52, // Higher marginal rates, different for rental
        capitalGainsTax: propertyType === 'rental' ? 0.25 : 0, // No capital gains for owner-occupied
        rentalIncomeTax: 0.52, // High rental income tax in 1990s
      };
    } else if (year <= 2005) {
      return {
        propertyTaxRate: 0.009,
        maintenanceRate: 0.011,
        insuranceRate: 0.0025,
        rentalYield: 0.048,
        incomeTaxRate: propertyType === 'owner' ? 0.37 : 0.42,
        capitalGainsTax: propertyType === 'rental' ? 0.20 : 0,
        rentalIncomeTax: 0.42,
      };
    } else {
      return {
        propertyTaxRate: 0.0107, // Current OZB + water tax
        maintenanceRate: 0.01,
        insuranceRate: 0.003,
        rentalYield: 0.042, // Lower yields due to higher property prices
        incomeTaxRate: propertyType === 'owner' ? 0.37 : 0.495, // Box 3 wealth tax for rental
        capitalGainsTax: propertyType === 'rental' ? 0.31 : 0, // Current capital gains
        rentalIncomeTax: 0.495, // Current top rate for rental income
      };
    }
  };

  const rates = getHistoricalRates(year);
  
  for (let yearNum = 1; yearNum <= years; yearNum++) {
    const yearlyPayment = monthlyPayment * 12;
    const yearlyInterest = remainingPrincipal * (rate / 100);
    const yearlyPrincipal = yearlyPayment - yearlyInterest;
    
    // Calculate Dutch-specific tax benefits and costs
    const propertyTax = propertyValue * rates.propertyTaxRate;
    const maintenanceCost = propertyValue * rates.maintenanceRate;
    const insuranceCost = propertyValue * rates.insuranceRate;
    const rentalIncome = propertyType === 'rental' ? propertyValue * rates.rentalYield : 0;
    
    // Tax calculations based on property type and year
    let taxSavings = 0;
    let rentalTax = 0;
    
    if (propertyType === 'owner') {
      // Owner-occupied: mortgage interest deduction
      taxSavings = yearlyInterest * rates.incomeTaxRate;
    } else {
      // Rental property: rental income tax
      rentalTax = rentalIncome * rates.rentalIncomeTax;
      // Rental properties can also deduct mortgage interest as business expense
      taxSavings = yearlyInterest * rates.rentalIncomeTax;
    }
    
    totalTaxSavings += taxSavings;
    
    remainingPrincipal -= yearlyPrincipal;
    const netRentalIncome = rentalIncome - rentalTax;
    totalPaid += yearlyPayment + propertyTax + maintenanceCost + insuranceCost - taxSavings - netRentalIncome;
    totalInterest += yearlyInterest;
    propertyValue *= (1 + yearlyAppreciation);

    const netEquity = propertyValue - remainingPrincipal;
    
    if (netEquity > totalPaid && breakEvenYear === 0) {
      breakEvenYear = yearNum;
    }

    yearlyData.push({
      year: yearNum,
      payment: yearlyPayment,
      principal: yearlyPrincipal,
      interest: yearlyInterest,
      remainingBalance: Math.max(0, remainingPrincipal),
      totalPaidToDate: totalPaid,
      totalInterestToDate: totalInterest,
      propertyValue,
      netEquity,
      taxSavings,
      propertyTax,
      maintenanceCost,
      insuranceCost,
      rentalIncome: netRentalIncome,
    });
  }

  const finalRates = getHistoricalRates(year);
  const yearlyPropertyTax = propertyValue * finalRates.propertyTaxRate;
  const yearlyMaintenance = propertyValue * finalRates.maintenanceRate;
  const yearlyInsurance = propertyValue * finalRates.insuranceRate;
  const yearlyRentalIncome = propertyType === 'rental' ? 
    (propertyValue * finalRates.rentalYield) * (1 - finalRates.rentalIncomeTax) : 0;

  const stats: MortgageStats = {
    totalCost: totalPaid,
    totalInterest,
    monthlyPayment,
    yearlyPayment: monthlyPayment * 12,
    breakEvenYear: breakEvenYear || years,
    affordabilityRatio: (monthlyPayment * 12) / yearlyIncome,
    debtToIncomeRatio: principal / yearlyIncome,
    taxSavings: totalTaxSavings,
    propertyTax: yearlyPropertyTax,
    maintenanceCosts: yearlyMaintenance,
    insuranceCosts: yearlyInsurance,
    rentalIncome: yearlyRentalIncome,
    netRentalYield: yearlyRentalIncome / principal,
  };

  return { yearlyData, stats };
};

type PersonId = 'person1' | 'person2' | 'person3';
type IncomeMap = {
  [key in PersonId]: number;
};

const getYearlyIncome = (personId: PersonId, year: Year): number => {
  // Example income levels based on age and year
  const incomeMap: IncomeMap = {
    person1: 45000, // 50-year-old in 1990
    person2: 38000, // 23-year-old in 2024
    person3: 52000, // 75-year-old in 2000 (pension + investments)
  };
  
  // Apply historical income adjustment
  const incomeMultiplier = {
    1990: 0.4,  // Incomes were roughly 40% of current levels
    2000: 0.6,  // Incomes were roughly 60% of current levels
    2024: 1.0,  // Current income levels
  };

  return incomeMap[personId] * incomeMultiplier[year];
};

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function CostBreakdown({ open, onClose, selectedOptions, propertyType }: CostBreakdownProps & { propertyType: PropertyType }) {
  const [tabValue, setTabValue] = useState(0);
  // Resolve selected entities from data arrays
  const person = people.find(p => p.id.toString() === selectedOptions.person);
  const house = houses.find(h => h.id.toString() === selectedOptions.house);
  const bank = bankOptions.find(b => b.id === selectedOptions.bank);

  if (!person || !house || !bank) {
    return null; // Early return if something is missing
  }

  const year = person.yearOfReference as Year;
  const yearlyIncome = person.monthlyIncome * 12;
  const housePrice = house.basePrice;
  const interestRate = bank.interestRates[year as keyof typeof bank.interestRates];

  // Safety fallback if rate is undefined
  if (interestRate === undefined) {
    return null;
  }

  const { yearlyData, stats } = calculateDetailedMortgage(housePrice, interestRate, 20, yearlyIncome, 0.03, propertyType, year);

  const formatCurrency = (amount: number) => 
    new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(amount);
  
  const formatPercent = (value: number) => 
    new Intl.NumberFormat('nl-NL', { style: 'percent', minimumFractionDigits: 1 }).format(value);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getAffordabilityStatus = (ratio: number) => {
    if (ratio <= 0.28) return { color: 'success', text: 'Affordable' };
    if (ratio <= 0.36) return { color: 'warning', text: 'Moderate' };
    return { color: 'error', text: 'High Risk' };
  };

  const affordabilityStatus = getAffordabilityStatus(stats.affordabilityRatio);

  const pieData = propertyType === 'owner' ? [
    { name: 'Principal', value: housePrice },
    { name: 'Interest', value: stats.totalInterest },
    { name: 'Property Tax', value: stats.propertyTax! * 20 },
    { name: 'Maintenance', value: stats.maintenanceCosts! * 20 },
    { name: 'Insurance', value: stats.insuranceCosts! * 20 },
    { name: 'Tax Savings', value: -stats.taxSavings! },
  ] : [
    { name: 'Principal', value: housePrice },
    { name: 'Interest', value: stats.totalInterest },
    { name: 'Property Tax', value: stats.propertyTax! * 20 },
    { name: 'Maintenance', value: stats.maintenanceCosts! * 20 },
    { name: 'Insurance', value: stats.insuranceCosts! * 20 },
    { name: 'Rental Income', value: -stats.rentalIncome! * 20 },
  ];

  const COLORS = ['#0088FE', '#FF8042', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  const renderPieLabel = (props: PieLabelRenderProps) => {
    const { name, value, percent } = props;
    // Only show percentage for slices bigger than 5% to avoid overlap
    if ((percent || 0) < 0.05) return '';
    return `${((percent || 0) * 100).toFixed(0)}%`;
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="cost-breakdown-modal"
    >
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '95%',
        maxWidth: '1200px',
        maxHeight: '90vh',
        bgcolor: 'background.paper',
        boxShadow: 24,
        p: 4,
        overflow: 'auto',
      }}>
        <Typography variant="h5" gutterBottom>
          {propertyType === 'owner' ? 'Owner-Occupied' : 'Rental Property'} Cost Analysis
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Overview" />
            <Tab label="Monthly Details" />
            <Tab label="Long-term Projection" />
            <Tab label="Risk Analysis" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Stack direction={{ xs: 'column', lg: 'row' }} spacing={3}>
            <Box flex={1}>
              <Paper elevation={2} sx={{ p: 3, mb: 2, height: 'fit-content' }}>
                <Typography variant="h6" gutterBottom>Key Figures</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Typography>House Price: {formatCurrency(housePrice)}</Typography>
                  <Typography>Interest Rate: {interestRate}% ({year})</Typography>
                  <Typography>Monthly Payment: {formatCurrency(stats.monthlyPayment)}</Typography>
                  <Typography>Total Cost (20 years): {formatCurrency(stats.totalCost)}</Typography>
                  <Typography>Total Interest: {formatCurrency(stats.totalInterest)}</Typography>
                  {propertyType === 'owner' ? (
                    <Typography>Tax Savings (20 years): {formatCurrency(stats.taxSavings!)}</Typography>
                  ) : (
                    <Typography>Rental Income (yearly): {formatCurrency(stats.rentalIncome!)}</Typography>
                  )}
                  <Typography>Property Tax (yearly): {formatCurrency(stats.propertyTax!)}</Typography>
                  <Typography>Maintenance (yearly): {formatCurrency(stats.maintenanceCosts!)}</Typography>
                  <Typography>Insurance (yearly): {formatCurrency(stats.insuranceCosts!)}</Typography>
                  {propertyType === 'rental' && (
                    <Typography>Net Rental Yield: {formatPercent(stats.netRentalYield!)}</Typography>
                  )}
                </Box>
              </Paper>
            </Box>
            <Box flex={1}>
              <Paper elevation={2} sx={{ p: 3, mb: 2, height: 'fit-content' }}>
                <Typography variant="h6" gutterBottom>Cost Distribution</Typography>
                <Box sx={{ height: 350, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <ResponsiveContainer width="100%" height="80%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={100}
                        fill="#8884d8"
                        paddingAngle={2}
                        dataKey="value"
                        label={renderPieLabel}
                        labelLine={false}
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip 
                        formatter={(value: number, name: string) => [
                          formatCurrency(Math.abs(value)), 
                          name
                        ]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  {/* Legend */}
                  <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                    {pieData.map((entry, index) => (
                      <Box key={entry.name} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Box 
                          sx={{ 
                            width: 12, 
                            height: 12, 
                            backgroundColor: COLORS[index % COLORS.length],
                            borderRadius: '2px'
                          }} 
                        />
                        <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                          {entry.name}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              </Paper>
            </Box>
          </Stack>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Stack spacing={3}>
            <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>Monthly Budget Impact</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography>
                  Monthly Income: {formatCurrency(yearlyIncome / 12)}
                </Typography>
                <Typography>
                  Monthly Mortgage: {formatCurrency(stats.monthlyPayment)}
                </Typography>
                <Typography>
                  Housing Cost Ratio: {formatPercent(stats.affordabilityRatio)}
                </Typography>
                <Alert severity={affordabilityStatus.color as 'success' | 'warning' | 'error'}>
                  Affordability Status: {affordabilityStatus.text}
                </Alert>
              </Box>
            </Paper>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Payment Breakdown</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={yearlyData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <RechartsTooltip />
                    <Area
                      type="monotone"
                      dataKey="interest"
                      stackId="1"
                      stroke="#FF8042"
                      fill="#FF8042"
                      name="Interest"
                    />
                    <Area
                      type="monotone"
                      dataKey="principal"
                      stackId="1"
                      stroke="#0088FE"
                      fill="#0088FE"
                      name="Principal"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Stack>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Stack spacing={3}>
            <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>Property Value vs. Mortgage Balance</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={yearlyData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="propertyValue"
                      stroke="#82ca9d"
                      name="Property Value"
                    />
                    <Line
                      type="monotone"
                      dataKey="remainingBalance"
                      stroke="#8884d8"
                      name="Mortgage Balance"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Net Equity Growth</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={yearlyData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <RechartsTooltip />
                    <Area
                      type="monotone"
                      dataKey="netEquity"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      name="Net Equity"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Stack>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
            <Box flex={1}>
              <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>Risk Metrics</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Debt-to-Income Ratio
                      <Tooltip title="Total mortgage amount divided by yearly income. Lower is better.">
                        <InfoIcon sx={{ ml: 1, fontSize: 16 }} />
                      </Tooltip>
                    </Typography>
                    <Typography>
                      {formatPercent(stats.debtToIncomeRatio)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Housing Cost Ratio
                      <Tooltip title="Monthly mortgage payment as percentage of monthly income. Should be under 28%.">
                        <InfoIcon sx={{ ml: 1, fontSize: 16 }} />
                      </Tooltip>
                    </Typography>
                    <Typography>
                      {formatPercent(stats.affordabilityRatio)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Break-even Point
                      <Tooltip title="Year when accumulated equity exceeds total payments made.">
                        <InfoIcon sx={{ ml: 1, fontSize: 16 }} />
                      </Tooltip>
                    </Typography>
                    <Typography>
                      Year {stats.breakEvenYear}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>
          </Stack>
        </TabPanel>
      </Box>
    </Modal>
  );
}

function OptionSection({ 
  title, 
  options, 
  selected, 
  onChange 
}: { 
  title: string;
  options: Option[];
  selected: string;
  onChange: (value: string) => void;
}) {
  return (
    <FormControl component="fieldset" sx={{ width: '100%' }}>
      <FormLabel component="legend" sx={{ color: colors.textDark, fontSize: '1.2rem', mb: 2 }}>
        {title}
      </FormLabel>
      <RadioGroup value={selected} onChange={(e) => onChange(e.target.value)}>
        {options.map((option) => (
          <Paper
            key={option.id}
            elevation={selected === option.id ? 3 : 1}
            sx={{
              mb: 2,
              p: 2,
              border: selected === option.id ? `2px solid ${colors.yellowPrimary}` : '2px solid transparent',
              transition: 'all 0.3s ease',
              '&:hover': {
                borderColor: colors.yellowLight,
              },
            }}
          >
            <FormControlLabel
              value={option.id}
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {option.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {option.description}
                  </Typography>
                </Box>
              }
              sx={{ width: '100%' }}
            />
          </Paper>
        ))}
      </RadioGroup>
    </FormControl>
  );
}

interface HouseOptionSectionProps {
  title: string;
  options: HouseOption[];
  selected: string;
  selectedYear: Year;
  onChange: (value: string) => void;
}

function HouseOptionSection({ 
  title, 
  options, 
  selected, 
  selectedYear,
  onChange 
}: HouseOptionSectionProps) {
  const formatCurrency = (amount: number) => 
    new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(amount);

  const getAdjustedPrice = (basePrice: number, year: Year) => {
    const priceMultiplier: PriceMultiplier = {
      1990: 0.25,
      2000: 0.45,
      2024: 1.0,
    };
    return basePrice * priceMultiplier[year];
  };

  return (
    <FormControl component="fieldset" sx={{ width: '100%' }}>
      <FormLabel component="legend" sx={{ color: colors.textDark, fontSize: '1.2rem', mb: 2 }}>
        {title}
      </FormLabel>
      <RadioGroup value={selected} onChange={(e) => onChange(e.target.value)}>
        <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
          {options.map((option) => (
            <Paper
              key={option.id}
              elevation={selected === option.id ? 3 : 1}
              sx={{
                border: selected === option.id ? `2px solid ${colors.yellowPrimary}` : '2px solid transparent',
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: colors.yellowLight,
                },
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{
                  height: 200,
                  width: '100%',
                  backgroundColor: '#e0e0e0',
                  backgroundImage: `url(${option.imageUrl})`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                }}
              >
                <Box
                  sx={{
                    height: '100%',
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'flex-end',
                    p: 2,
                  }}
                >
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                    {option.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'white' }}>
                    {option.description}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          ))}
        </Box>
      </RadioGroup>
    </FormControl>
  );
}

function PersonCard({ person }: { person: Person }) {
  const yearlyIncome = person.monthlyIncome * 12;
  const debtToIncomeRatio = (person.monthlyDebts / person.monthlyIncome * 100).toFixed(1);
  
  return (
    <Card 
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        '&:hover': {
          boxShadow: 6,
          transform: 'translateY(-4px)',
          transition: 'all 0.2s ease-in-out',
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h5" component="h2" gutterBottom color={colors.textDark}>
          {person.name}
        </Typography>
        
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          {person.age} years old ({person.yearOfReference})
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          {person.description}
        </Typography>

        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Monthly Income
            </Typography>
            <Typography variant="h6" color={colors.textDark}>
              {formatCurrency(person.monthlyIncome)}
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Yearly Income
            </Typography>
            <Typography variant="h6" color={colors.textDark}>
              {formatCurrency(yearlyIncome)}
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Total Wealth
            </Typography>
            <Typography variant="h6" color={colors.textDark}>
              {formatCurrency(person.wealth)}
            </Typography>
          </Box>

          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip 
              label={`Credit Score: ${person.creditScore}`}
              color={person.creditScore >= 740 ? "success" : person.creditScore >= 670 ? "warning" : "error"}
            />
            <Chip 
              label={`DTI: ${debtToIncomeRatio}%`}
              color={Number(debtToIncomeRatio) <= 36 ? "success" : Number(debtToIncomeRatio) <= 43 ? "warning" : "error"}
            />
            {person.hasStudentDebt && (
              <Chip label="Student Debt" color="default" />
            )}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

const ScenarioPage: React.FC = () => {
  const [selectedPerson, setSelectedPerson] = useState<string>('');
  const [selectedHouse, setSelectedHouse] = useState<string>('');
  const [selectedBank, setSelectedBank] = useState<string>('');
  const [propertyType, setPropertyType] = useState<'owner' | 'rental'>('owner');
  const [showCostBreakdown, setShowCostBreakdown] = useState(false);
  const navigate = useNavigate();

  // Filter people, houses, and banks based on the selected year
  const selectedPersonData = useMemo(() => {
    return people.find(p => p.id.toString() === selectedPerson);
  }, [selectedPerson]);

  const yearOfReference = selectedPersonData?.yearOfReference || 2024;

  const availableHouses = useMemo(() => {
    return houses.filter(house => 
      house.availableFrom <= yearOfReference && 
      house.availableTo >= yearOfReference
    );
  }, [yearOfReference]);

  const availableBanks = useMemo(() => {
    return bankOptions.map(bank => ({
      ...bank,
      currentRate: bank.interestRates[yearOfReference as keyof typeof bank.interestRates] || bank.interestRates[2024]
    }));
  }, [yearOfReference]);

  const handleShowCosts = () => {
    if (selectedPerson && selectedHouse && selectedBank) {
      setShowCostBreakdown(true);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Create Your Housing Scenario
      </Typography>
      
      <Box sx={{ mb: 4 }}>
        <Box sx={{ 
          mb: 3, 
          p: 3, 
          background: `linear-gradient(135deg, ${colors.yellowLight} 0%, ${colors.yellowPrimary} 100%)`,
          borderRadius: 2,
          boxShadow: 1
        }}>
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: colors.textDark }}>
            👤 Select a Person Profile
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Choose the profile that matches your financial situation
          </Typography>
        </Box>
        <Stack spacing={2}>
          {people.map((person) => (
            <Card 
              key={person.id}
              sx={{ 
                cursor: 'pointer',
                border: selectedPerson === person.id.toString() ? `2px solid ${colors.yellowPrimary}` : 'none',
                width: '100%',
                maxWidth: '600px',
                mx: 'auto'
              }}
              onClick={() => setSelectedPerson(person.id.toString())}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ mb: 1 }}>{person.name}</Typography>
                    <Typography color="textSecondary" gutterBottom>
                      {person.yearOfReference}
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {person.description}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1} sx={{ ml: 2 }}>
                    <Chip 
                      label={`€${Math.round(person.monthlyIncome).toLocaleString()} /month`}
                      size="small"
                    />
                    <Chip 
                      label={`${person.age} years old`}
                      size="small"
                    />
                  </Stack>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Box>

      {selectedPerson && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ 
            mb: 3, 
            p: 3, 
            background: `linear-gradient(135deg, ${colors.yellowLight} 0%, ${colors.yellowPrimary} 100%)`,
            borderRadius: 2,
            boxShadow: 1
          }}>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: colors.textDark }}>
              🏠 Select a House
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Choose from properties available in {yearOfReference}
            </Typography>
          </Box>
          <Stack spacing={2}>
            {availableHouses.map((house) => (
              <Card 
                key={house.id}
                sx={{ 
                  cursor: 'pointer',
                  border: selectedHouse === house.id.toString() ? `2px solid ${colors.yellowPrimary}` : 'none',
                  width: '100%',
                  maxWidth: '600px',
                  mx: 'auto'
                }}
                onClick={() => setSelectedHouse(house.id.toString())}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ mb: 1 }}>{house.name}</Typography>
                      <Typography color="textSecondary" gutterBottom>
                        Built in {house.yearBuilt}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {house.description}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1} sx={{ ml: 2 }}>
                      <Chip 
                        label={formatCurrency(house.basePrice)}
                        size="small"
                      />
                      <Chip 
                        label={`${house.squareMeters}m²`}
                        size="small"
                      />
                    </Stack>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Box>
      )}

      {selectedHouse && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ 
            mb: 3, 
            p: 3, 
            background: `linear-gradient(135deg, ${colors.yellowLight} 0%, ${colors.yellowPrimary} 100%)`,
            borderRadius: 2,
            boxShadow: 1
          }}>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: colors.textDark }}>
              🏦 Select a Bank
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Compare mortgage rates for {yearOfReference}
            </Typography>
          </Box>
          <Grid container spacing={2}>
            {availableBanks.map((bank) => (
              <Grid item component="div" xs={12} sm={6} md={4} key={bank.id}>
                <Card 
                  sx={{ 
                    cursor: 'pointer',
                    border: selectedBank === bank.id ? `2px solid ${colors.yellowPrimary}` : 'none',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column'
                  }}
                  onClick={() => setSelectedBank(bank.id)}
                >
                  <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="h6" sx={{ mb: 1 }}>{bank.title}</Typography>
                    <Typography variant="body2" paragraph sx={{ flexGrow: 1 }}>
                      {bank.description}
                    </Typography>
                    <Stack direction="row" spacing={1} sx={{ mt: 'auto' }}>
                      <Chip 
                        label={`${bank.currentRate.toFixed(1)}% interest`}
                        size="small"
                      />
                      <Chip 
                        label={`${(bank.loanToValue * 100).toFixed(0)}% LTV`}
                        size="small"
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {selectedBank && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ 
            mb: 3, 
            p: 3, 
            background: `linear-gradient(135deg, ${colors.yellowLight} 0%, ${colors.yellowPrimary} 100%)`,
            borderRadius: 2,
            boxShadow: 1
          }}>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: colors.textDark }}>
              🏘️ Property Type
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Will you live in the property or rent it out?
            </Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid item component="div" xs={12} sm={6}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  border: propertyType === 'owner' ? `2px solid ${colors.yellowPrimary}` : 'none'
                }}
                onClick={() => setPropertyType('owner')}
              >
                <CardContent>
                  <Typography variant="h6">Owner Occupied</Typography>
                  <Typography variant="body2" paragraph>
                    Live in the property yourself. Benefit from mortgage interest deduction and no rental income tax.
                  </Typography>
                  <Stack direction="row" spacing={1}>
                    <Chip label="Tax Deductible Interest" size="small" color="success" />
                    <Chip label="No Rental Tax" size="small" color="success" />
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
            <Grid item component="div" xs={12} sm={6}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  border: propertyType === 'rental' ? `2px solid ${colors.yellowPrimary}` : 'none'
                }}
                onClick={() => setPropertyType('rental')}
              >
                <CardContent>
                  <Typography variant="h6">Rental Property</Typography>
                  <Typography variant="body2" paragraph>
                    Rent out the property for income. Generate rental yield but pay tax on rental income.
                  </Typography>
                  <Stack direction="row" spacing={1}>
                    <Chip label="Rental Income" size="small" color="primary" />
                    <Chip label="Taxable Income" size="small" color="warning" />
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {selectedPerson && selectedHouse && selectedBank && (
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
          <Button 
            variant="contained" 
            color="primary"
            size="large"
            onClick={handleShowCosts}
          >
            Calculate Costs
          </Button>
        </Box>
      )}

      {showCostBreakdown && (
        <CostBreakdown
          open={showCostBreakdown}
          onClose={() => setShowCostBreakdown(false)}
          selectedOptions={{
            person: selectedPerson,
            house: selectedHouse,
            bank: selectedBank
          }}
          propertyType={propertyType}
        />
      )}
    </Container>
  );
};

export default ScenarioPage;