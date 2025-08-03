import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  Slider,
  Button,
  Paper,
  Grid as MuiGrid,
  styled,
  Tooltip,
  Divider,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import type { Theme } from '@mui/material/styles';
import type { SxProps } from '@mui/system';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  Area,
  AreaChart,
} from 'recharts';
import { useLandlordCalculator } from '../hooks/useLandlordCalculator';
import InfoIcon from '@mui/icons-material/Info';
import ScenarioPage from './ScenarioPage';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700',
  yellowLight: '#FFF4B8',
  yellowDark: '#FFC000',
  textDark: '#2C2C2C',
};

// Create a properly typed Grid component
const Grid = MuiGrid as React.ComponentType<{
  container?: boolean;
  item?: boolean;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  spacing?: number;
  children?: React.ReactNode;
  sx?: SxProps<Theme>;
}>;

const StyledSlider = styled(Slider)(({ theme }) => ({
  marginTop: theme.spacing(1),
  marginBottom: theme.spacing(3),
}));

const ChartContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  height: '300px',
  marginBottom: theme.spacing(2),
  '& .recharts-wrapper': {
    width: '100% !important',
    height: '100% !important',
  },
}));

const MetricBox = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(2),
  '& > *': {
    borderBottom: `1px solid ${theme.palette.divider}`,
    paddingBottom: theme.spacing(2),
    '&:last-child': {
      borderBottom: 'none',
    },
  },
}));

const MetricTooltip = styled(({ title, children, ...props }: { 
  title: string; 
  children: React.ReactNode;
  [key: string]: any; 
}) => (
  <Tooltip title={title} arrow placement="top" {...props}>
    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
      {children}
      <InfoIcon sx={{ fontSize: 16, opacity: 0.7 }} />
    </Box>
  </Tooltip>
))(() => ({
  cursor: 'help',
}));

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('nl-NL', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatPercentage = (value: number) => {
  return new Intl.NumberFormat('nl-NL', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
};

const RiskIndicator: React.FC<{ score: number; label: string }> = ({ score, label }) => (
  <Box sx={{ width: '100%', mb: 2 }}>
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
      <Typography variant="body2">{label}</Typography>
      <Typography variant="body2" color={score > 66 ? 'error' : score > 33 ? 'warning.main' : 'success.main'}>
        {score.toFixed(1)}%
      </Typography>
    </Box>
    <LinearProgress
      variant="determinate"
      value={score}
      color={score > 66 ? 'error' : score > 33 ? 'warning' : 'success'}
      sx={{ height: 8, borderRadius: 4 }}
    />
  </Box>
);

function LandlordPage() {
  const [calculatorType, setCalculatorType] = useState<'scenario' | 'custom'>('scenario');
  const { inputs, results, updateInput, calculate } = useLandlordCalculator();

  // Calculate initial results when component mounts
  useEffect(() => {
    calculate();
  }, [calculate]);

  const handleCalculatorTypeChange = (
    event: React.MouseEvent<HTMLElement>,
    newType: 'scenario' | 'custom',
  ) => {
    if (newType !== null) {
      setCalculatorType(newType);
    }
  };

  const handleSliderChange = (name: keyof typeof inputs) => (_event: Event, value: number | number[]) => {
    updateInput(name, value as number);
  };

  const [focusedFields, setFocusedFields] = useState<{ [key: string]: boolean }>({});

  const handleInputChange = (name: keyof typeof inputs) => (event: React.ChangeEvent<HTMLInputElement>) => {
    updateInput(name, Number(event.target.value));
  };

  const handleInputFocus = (name: string) => () => {
    setFocusedFields(prev => ({ ...prev, [name]: true }));
  };

  const handleInputBlur = (name: string) => () => {
    setFocusedFields(prev => ({ ...prev, [name]: false }));
  };

  const handleLocationChange = (event: SelectChangeEvent) => {
    const value = event.target.value as 'central' | 'suburban' | 'remote';
    updateInput('location', value);
  };

  if (calculatorType === 'scenario') {
    return (
      <Container maxWidth="xl">
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
          <ToggleButtonGroup
            value={calculatorType}
            exclusive
            onChange={handleCalculatorTypeChange}
            aria-label="calculator type"
            sx={{ mb: 2 }}
          >
            <ToggleButton 
              value="scenario" 
              aria-label="scenario calculator"
              sx={{
                '&.Mui-selected': {
                  backgroundColor: colors.yellowPrimary,
                  '&:hover': {
                    backgroundColor: colors.yellowDark,
                  },
                },
              }}
            >
              Scenario Calculator
            </ToggleButton>
            <ToggleButton 
              value="custom" 
              aria-label="custom calculator"
              sx={{
                '&.Mui-selected': {
                  backgroundColor: colors.yellowPrimary,
                  '&:hover': {
                    backgroundColor: colors.yellowDark,
                  },
                },
              }}
            >
              Custom Calculator
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <ScenarioPage />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom align="center" sx={{ color: colors.textDark }}>
        Landlord Investment Calculator
      </Typography>

      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
        <ToggleButtonGroup
          value={calculatorType}
          exclusive
          onChange={handleCalculatorTypeChange}
          aria-label="calculator type"
          sx={{ mb: 2 }}
        >
          <ToggleButton 
            value="scenario" 
            aria-label="scenario calculator"
            sx={{
              '&.Mui-selected': {
                backgroundColor: colors.yellowPrimary,
                '&:hover': {
                  backgroundColor: colors.yellowDark,
                },
              },
            }}
          >
            Scenario Calculator
          </ToggleButton>
          <ToggleButton 
            value="custom" 
            aria-label="custom calculator"
            sx={{
              '&.Mui-selected': {
                backgroundColor: colors.yellowPrimary,
                '&:hover': {
                  backgroundColor: colors.yellowDark,
                },
              },
            }}
          >
            Custom Calculator
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Investment Parameters
            </Typography>

            <TextField
              fullWidth
              label="Purchase Price (€)"
              type="number"
              value={focusedFields['purchasePrice'] ? '' : inputs.purchasePrice}
              onChange={handleInputChange('purchasePrice')}
              onFocus={handleInputFocus('purchasePrice')}
              onBlur={handleInputBlur('purchasePrice')}
              margin="normal"
            />

            <FormControl fullWidth margin="normal">
              <InputLabel>Location</InputLabel>
              <Select
                value={inputs.location}
                onChange={handleLocationChange}
                label="Location"
              >
                <MenuItem value="central">Central (e.g. Amsterdam)</MenuItem>
                <MenuItem value="suburban">Suburban (e.g. Amstelveen)</MenuItem>
                <MenuItem value="remote">Remote (e.g. Kerkrade)</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Point System Rent (€)"
              type="number"
              value={focusedFields['pointSystemRent'] ? '' : inputs.pointSystemRent}
              onChange={handleInputChange('pointSystemRent')}
              onFocus={handleInputFocus('pointSystemRent')}
              onBlur={handleInputBlur('pointSystemRent')}
              margin="normal"
              helperText="Maximum rent allowed by the point system"
            />

            <TextField
              fullWidth
              label="Market Rent (€)"
              type="number"
              value={focusedFields['monthlyRent'] ? '' : inputs.monthlyRent}
              onChange={handleInputChange('monthlyRent')}
              onFocus={handleInputFocus('monthlyRent')}
              onBlur={handleInputBlur('monthlyRent')}
              margin="normal"
              helperText="Actual market rent in the area"
            />

            <Typography gutterBottom>
              Down Payment: {inputs.downPayment}% ({formatCurrency(inputs.purchasePrice * (inputs.downPayment / 100))})
            </Typography>
            <StyledSlider
              value={inputs.downPayment}
              onChange={handleSliderChange('downPayment')}
              min={0}
              max={100}
              step={1}
              marks={[
                { value: 0, label: '0%' },
                { value: 20, label: '20%' },
                { value: 40, label: '40%' },
                { value: 60, label: '60%' },
                { value: 80, label: '80%' },
                { value: 100, label: '100%' },
              ]}
            />

            <Typography gutterBottom>
              Interest Rate: {inputs.interestRate}% ({formatCurrency((inputs.purchasePrice * (1 - inputs.downPayment / 100)) * (inputs.interestRate / 100))} per year)
            </Typography>
            <StyledSlider
              value={inputs.interestRate}
              onChange={handleSliderChange('interestRate')}
              min={0}
              max={10}
              step={0.05}
              marks={[
                { value: 0, label: '0%' },
                { value: 2.5, label: '2.5%' },
                { value: 5, label: '5%' },
                { value: 7.5, label: '7.5%' },
                { value: 10, label: '10%' },
              ]}
            />

            <Typography gutterBottom>
              Loan Term: {inputs.loanTerm} years
            </Typography>
            <StyledSlider
              value={inputs.loanTerm}
              onChange={handleSliderChange('loanTerm')}
              min={5}
              max={40}
              step={1}
              marks={[
                { value: 5, label: '5y' },
                { value: 15, label: '15y' },
                { value: 25, label: '25y' },
                { value: 35, label: '35y' },
              ]}
            />

            <Typography gutterBottom>
              Property Tax Rate: {inputs.propertyTax}% ({formatCurrency(inputs.purchasePrice * (inputs.propertyTax / 100))} per year)
            </Typography>
            <StyledSlider
              value={inputs.propertyTax}
              onChange={handleSliderChange('propertyTax')}
              min={0}
              max={2}
              step={0.01}
              marks={[
                { value: 0, label: '0%' },
                { value: 0.5, label: '0.5%' },
                { value: 1, label: '1%' },
                { value: 1.5, label: '1.5%' },
                { value: 2, label: '2%' },
              ]}
            />

            <Typography gutterBottom>
              Maintenance & Management: {inputs.maintenanceRate}% ({formatCurrency(inputs.purchasePrice * (inputs.maintenanceRate / 100))} per year)
            </Typography>
            <StyledSlider
              value={inputs.maintenanceRate}
              onChange={handleSliderChange('maintenanceRate')}
              min={0}
              max={20}
              step={0.1}
              marks={[
                { value: 0, label: '0%' },
                { value: 5, label: '5%' },
                { value: 10, label: '10%' },
                { value: 15, label: '15%' },
                { value: 20, label: '20%' },
              ]}
            />

            <Typography gutterBottom>
              Vacancy Rate: {inputs.vacancyRate}% ({formatCurrency(inputs.monthlyRent * 12 * (inputs.vacancyRate / 100))} lost per year)
            </Typography>
            <StyledSlider
              value={inputs.vacancyRate}
              onChange={handleSliderChange('vacancyRate')}
              min={0}
              max={20}
              step={0.1}
              marks={[
                { value: 0, label: '0%' },
                { value: 5, label: '5%' },
                { value: 10, label: '10%' },
                { value: 15, label: '15%' },
                { value: 20, label: '20%' },
              ]}
            />

            <Typography gutterBottom>
              Insurance Rate: {inputs.insuranceRate}% ({formatCurrency(inputs.purchasePrice * (inputs.insuranceRate / 100))} per year)
            </Typography>
            <StyledSlider
              value={inputs.insuranceRate}
              onChange={handleSliderChange('insuranceRate')}
              min={0}
              max={2}
              step={0.01}
              marks={[
                { value: 0, label: '0%' },
                { value: 0.5, label: '0.5%' },
                { value: 1, label: '1%' },
                { value: 1.5, label: '1.5%' },
                { value: 2, label: '2%' },
              ]}
            />

            <Typography gutterBottom>
              Utility Rate: {inputs.utilityRate}% ({formatCurrency(inputs.monthlyRent * 12 * (inputs.utilityRate / 100))} per year)
            </Typography>
            <StyledSlider
              value={inputs.utilityRate}
              onChange={handleSliderChange('utilityRate')}
              min={0}
              max={10}
              step={0.1}
              marks={[
                { value: 0, label: '0%' },
                { value: 2.5, label: '2.5%' },
                { value: 5, label: '5%' },
                { value: 7.5, label: '7.5%' },
                { value: 10, label: '10%' },
              ]}
            />

            <Typography gutterBottom>
              Annual Appreciation Rate: {inputs.appreciationRate}% ({formatCurrency(inputs.purchasePrice * (inputs.appreciationRate / 100))} per year)
            </Typography>
            <StyledSlider
              value={inputs.appreciationRate}
              onChange={handleSliderChange('appreciationRate')}
              min={0}
              max={10}
              step={0.01}
              marks={[
                { value: 0, label: '0%' },
                { value: 2.5, label: '2.5%' },
                { value: 5, label: '5%' },
                { value: 7.5, label: '7.5%' },
                { value: 10, label: '10%' },
              ]}
            />

            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={calculate}
              sx={{ mt: 3 }}
            >
              Calculate Investment
            </Button>
          </Paper>
        </Grid>

        {results && (
          <Grid item xs={12} md={8}>
            {/* Monthly Income & Expenses */}
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Monthly Income & Expenses
              </Typography>
              <Grid container spacing={4}>
                <Grid item xs={12} md={6}>
                  <Box component="div">
                    <MetricTooltip title="Total monthly rental income before expenses">
                      <Typography variant="subtitle1" color="primary">
                        Gross Income: {formatCurrency(results.monthlyGrossIncome)}
                      </Typography>
                    </MetricTooltip>
                    <Box sx={{ pl: 2, mt: 1 }}>
                      <Typography color="error">
                        Vacancy Loss: -{formatCurrency(results.monthlyVacancyLoss)}
                      </Typography>
                    </Box>
                    <Divider sx={{ my: 2 }} />
                    <MetricTooltip title="Monthly income after all expenses and mortgage">
                      <Typography variant="subtitle1" color="success.main">
                        Net Income: {formatCurrency(results.monthlyNetIncome)}
                      </Typography>
                    </MetricTooltip>
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box component="div">
                    <Typography variant="subtitle1">Monthly Expenses</Typography>
                    <Box sx={{ pl: 2 }}>
                      <Typography>Mortgage: {formatCurrency(results.monthlyMortgage)}</Typography>
                      <Typography>Property Tax: {formatCurrency(results.monthlyPropertyTax)}</Typography>
                      <Typography>Maintenance: {formatCurrency(results.monthlyMaintenance)}</Typography>
                      <Typography>Insurance: {formatCurrency(results.monthlyInsurance)}</Typography>
                      <Typography>Utilities: {formatCurrency(results.monthlyUtilities)}</Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Paper>

            {/* Investment Metrics */}
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Investment Metrics
              </Typography>
              {results && (
                <MetricBox>
                  <MetricTooltip title="Annual cash flow divided by total investment">
                    <Typography>Cash on Cash Return: {formatPercentage(results.cashOnCashReturn)}</Typography>
                  </MetricTooltip>
                  <MetricTooltip title="Net operating income divided by property value">
                    <Typography>Cap Rate: {formatPercentage(results.capRate)}</Typography>
                  </MetricTooltip>
                  <MetricTooltip title="Property price divided by annual gross income">
                    <Typography>Gross Rent Multiplier: {results.grossRentMultiplier.toFixed(2)}x</Typography>
                  </MetricTooltip>
                  <MetricTooltip title="Net operating income divided by debt service">
                    <Typography>Debt Coverage Ratio: {results.debtServiceCoverageRatio.toFixed(2)}</Typography>
                  </MetricTooltip>
                  <MetricTooltip title="Required occupancy rate to cover expenses">
                    <Typography>Break-even Occupancy: {formatPercentage(results.breakEvenOccupancy)}</Typography>
                  </MetricTooltip>
                  <MetricTooltip title="Months needed to recover initial investment">
                    <Typography>Break-even Period: {results.riskMetrics.breakEvenMonths} months</Typography>
                  </MetricTooltip>
                </MetricBox>
              )}
            </Paper>

            {/* Risk Analysis */}
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Risk Analysis
              </Typography>
              <RiskIndicator score={results.riskMetrics.overallRiskScore} label="Overall Risk" />
              <RiskIndicator score={results.riskMetrics.cashFlowRiskScore} label="Cash Flow Risk" />
              <RiskIndicator score={results.riskMetrics.vacancyRiskScore} label="Vacancy Risk" />
              <RiskIndicator score={results.riskMetrics.appreciationRiskScore} label="Appreciation Risk" />
            </Paper>

            {/* Charts */}
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                30-Year Projection
              </Typography>
              
              <Typography variant="subtitle1" gutterBottom>Property Value & Equity Growth</Typography>
              <ChartContainer>
                <ResponsiveContainer>
                  <AreaChart data={results?.yearlyData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="year" 
                      label={{ value: 'Year', position: 'bottom', offset: -10 }}
                    />
                    <YAxis 
                      label={{ value: 'Value (€)', angle: -90, position: 'insideLeft', offset: 10 }}
                      tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                    />
                    <RechartsTooltip 
                      formatter={(value: number) => formatCurrency(value)}
                      labelFormatter={(label) => `Year ${label}`}
                    />
                    <Legend verticalAlign="top" height={36} />
                    <Area 
                      type="monotone" 
                      dataKey="propertyValue" 
                      name="Property Value" 
                      fill="#8884d8" 
                      stroke="#8884d8" 
                      fillOpacity={0.3}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="equity" 
                      name="Equity" 
                      fill="#82ca9d" 
                      stroke="#82ca9d" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartContainer>

              <Typography variant="subtitle1" gutterBottom sx={{ mt: 4 }}>Annual Cash Flow & NOI</Typography>
              <ChartContainer>
                <ResponsiveContainer>
                  <LineChart data={results?.yearlyData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="year" 
                      label={{ value: 'Year', position: 'bottom', offset: -10 }}
                    />
                    <YAxis 
                      label={{ value: 'Amount (€)', angle: -90, position: 'insideLeft', offset: 10 }}
                      tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                    />
                    <RechartsTooltip 
                      formatter={(value: number) => formatCurrency(value)}
                      labelFormatter={(label) => `Year ${label}`}
                    />
                    <Legend verticalAlign="top" height={36} />
                    <Line 
                      type="monotone" 
                      dataKey="cashFlow" 
                      name="Cash Flow" 
                      stroke="#2ecc71" 
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="netOperatingIncome" 
                      name="NOI" 
                      stroke="#3498db" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>

              <Typography variant="subtitle1" gutterBottom sx={{ mt: 4 }}>Operating Metrics</Typography>
              <ChartContainer>
                <ResponsiveContainer>
                  <LineChart data={results?.yearlyData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="year" 
                      label={{ value: 'Year', position: 'bottom', offset: -10 }}
                    />
                    <YAxis 
                      label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', offset: 10 }}
                      domain={[0, 100]}
                    />
                    <RechartsTooltip 
                      formatter={(value: number) => `${value.toFixed(1)}%`}
                      labelFormatter={(label) => `Year ${label}`}
                    />
                    <Legend verticalAlign="top" height={36} />
                    <Line 
                      type="monotone" 
                      dataKey="operatingExpenseRatio" 
                      name="Expense Ratio" 
                      stroke="#e74c3c" 
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="debtCoverageRatio" 
                      name="DSCR" 
                      stroke="#f39c12" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>
            </Paper>

            {/* Yearly Breakdown Table */}
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Yearly Breakdown
              </Typography>
              <Box sx={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #eee' }}>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Year</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Property Value</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Equity</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Cash Flow</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>ROI</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>DSCR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.yearlyData.map((year, index) => (
                      <tr key={year.year} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '8px' }}>{year.year}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>{formatCurrency(year.propertyValue)}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>{formatCurrency(year.equity)}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>{formatCurrency(year.cashFlow)}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>{formatPercentage(year.roi)}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>{year.debtCoverageRatio.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            </Paper>

            {/* Location Metrics */}
            <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Location Metrics
              </Typography>
              {results && (
                <>
                  <MetricBox>
                    <MetricTooltip title="Ratio of property price to annual rent based on point system">
                      <Typography>Price to Point-Rent Ratio: {results.locationMetrics.priceToPointRentRatio.toFixed(1)}x</Typography>
                    </MetricTooltip>
                    <MetricTooltip title="How much higher the market rent is compared to point system rent">
                      <Typography>Market Rent Premium: {formatPercentage(results.locationMetrics.marketRentPremium)}</Typography>
                    </MetricTooltip>
                    <MetricTooltip title="Return on investment compared to market average">
                      <Typography>Relative ROI: {formatPercentage(results.locationMetrics.relativeROI)}</Typography>
                    </MetricTooltip>
                    <MetricTooltip title="Overall profitability score for this location">
                      <Typography>Location Profitability Score: {results.locationMetrics.locationProfitabilityScore.toFixed(1)}</Typography>
                    </MetricTooltip>
                    <MetricTooltip title="Impact of the point system on potential returns">
                      <Typography>Point System Impact: {results.locationMetrics.pointSystemImpact.toFixed(1)}</Typography>
                    </MetricTooltip>
                  </MetricBox>

                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Point System Impact
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={results.locationMetrics.pointSystemImpact}
                      sx={{
                        height: 10,
                        borderRadius: 5,
                        backgroundColor: '#e0e0e0',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: results.locationMetrics.pointSystemImpact > 70 ? '#f44336' :
                                         results.locationMetrics.pointSystemImpact > 40 ? '#ff9800' : '#4caf50',
                        },
                      }}
                    />
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      {results.locationMetrics.pointSystemImpact > 70 ? 'High impact - Point system significantly limits profitability' :
                       results.locationMetrics.pointSystemImpact > 40 ? 'Medium impact - Point system moderately affects returns' :
                       'Low impact - Point system has minimal effect on returns'}
                    </Typography>
                  </Box>
                </>
              )}
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}

export default LandlordPage; 