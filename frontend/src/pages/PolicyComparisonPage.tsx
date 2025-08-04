import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
  CircularProgress,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import InfoIcon from '@mui/icons-material/Info';
import { useSimulation } from '../contexts/SimulationContext';
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
  ErrorBar,
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

interface AggregateMetrics {
  mean: number;
  std: number;
  p25: number;
  p75: number;
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
  aggregateMetrics?: {
    rent: AggregateMetrics;
    satisfaction: AggregateMetrics;
    rent_burden: AggregateMetrics;
    unhoused: AggregateMetrics;
  };
}

const PolicyComparisonPage = () => {
  const { startSimulation, resetSimulation } = useSimulation();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  
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

  const runSimulationWithSSE = async (params: any): Promise<any> => {
    return new Promise(async (resolve, reject) => {
      try {
        const response = await fetch('http://localhost:8000/simulation/run', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
          },
          body: JSON.stringify(params),
        });
        
        if (!response.ok) {
          throw new Error('Failed to start simulation');
        }
        
        // Check if this is a streaming response
        const contentType = response.headers.get('content-type');
        if (!contentType?.includes('text/event-stream')) {
          // Fallback to regular JSON response
          const result = await response.json();
          resolve(result);
          return;
        }
        
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body');
        }
        
        const decoder = new TextDecoder();
        let buffer = '';
        
        const processChunk = async () => {
          try {
            console.log('Starting to read stream...');
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                console.log('Stream ended');
                break;
              }
              
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || ''; // Keep incomplete line in buffer
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.progress !== undefined) {
                      // console.log('Progress update received:', data.progress, data.message);
                      setProgress(data.progress);
                      setProgressMessage(data.message || '');
                    }
                    
                    if (data.completed) {
                      console.log('Simulation completed');
                      resolve(data.result);
                      return;
                    }
                  } catch (e) {
                    console.error('Error parsing chunk:', e, 'Line:', line);
                  }
                }
              }
            }
          } catch (readerError) {
            console.error('Error reading stream:', readerError);
            reject(readerError);
          }
        };

        reader.read().then(processChunk);
      } catch (error) {
        console.error('Error setting up stream:', error);
        
        // Fallback to regular fetch if streaming fails
        try {
          const response = await fetch('http://localhost:8000/simulation/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const result = await response.json();
          resolve(result);
        } catch (fallbackError) {
          reject(fallbackError);
        }
      }
    });
  };

  const runComparison = async () => {
    setIsLoading(true);
    setError(null);
    setProgress(0);
    setProgressMessage('Starting comparison...');
    
    try {
      // Run first simulation with progress updates
      setProgressMessage('Running first simulation...');
      const result1 = await runSimulationWithSSE({
        initial_households: 1000,
        migration_rate: 0.1,
        years: 10,
        policy: simulation1.policy === 'rent_cap' ? 'rent_cap' : 
               simulation1.policy === 'lvt' ? 'lvt' : 'none',
        lvt_rate: simulation1.policy === 'lvt' ? 0.40 : 0,
        num_runs: 5,
      });
      
      // Store first simulation results
      console.log('Processing first simulation result:', result1);
      setSimulation1(prev => ({
        ...prev,
        metrics: extractMetrics(result1),
        yearlyData: extractYearlyData(result1),
        aggregateMetrics: result1.aggregate_metrics,
      }));

      // Reset progress for second simulation
      setProgress(0);
      setProgressMessage('Running second simulation...');
      
      // Run second simulation with progress updates
      const result2 = await runSimulationWithSSE({
        initial_households: 1000,
        migration_rate: 0.1,
        years: 10,
        policy: simulation2.policy === 'rent_cap' ? 'rent_cap' : 
               simulation2.policy === 'lvt' ? 'lvt' : 'none',
        lvt_rate: simulation2.policy === 'lvt' ? 0.40 : 0,
        num_runs: 5,
      });

      // Store second simulation results
      console.log('Processing second simulation result:', result2);
      setSimulation2(prev => ({
        ...prev,
        metrics: extractMetrics(result2),
        yearlyData: extractYearlyData(result2),
        aggregateMetrics: result2.aggregate_metrics,
      }));

      setProgress(100);
      setProgressMessage('Comparison complete!');
      console.log('Comparison completed successfully');
    } catch (err) {
      console.error('Error running comparison:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while running the comparison');
    } finally {
      setIsLoading(false);
      console.log('Loading state set to false');
    }
  };

  const extractMetrics = (simulationResult: any): ComparisonMetrics => {
    // Add defensive checks for the simulation result structure
    if (!simulationResult || !simulationResult.frames || !Array.isArray(simulationResult.frames)) {
      console.warn('Invalid simulation result structure:', simulationResult);
      return {
        avgRent: 0,
        totalUnhoused: 0,
        avgSatisfaction: 0,
        avgRentBurden: 0,
      };
    }

    // Extract and calculate average metrics from the simulation result
    try {
      const avgRent = calculateAverage(simulationResult.frames.map((f: any) => {
        return f.metrics?.average_rent || 0;
      }));

      const totalUnhoused = calculateAverage(simulationResult.frames.map((f: any) => {
        return f.unhoused_households?.length || 0;
      }));

      const avgSatisfaction = calculateAverage(simulationResult.frames.map((f: any) => {
        if (!f.units || !Array.isArray(f.units)) return 0;
        const housedUnits = f.units.filter((u: any) => u.household);
        if (housedUnits.length === 0) return 0;
        const totalSatisfaction = housedUnits.reduce((sum: number, u: any) => 
          sum + (u.household?.satisfaction || 0), 0);
        return (totalSatisfaction / housedUnits.length) * 100; // Convert to percentage
      }));

      const avgRentBurden = calculateAverage(simulationResult.frames.map((f: any) => {
        if (!f.units || !Array.isArray(f.units)) return 0;
        const housedUnits = f.units.filter((u: any) => u.household && u.household.income > 0);
        if (housedUnits.length === 0) return 0;
        const totalRentBurden = housedUnits.reduce((sum: number, u: any) => {
          const household = u.household;
          let burden = 0;
          if (household.monthly_payment && household.monthly_payment > 0) {
            // Owner-occupier: use mortgage payment
            burden = (household.monthly_payment / household.income) * 100;
          } else {
            // Renter: use rent
            burden = (u.rent / household.income) * 100;
          }
          return sum + burden;
        }, 0);
        return totalRentBurden / housedUnits.length;
      }));

      return {
        avgRent,
        totalUnhoused,
        avgSatisfaction,
        avgRentBurden,
      };
    } catch (error) {
      console.error('Error extracting metrics:', error);
      return {
        avgRent: 0,
        totalUnhoused: 0,
        avgSatisfaction: 0,
        avgRentBurden: 0,
      };
    }
  };

  const extractYearlyData = (simulationResult: any) => {
    // Add defensive checks
    if (!simulationResult || !simulationResult.frames || !Array.isArray(simulationResult.frames)) {
      console.warn('Invalid simulation result for yearly data:', simulationResult);
      return [];
    }

    try {
      return simulationResult.frames.map((frame: any) => {
        // Ensure frame has required structure
        if (!frame || !frame.units || !Array.isArray(frame.units)) {
          return {
            period: frame?.period || 0,
            avgRent: 0,
            avgSatisfaction: 0,
            avgRentBurden: 0,
            unhoused: 0,
          };
        }

        // Calculate satisfaction for housed units only
        const housedUnits = frame.units.filter((u: any) => u.household);
        const avgSatisfaction = housedUnits.length > 0 
          ? (housedUnits.reduce((sum: number, u: any) => sum + (u.household?.satisfaction || 0), 0) / housedUnits.length) * 100
          : 0;

        // Calculate rent burden for units with income data
        const unitsWithIncome = frame.units.filter((u: any) => u.household && u.household.income > 0);
        const avgRentBurden = unitsWithIncome.length > 0 
          ? unitsWithIncome.reduce((sum: number, u: any) => {
              const household = u.household;
              let burden = 0;
              if (household.monthly_payment && household.monthly_payment > 0) {
                burden = (household.monthly_payment / household.income) * 100;
              } else {
                burden = (u.rent / household.income) * 100;
              }
              return sum + burden;
            }, 0) / unitsWithIncome.length
          : 0;

        return {
          period: frame.period || 0,
          avgRent: frame.metrics?.average_rent || 0,
          satisfaction: avgSatisfaction,
          rentBurden: avgRentBurden,
          unhoused: frame.unhoused_households?.length || 0,
        };
      });
    } catch (error) {
      console.error('Error extracting yearly data:', error);
      return [];
    }
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

  const formatMetricWithRange = (value: AggregateMetrics | undefined, type: 'currency' | 'percentage' | 'number' = 'number') => {
    if (!value || typeof value.mean === 'undefined') {
      return <span>No data available</span>;
    }
    
    const mean = formatMetric(value.mean, type);
    const range = `${formatMetric(value.p25, type)} - ${formatMetric(value.p75, type)}`;
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <span>{mean}</span>
        <Tooltip title="25th to 75th percentile range">
          <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary', fontSize: '0.875rem' }}>
            <span>({range})</span>
            <InfoIcon sx={{ fontSize: 16, ml: 0.5 }} />
          </Box>
        </Tooltip>
      </Box>
    );
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

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" paragraph>
          This tool allows you to compare the effects of different housing policies by running parallel simulations with identical starting conditions. Each policy is simulated 100 times with different random seeds to ensure statistical robustness. Each simulation runs for 10 years with 1000 initial households and a 10% yearly migration rate, across approximately 1000 housing units. The policies available for comparison are:
          <ul>
            <li>Free market approach (no intervention)</li>
            <li>Rent cap limiting yearly increases to 5%</li>
            <li>Land value tax of 40% annually on the unimproved land value</li>
          </ul>
          The simulation tracks key metrics including average rent prices, number of unhoused households, tenant satisfaction, and rent burden (percentage of income spent on housing). Results show both the mean values and the range between the 25th and 75th percentiles to indicate the variation in outcomes. About half of the initial households are owner-occupiers with mortgages, while the other half are renters.
        </Typography>
      </Paper>

      {/* Policy Selection */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap' }}>
          <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
            <FormControl fullWidth>
              <InputLabel>Policy 1</InputLabel>
              <Select
                value={simulation1.policy}
                onChange={(e) => handlePolicyChange(1, e.target.value)}
                label="Policy 1"
              >
                <MenuItem value="none">No Policy (Free market)</MenuItem>
                <MenuItem value="rent_cap">Rent Cap (Max 10% yearly increase)</MenuItem>
                <MenuItem value="lvt">Land Value Tax (40% on land value)</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box sx={{ textAlign: 'center', flex: '0 0 auto' }}>
            <CompareArrowsIcon sx={{ fontSize: 40, color: colors.textDark }} />
          </Box>
          
          <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
            <FormControl fullWidth>
              <InputLabel>Policy 2</InputLabel>
              <Select
                value={simulation2.policy}
                onChange={(e) => handlePolicyChange(2, e.target.value)}
                label="Policy 2"
              >
                <MenuItem value="none">No Policy (Free market)</MenuItem>
                <MenuItem value="rent_cap">Rent Cap (Max 10% yearly increase)</MenuItem>
                <MenuItem value="lvt">Land Value Tax (40% on land value)</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>

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
          {isLoading && (
            <Box sx={{ width: '100%', mt: 2 }}>
              <LinearProgress variant="determinate" value={progress} />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {progressMessage} ({Math.round(progress)}% complete)
              </Typography>
            </Box>
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {simulation1.metrics && simulation2.metrics && simulation1.aggregateMetrics && simulation2.aggregateMetrics && (
        <>
          {/* Key Metrics Comparison */}
          <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Key Metrics Comparison
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
                <Box sx={{ p: 2, backgroundColor: colors.yellowLight, borderRadius: 1 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {getPolicyName(simulation1.policy)}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography>
                      Average Rent: {formatMetricWithRange(simulation1.aggregateMetrics?.rent, 'currency')}
                    </Typography>
                    <Typography>
                      Unhoused Households: {formatMetricWithRange(simulation1.aggregateMetrics?.unhoused)}
                    </Typography>
                    <Typography>
                      Average Satisfaction: {formatMetricWithRange(simulation1.aggregateMetrics?.satisfaction, 'percentage')}
                    </Typography>
                    <Typography>
                      Average Rent Burden: {formatMetricWithRange(simulation1.aggregateMetrics?.rent_burden, 'percentage')}
                    </Typography>
                  </Box>
                </Box>
              </Box>
              <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
                <Box sx={{ p: 2, backgroundColor: colors.yellowLight, borderRadius: 1 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {getPolicyName(simulation2.policy)}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography>
                      Average Rent: {formatMetricWithRange(simulation2.aggregateMetrics?.rent, 'currency')}
                    </Typography>
                    <Typography>
                      Unhoused Households: {formatMetricWithRange(simulation2.aggregateMetrics?.unhoused)}
                    </Typography>
                    <Typography>
                      Average Satisfaction: {formatMetricWithRange(simulation2.aggregateMetrics?.satisfaction, 'percentage')}
                    </Typography>
                    <Typography>
                      Average Rent Burden: {formatMetricWithRange(simulation2.aggregateMetrics?.rent_burden, 'percentage')}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          </Paper>

          {/* Charts Section */}
          <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ color: colors.textDark }}>
              Policy Impact Analysis
            </Typography>

            {/* Rent Trends with Area Chart */}
            <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
              Average Rent Trends Over Time
            </Typography>
            <Box sx={{ height: 400, mb: 4 }}>
              <ResponsiveContainer>
                <AreaChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="period" 
                    label={{ value: 'Period (6-month intervals)', position: 'insideBottom', offset: -10 }}
                    padding={{ left: 30, right: 30 }}
                  />
                  <YAxis label={{ value: 'Rent (€)', angle: -90, position: 'insideLeft' }} />
                  <RechartsTooltip 
                    formatter={(value: any) => formatMetric(value, 'currency')}
                    labelFormatter={(period) => `Period ${period}`}
                  />
                  <Legend 
                    verticalAlign="top" 
                    height={36}
                  />
                  <Area
                    type="monotone"
                    dataKey="avgRent1"
                    name={getPolicyName(simulation1.policy)}
                    stroke={colors.policy1}
                    fill={colors.policy1}
                    fillOpacity={0.3}
                    strokeWidth={3}
                  />
                  <Area
                    type="monotone"
                    dataKey="avgRent2"
                    name={getPolicyName(simulation2.policy)}
                    stroke={colors.policy2}
                    fill={colors.policy2}
                    fillOpacity={0.3}
                    strokeWidth={3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>

            {/* Housing Crisis Indicator - Unhoused vs Rent Burden */}
            <Typography variant="subtitle1" gutterBottom>
              Housing Crisis Indicators
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
              {/* Unhoused Households */}
              <Box sx={{ flex: '1 1 400px', minWidth: '400px', height: 350 }}>
                <Typography variant="body2" gutterBottom>Unhoused Households</Typography>
                <ResponsiveContainer>
                  <LineChart data={combinedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="unhoused1"
                      name={getPolicyName(simulation1.policy)}
                      stroke={colors.policy1}
                      strokeWidth={3}
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="unhoused2"
                      name={getPolicyName(simulation2.policy)}
                      stroke={colors.policy2}
                      strokeWidth={3}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>

              {/* Rent Burden */}
              <Box sx={{ flex: '1 1 400px', minWidth: '400px', height: 350 }}>
                <Typography variant="body2" gutterBottom>Average Rent Burden (%)</Typography>
                <ResponsiveContainer>
                  <AreaChart data={combinedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <RechartsTooltip formatter={(value: any) => `${value}%`} />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="rentBurden1"
                      name={getPolicyName(simulation1.policy)}
                      stroke={colors.policy1}
                      fill={colors.policy1}
                      fillOpacity={0.4}
                    />
                    <Area
                      type="monotone"
                      dataKey="rentBurden2"
                      name={getPolicyName(simulation2.policy)}
                      stroke={colors.policy2}
                      fill={colors.policy2}
                      fillOpacity={0.4}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </Box>

            {/* Satisfaction Trends */}
            <Typography variant="subtitle1" gutterBottom>
              Tenant Satisfaction Over Time
            </Typography>
            <Box sx={{ height: 350, mb: 4 }}>
              <ResponsiveContainer>
                <LineChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="period" 
                    label={{ value: 'Period', position: 'insideBottom', offset: -10 }}
                  />
                  <YAxis 
                    label={{ value: 'Satisfaction (%)', angle: -90, position: 'insideLeft' }}
                    domain={[0, 100]}
                  />
                  <RechartsTooltip formatter={(value: any) => `${value}%`} />
                  <Legend verticalAlign="top" height={36} />
                  <Line
                    type="monotone"
                    dataKey="satisfaction1"
                    name={getPolicyName(simulation1.policy)}
                    stroke={colors.policy1}
                    strokeWidth={3}
                    dot={{ r: 3 }}
                    connectNulls={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="satisfaction2"
                    name={getPolicyName(simulation2.policy)}
                    stroke={colors.policy2}
                    strokeWidth={3}
                    dot={{ r: 3 }}
                    connectNulls={false}
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