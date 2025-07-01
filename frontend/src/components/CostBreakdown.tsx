import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Alert,
  Tabs,
  Tab,
  Tooltip,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import { MortgageStats, YearlyData, PropertyType } from '../types';
import { formatCurrency, formatPercent } from '../utils/formatters';

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
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

interface CostBreakdownProps {
  stats: MortgageStats;
  yearlyData: YearlyData[];
  propertyType: PropertyType;
  yearlyIncome: number;
}

export function CostBreakdown({ stats, yearlyData, propertyType, yearlyIncome }: CostBreakdownProps) {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Prepare data for pie chart based on property type
  const getPieData = () => {
    if (propertyType === 'owner') {
      return [
        { name: 'Principal', value: stats.totalCost - stats.totalInterest },
        { name: 'Interest', value: stats.totalInterest },
        { name: 'Property Tax', value: stats.propertyTax * 20 }, // 20 years
        { name: 'Maintenance', value: stats.maintenanceCosts * 20 },
        { name: 'Insurance', value: stats.insuranceCosts * 20 },
      ];
    } else {
      return [
        { name: 'Mortgage', value: stats.yearlyPayment },
        { name: 'Property Tax', value: stats.propertyTax },
        { name: 'Maintenance', value: stats.maintenanceCosts },
        { name: 'Insurance', value: stats.insuranceCosts },
        { name: 'Property Management', value: stats.propertyManagementFee! },
      ];
    }
  };

  const pieData = getPieData();

  const renderPieLabel = (entry: any) => {
    return `${entry.name}: ${formatPercent(entry.value / pieData.reduce((sum, item) => sum + item.value, 0))}`;
  };

  const getAffordabilityStatus = () => {
    if (propertyType === 'owner') {
      if (stats.affordabilityRatio > 0.33) {
        return { color: 'error', text: 'Housing costs are too high for your income' };
      } else if (stats.affordabilityRatio > 0.28) {
        return { color: 'warning', text: 'Housing costs are slightly high for your income' };
      } else {
        return { color: 'success', text: 'Housing costs are within recommended limits' };
      }
    } else {
      if (stats.cashOnCashReturn! < 4) {
        return { color: 'error', text: 'Poor cash-on-cash return' };
      } else if (stats.cashOnCashReturn! < 6) {
        return { color: 'warning', text: 'Moderate cash-on-cash return' };
      } else {
        return { color: 'success', text: 'Good cash-on-cash return' };
      }
    }
  };

  const affordabilityStatus = getAffordabilityStatus();

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Monthly Details" />
          <Tab label="Long-term Projection" />
          <Tab label="Risk Analysis" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
          <Paper elevation={2} sx={{ p: 2, mb: 2, flex: 1 }}>
            <Typography variant="h6" gutterBottom>Key Figures</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography>Monthly Payment: {formatCurrency(stats.monthlyPayment)}</Typography>
              <Typography>Total Cost (20 years): {formatCurrency(stats.totalCost)}</Typography>
              {propertyType === 'owner' ? (
                <>
                  <Typography>Total Interest: {formatCurrency(stats.totalInterest)}</Typography>
                  <Typography>Tax Savings (20 years): {formatCurrency(stats.taxSavings!)}</Typography>
                </>
              ) : (
                <>
                  <Typography>Monthly Rental Income: {formatCurrency(stats.rentalIncome! / 12)}</Typography>
                  <Typography>Net Operating Income: {formatCurrency(stats.netOperatingIncome!)}</Typography>
                  <Typography>Cash Flow: {formatCurrency(stats.netOperatingIncome! - stats.yearlyPayment)}</Typography>
                  <Typography>Net Rental Yield: {formatPercent(stats.netRentalYield!)}</Typography>
                </>
              )}
              <Typography>Property Tax (yearly): {formatCurrency(stats.propertyTax)}</Typography>
              <Typography>Maintenance (yearly): {formatCurrency(stats.maintenanceCosts)}</Typography>
              <Typography>Insurance (yearly): {formatCurrency(stats.insuranceCosts)}</Typography>
              {propertyType === 'rental' && (
                <>
                  <Typography>Vacancy Rate: {formatPercent(stats.vacancyRate!)}</Typography>
                  <Typography>Property Management: {formatCurrency(stats.propertyManagementFee!)}</Typography>
                  <Typography>Cap Rate: {formatPercent(stats.capitalizationRate!)}</Typography>
                </>
              )}
            </Box>
          </Paper>

          <Paper elevation={2} sx={{ p: 2, mb: 2, flex: 1 }}>
            <Typography variant="h6" gutterBottom>Cost Distribution</Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    fill="#8884d8"
                    paddingAngle={5}
                    dataKey="value"
                    label={renderPieLabel}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Monthly Budget Impact</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography>
                Monthly Income: {formatCurrency(yearlyIncome / 12)}
              </Typography>
              <Typography>
                Monthly Payment: {formatCurrency(stats.monthlyPayment)}
              </Typography>
              {propertyType === 'owner' ? (
                <Typography>
                  Housing Cost Ratio: {formatPercent(stats.affordabilityRatio)}
                </Typography>
              ) : (
                <Typography>
                  Monthly Cash Flow: {formatCurrency((stats.netOperatingIncome! - stats.yearlyPayment) / 12)}
                </Typography>
              )}
              <Alert severity={affordabilityStatus.color as 'success' | 'warning' | 'error'}>
                {affordabilityStatus.text}
              </Alert>
            </Box>
          </Paper>

          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              {propertyType === 'owner' ? 'Payment Breakdown' : 'Income & Expenses'}
            </Typography>
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
                  {propertyType === 'owner' ? (
                    <>
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
                    </>
                  ) : (
                    <>
                      <Area
                        type="monotone"
                        dataKey="rentalIncome"
                        stackId="1"
                        stroke="#82ca9d"
                        fill="#82ca9d"
                        name="Rental Income"
                      />
                      <Area
                        type="monotone"
                        dataKey="netOperatingIncome"
                        stackId="2"
                        stroke="#8884d8"
                        fill="#8884d8"
                        name="Net Operating Income"
                      />
                      <Area
                        type="monotone"
                        dataKey="cashFlow"
                        stackId="3"
                        stroke="#ffc658"
                        fill="#ffc658"
                        name="Cash Flow"
                      />
                    </>
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Paper elevation={2} sx={{ p: 2 }}>
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
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
          <Paper elevation={2} sx={{ p: 2, flex: 1 }}>
            <Typography variant="h6" gutterBottom>Risk Metrics</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {propertyType === 'owner' ? (
                <>
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
                </>
              ) : (
                <>
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Cash-on-Cash Return
                      <Tooltip title="Annual cash flow divided by total cash invested. Higher is better.">
                        <InfoIcon sx={{ ml: 1, fontSize: 16 }} />
                      </Tooltip>
                    </Typography>
                    <Typography>
                      {formatPercent(stats.cashOnCashReturn!)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Capitalization Rate
                      <Tooltip title="Net operating income divided by property value. Higher indicates better income generation.">
                        <InfoIcon sx={{ ml: 1, fontSize: 16 }} />
                      </Tooltip>
                    </Typography>
                    <Typography>
                      {formatPercent(stats.capitalizationRate!)}
                    </Typography>
                  </Box>
                </>
              )}
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

          <Paper elevation={2} sx={{ p: 2, flex: 1 }}>
            <Typography variant="h6" gutterBottom>Recommendations</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {propertyType === 'owner' ? (
                <>
                  {stats.affordabilityRatio > 0.28 && (
                    <Alert severity="warning">
                      Monthly payments are higher than recommended (28% of income).
                      Consider a smaller loan or longer term.
                    </Alert>
                  )}
                  {stats.debtToIncomeRatio > 3 && (
                    <Alert severity="warning">
                      Total debt is more than 3x yearly income.
                      This might make it difficult to get approved for a mortgage.
                    </Alert>
                  )}
                  {stats.breakEvenYear > 10 && (
                    <Alert severity="info">
                      It will take {stats.breakEvenYear} years to break even.
                      Make sure you plan to stay in the house long enough.
                    </Alert>
                  )}
                  {stats.affordabilityRatio <= 0.28 && 
                   stats.debtToIncomeRatio <= 3 && 
                   stats.breakEvenYear <= 10 && (
                    <Alert severity="success">
                      This appears to be a financially sound investment based on your income and the loan terms.
                    </Alert>
                  )}
                </>
              ) : (
                <>
                  {stats.cashOnCashReturn! < 4 && (
                    <Alert severity="warning">
                      Cash-on-cash return is below 4%.
                      Consider negotiating a better purchase price or finding ways to increase rental income.
                    </Alert>
                  )}
                  {stats.netRentalYield! < 5 && (
                    <Alert severity="warning">
                      Net rental yield is below 5%.
                      This property might not generate sufficient rental income.
                    </Alert>
                  )}
                  {(stats.netOperatingIncome! - stats.yearlyPayment) < 0 && (
                    <Alert severity="error">
                      Negative cash flow!
                      This property will require additional monthly investment.
                    </Alert>
                  )}
                  {stats.cashOnCashReturn! >= 6 && 
                   stats.netRentalYield! >= 5 && 
                   (stats.netOperatingIncome! - stats.yearlyPayment) > 0 && (
                    <Alert severity="success">
                      This property shows good potential as a rental investment with healthy returns.
                    </Alert>
                  )}
                </>
              )}
            </Box>
          </Paper>
        </Box>
      </TabPanel>
    </Box>
  );
} 