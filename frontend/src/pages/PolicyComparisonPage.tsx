import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
} from '@mui/material';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import { useSimulation } from '../contexts/SimulationContext';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700',
  yellowLight: '#FFF4B8',
  yellowDark: '#FFC000',
  textDark: '#2C2C2C',
  white: '#FFFFFF',
  occupied: '#28a745',
  vacant: '#dc3545',
  policy1: '#2196f3',
  policy2: '#f50057',
};

interface ComparisonMetrics {
  avgRent: number;
  totalUnhoused: number;
  avgSatisfaction: number;
  avgRentBurden: number;
  policyMetrics?: {
    total_lvt_collected?: number;
    violations_found?: number;
    improvements_required?: number;
    lvt_rate?: number;
  };
}

interface SimulationState {
  policy: string;
  metrics: ComparisonMetrics | null;
  yearlyData: Array<{
    period: number;
    avgRent: number;
    unhoused: number;
    satisfaction: number;
    rentBurden: number;
  }>;
}

const PolicyComparisonPage = () => {
  const { startSimulation, resetSimulation } = useSimulation();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [simulation1, setSimulation1] = useState<SimulationState>({
    policy: 'none',
    metrics: null,
    yearlyData: [],
  });
  
  const [simulation2, setSimulation2] = useState<SimulationState>({
    policy: 'rent_cap',
    metrics: null,
    yearlyData: [],
  });

  const runComparison = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Make direct API calls instead of using the context
      const response1 = await fetch('http://localhost:8000/simulation/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          initial_households: 100,
          migration_rate: 0.1,
          years: 5,
          policy: simulation1.policy === 'rent_cap' ? 'rent_cap' : 
                 simulation1.policy === 'lvt' ? 'lvt' : 'none',
          lvt_rate: simulation1.policy === 'lvt' ? 0.02 : 0,
        }),
      });

      if (!response1.ok) {
        throw new Error('Failed to run first simulation');
      }

      const result1 = await response1.json();
      
      // Store first simulation results
      setSimulation1(prev => ({
        ...prev,
        metrics: extractMetrics(result1),
        yearlyData: extractYearlyData(result1),
      }));

      // Run second simulation
      const response2 = await fetch('http://localhost:8000/simulation/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          initial_households: 100,
          migration_rate: 0.1,
          years: 5,
          policy: simulation2.policy === 'rent_cap' ? 'rent_cap' : 
                 simulation2.policy === 'lvt' ? 'lvt' : 'none',
          lvt_rate: simulation2.policy === 'lvt' ? 0.02 : 0,
        }),
      });

      if (!response2.ok) {
        throw new Error('Failed to run second simulation');
      }

      const result2 = await response2.json();

      // Store second simulation results
      setSimulation2(prev => ({
        ...prev,
        metrics: extractMetrics(result2),
        yearlyData: extractYearlyData(result2),
      }));

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run comparison');
    } finally {
      setIsLoading(false);
    }
  };

  const extractMetrics = (simulationResult: any): ComparisonMetrics => {
    // Extract and calculate average metrics from the simulation result
    return {
      avgRent: calculateAverage(simulationResult.frames.map((f: any) => f.metrics.average_rent)),
      totalUnhoused: calculateAverage(simulationResult.frames.map((f: any) => f.unhoused_households?.length || 0)),
      avgSatisfaction: calculateAverage(simulationResult.frames.map((f: any) => {
        const satisfiedHouseholds = f.units
          .filter((u: any) => u.household?.satisfaction)
          .map((u: any) => u.household.satisfaction);
        return satisfiedHouseholds.length > 0 
          ? (satisfiedHouseholds.reduce((a: number, b: number) => a + b, 0) / satisfiedHouseholds.length) * 100
          : 0;
      })),
      avgRentBurden: calculateAverage(simulationResult.frames.map((f: any) => {
        const housedHouseholds = f.units
          .filter((u: any) => u.household)
          .map((u: any) => (u.rent * 12) / u.household.income * 100);
        return housedHouseholds.length > 0
          ? housedHouseholds.reduce((a: number, b: number) => a + b, 0) / housedHouseholds.length
          : 0;
      })),
      policyMetrics: simulationResult.frames[simulationResult.frames.length - 1]?.metrics?.policy_metrics,
    };
  };

  const extractYearlyData = (simulationResult: any) => {
    return simulationResult.frames.map((frame: any) => {
      const satisfactionHouseholds = frame.units.filter((u: any) => u.household?.satisfaction);
      return {
        period: frame.period,
        avgRent: frame.metrics.average_rent,
        unhoused: frame.unhoused_households?.length || 0,
        satisfaction:
          satisfactionHouseholds.length > 0
            ? (satisfactionHouseholds.reduce((acc: number, u: any) => acc + u.household.satisfaction, 0) /
                satisfactionHouseholds.length) * 100
            : 0,
        rentBurden:
          frame.units.filter((u: any) => u.household).length > 0
            ? frame.units
                .filter((u: any) => u.household)
                .reduce((acc: number, u: any) => acc + ((u.rent * 12) / u.household.income * 100), 0) /
              frame.units.filter((u: any) => u.household).length
            : 0,
      };
    });
  };

  const calculateAverage = (numbers: number[]) => {
    return numbers.length > 0 
      ? numbers.reduce((a, b) => a + b, 0) / numbers.length 
      : 0;
  };

  const formatMetric = (value: number, type: 'currency' | 'percentage' | 'number' = 'number') => {
    if (type === 'currency') {
      return new Intl.NumberFormat('nl-NL', {
        style: 'currency',
        currency: 'EUR',
        maximumFractionDigits: 0,
      }).format(value);
    } else if (type === 'percentage') {
      return `${value.toFixed(1)}%`;
    } else {
      return value.toFixed(1);
    }
  };

  const getPolicyName = (policy: string) => {
    switch (policy) {
      case 'rent_cap':
        return 'Rent Cap';
      case 'lvt':
        return 'Land Value Tax';
      default:
        return 'No Policy';
    }
  };

  const handlePolicyChange = (simNumber: number, policy: string) => {
    if (simNumber === 1) {
      setSimulation1(prev => ({ ...prev, policy }));
    } else {
      setSimulation2(prev => ({ ...prev, policy }));
    }
  };

  const combinedData = simulation1.yearlyData.map((data1, index) => {
    const data2 = simulation2.yearlyData[index] || {};
    return {
      period: data1.period,
      [`avgRent1`]: data1.avgRent,
      [`avgRent2`]: data2.avgRent,
      [`unhoused1`]: data1.unhoused,
      [`unhoused2`]: data2.unhoused,
      [`satisfaction1`]: data1.satisfaction,
      [`satisfaction2`]: data2.satisfaction,
      [`rentBurden1`]: data1.rentBurden,
      [`rentBurden2`]: data2.rentBurden,
    };
  });

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom align="center" sx={{ color: colors.textDark }}>
        Policy Comparison
      </Typography>

      {/* Policy Selection */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={5}>
            <FormControl fullWidth>
              <InputLabel>Policy 1</InputLabel>
              <Select
                value={simulation1.policy}
                onChange={(e) => handlePolicyChange(1, e.target.value)}
                label="Policy 1"
              >
                <MenuItem value="none">No Policy (Free market)</MenuItem>
                <MenuItem value="rent_cap">Rent Cap (Max 10% increase)</MenuItem>
                <MenuItem value="lvt">Land Value Tax</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={2} sx={{ textAlign: 'center' }}>
            <CompareArrowsIcon sx={{ fontSize: 40, color: colors.textDark }} />
          </Grid>
          
          <Grid item xs={12} md={5}>
            <FormControl fullWidth>
              <InputLabel>Policy 2</InputLabel>
              <Select
                value={simulation2.policy}
                onChange={(e) => handlePolicyChange(2, e.target.value)}
                label="Policy 2"
              >
                <MenuItem value="none">No Policy (Free market)</MenuItem>
                <MenuItem value="rent_cap">Rent Cap (Max 10% increase)</MenuItem>
                <MenuItem value="lvt">Land Value Tax</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button
            variant="contained"
            onClick={runComparison}
            disabled={isLoading}
            sx={{
              backgroundColor: colors.yellowPrimary,
              color: colors.textDark,
              '&:hover': {
                backgroundColor: colors.yellowDark,
              },
            }}
          >
            {isLoading ? 'Running Simulations...' : 'Compare Policies'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {simulation1.metrics && simulation2.metrics && (
        <>
          {/* Key Metrics Comparison */}
          <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Key Metrics Comparison
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ p: 2, backgroundColor: colors.yellowLight, borderRadius: 1 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {getPolicyName(simulation1.policy)}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography>
                      Average Rent: {formatMetric(simulation1.metrics.avgRent, 'currency')}
                    </Typography>
                    <Typography>
                      Unhoused Households: {formatMetric(simulation1.metrics.totalUnhoused)}
                    </Typography>
                    <Typography>
                      Average Satisfaction: {formatMetric(simulation1.metrics.avgSatisfaction, 'percentage')}
                    </Typography>
                    <Typography>
                      Average Rent Burden: {formatMetric(simulation1.metrics.avgRentBurden, 'percentage')}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ p: 2, backgroundColor: colors.yellowLight, borderRadius: 1 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {getPolicyName(simulation2.policy)}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography>
                      Average Rent: {formatMetric(simulation2.metrics.avgRent, 'currency')}
                    </Typography>
                    <Typography>
                      Unhoused Households: {formatMetric(simulation2.metrics.totalUnhoused)}
                    </Typography>
                    <Typography>
                      Average Satisfaction: {formatMetric(simulation2.metrics.avgSatisfaction, 'percentage')}
                    </Typography>
                    <Typography>
                      Average Rent Burden: {formatMetric(simulation2.metrics.avgRentBurden, 'percentage')}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Paper>

          {/* Charts */}
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Trends Over Time
            </Typography>

            {/* Average Rent */}
            <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
              Average Rent
            </Typography>
            <Box sx={{ height: 300, mb: 4 }}>
              <ResponsiveContainer>
                <LineChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" label={{ value: 'Period', position: 'bottom' }} />
                  <YAxis label={{ value: 'Rent (€)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value: any) => formatMetric(value, 'currency')} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="avgRent1"
                    name={getPolicyName(simulation1.policy)}
                    stroke={colors.policy1}
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="avgRent2"
                    name={getPolicyName(simulation2.policy)}
                    stroke={colors.policy2}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>

            {/* Unhoused Households */}
            <Typography variant="subtitle1" gutterBottom>
              Unhoused Households
            </Typography>
            <Box sx={{ height: 300, mb: 4 }}>
              <ResponsiveContainer>
                <LineChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" label={{ value: 'Period', position: 'bottom' }} />
                  <YAxis label={{ value: 'Households', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="unhoused1"
                    name={getPolicyName(simulation1.policy)}
                    stroke={colors.policy1}
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="unhoused2"
                    name={getPolicyName(simulation2.policy)}
                    stroke={colors.policy2}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>

            {/* Satisfaction */}
            <Typography variant="subtitle1" gutterBottom>
              Average Satisfaction
            </Typography>
            <Box sx={{ height: 300, mb: 4 }}>
              <ResponsiveContainer>
                <LineChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" label={{ value: 'Period', position: 'bottom' }} />
                  <YAxis label={{ value: 'Satisfaction (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value: any) => formatMetric(value, 'percentage')} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="satisfaction1"
                    name={getPolicyName(simulation1.policy)}
                    stroke={colors.policy1}
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="satisfaction2"
                    name={getPolicyName(simulation2.policy)}
                    stroke={colors.policy2}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>

            {/* Rent Burden */}
            <Typography variant="subtitle1" gutterBottom>
              Average Rent Burden
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer>
                <LineChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" label={{ value: 'Period', position: 'bottom' }} />
                  <YAxis label={{ value: 'Rent Burden (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value: any) => formatMetric(value, 'percentage')} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="rentBurden1"
                    name={getPolicyName(simulation1.policy)}
                    stroke={colors.policy1}
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="rentBurden2"
                    name={getPolicyName(simulation2.policy)}
                    stroke={colors.policy2}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </>
      )}
    </Container>
  );
};

export default PolicyComparisonPage;