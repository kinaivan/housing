import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid as MuiGrid,
  Divider,
  Card,
  CardContent,
  Chip,

  Stack,
  LinearProgress,
  Alert,
} from '@mui/material';
import EventLog from '../components/EventLog';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import StarIcon from '@mui/icons-material/Star';
import BuildIcon from '@mui/icons-material/Build';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useSimulation } from '../contexts/SimulationContext';

// Create a properly typed Grid component
const Grid = MuiGrid as React.ComponentType<{
  container?: boolean;
  item?: boolean;
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
  spacing?: number;
  sx?: any;
  children?: React.ReactNode;
  component?: React.ElementType;
}>;

// Theme colors
const colors = {
  yellowPrimary: '#FFD700',
  yellowLight: '#FFF4B8',
  yellowDark: '#FFC000',
  textDark: '#2C2C2C',
  white: '#FFFFFF',
  occupied: '#28a745',  // Rented units (green)
  ownerOccupied: '#2196f3',  // Owner-occupied units (blue)
  vacant: '#808080',  // Empty units (grey)
  warning: '#ff9800',
  info: '#2196f3',
  success: '#4caf50',
};

interface Unit {
  id: number;
  occupants: number;
  rent: number;
  is_occupied: boolean;
  is_owner_occupied: boolean;
  quality?: number;
  lastRenovation?: number;
  household?: {
    id: number;
    name: string;
    age: number;
    size: number;
    income: number;
    wealth: number;
    satisfaction: number;
    life_stage: string;
    months_in_current_unit?: number;
    monthly_payment?: number;
    mortgage_balance?: number;
    mortgage_interest_rate?: number;
    mortgage_term?: number;
  };
}

interface UnitHistoryEntry {
  period: number;
  occupants: number;
  rent: number;
  occupancyRate: number;
  quality: number;
  satisfaction: number;
  rentBurden: number;
  income: number;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  icon, 
  subtitle, 
  trend, 
  color = colors.info 
}) => {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUpIcon sx={{ color: colors.success, fontSize: 16 }} />;
    if (trend === 'down') return <TrendingDownIcon sx={{ color: colors.vacant, fontSize: 16 }} />;
    return null;
  };

  return (
    <Card elevation={3} sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Box sx={{ color, fontSize: 24 }}>{icon}</Box>
          <Typography variant="h6" sx={{ fontWeight: 600, color: colors.textDark }}>
            {title}
          </Typography>
          {getTrendIcon()}
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: colors.textDark, mb: 0.5 }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

const PropertyDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { units, frame, stats, isPaused, resumeSimulation } = useSimulation();
  const [unitHistory, setUnitHistory] = useState<UnitHistoryEntry[]>([]);
  
  // Convert the URL parameter to a number
  const unitId = Number(id);
  
  // Find the unit with the matching ID
  const unit = units.find(u => u.id === unitId);
  
  // Update history when frame changes
  useEffect(() => {
    if (frame && unit) {
      setUnitHistory(prev => {
        // Log current unit data for debugging
        console.log('Updating unit history:', {
          unitId: unit.id,
          period: frame.period,
          satisfaction: unit.household?.satisfaction,
          quality: unit.quality
        });

        const rentBurden = unit.household ? ((unit.rent) / unit.household.income * 100) : 0;
        
        const newEntry: UnitHistoryEntry = {
          period: frame.period,
          occupants: unit.occupants,
          rent: unit.rent,
          occupancyRate: unit.is_occupied ? 100 : 0,
          quality: (unit.quality || 0) * 100,
          satisfaction: unit.household?.satisfaction ? unit.household.satisfaction * 100 : 0,
          rentBurden: rentBurden,
          income: unit.household?.income || 0,
        };
        
        // Check if we already have this period
        const exists = prev.some(p => p.period === frame.period);
        if (exists) {
          // Update existing entry
          return prev.map(p => p.period === frame.period ? newEntry : p);
        }
        
        // Add new entry and sort by period
        return [...prev, newEntry].sort((a, b) => a.period - b.period);
      });
    }
  }, [frame, unit]);

  // Calculate analytics
  const analytics = useMemo(() => {
    if (!unit || unitHistory.length === 0) return null;

    // Get last 12 periods (or all if less than 12)
    const recentHistory = unitHistory.slice(-12);
    
    // Calculate average occupancy over recent periods
    const avgOccupancy = recentHistory.reduce((sum, entry) => sum + entry.occupancyRate, 0) / recentHistory.length;

    // Calculate rent growth over the last 12 periods
    const rentGrowth = recentHistory.length > 1 
      ? ((recentHistory[recentHistory.length - 1].rent - recentHistory[0].rent) / recentHistory[0].rent) * 100 
      : 0;
    
    // Calculate vacancy rate over all history
    const vacantPeriods = unitHistory.filter(entry => entry.occupancyRate === 0).length;
    const totalPeriods = unitHistory.length;
    const vacancyRate = totalPeriods > 0 ? (vacantPeriods / totalPeriods) * 100 : 0;

    // Calculate total revenue (only count rent when occupied)
    const totalRevenue = unitHistory.reduce((sum, entry) => {
      return sum + (entry.occupancyRate > 0 ? entry.rent : 0);
    }, 0);
    
    return {
      avgOccupancy,
      rentGrowth,
      vacancyRate,
      totalRevenue,
      // Current occupancy streak (number of consecutive occupied periods)
      occupancyStreak: unit.is_occupied 
        ? [...unitHistory].reverse().findIndex(entry => entry.occupancyRate === 0)
        : 0,
    };
  }, [unit, unitHistory]);

  if (!unit) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Property #{unitId} not found</Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Available units: {units.length > 0 ? units.map(u => u.id).join(', ') : 'None loaded yet'}
        </Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>
          Simulation status: {status} | Frame: {frame ? `Period ${frame.period}` : 'No frame'}
        </Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)}>
          Go Back
        </Button>
      </Container>
    );
  }

  const currentRentBurden = unit.household ? ((unit.rent) / unit.household.income * 100) : 0;
  const isAffordable = currentRentBurden <= 30;
  const qualityScore = (unit.quality || 0) * 100;
  const satisfactionScore = unit.household?.satisfaction ? unit.household.satisfaction * 100 : 0;

  const getOccupancyColor = (unit: Unit) => {
    if (unit.is_owner_occupied) return colors.ownerOccupied;
    if (unit.is_occupied) return colors.occupied;
    return colors.vacant;
  };

  const getOccupancyStatus = (unit: Unit) => {
    if (unit.is_owner_occupied) return 'Owner Occupied';
    if (unit.is_occupied) return 'Rented';
    return 'Vacant';
  };

  const formatLifeStage = (stage: string) => {
    return stage
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Button 
        startIcon={<ArrowBackIcon />} 
        onClick={async () => {
          // Auto-resume simulation if it was paused
          if (isPaused) {
            try {
              await resumeSimulation();
              console.log('Simulation auto-resumed when returning to main view');
            } catch (error) {
              console.error('Failed to auto-resume simulation:', error);
            }
          }
          navigate(-1);
        }}
        sx={{ 
          mb: 3,
          backgroundColor: colors.yellowPrimary,
          color: colors.textDark,
          '&:hover': {
            backgroundColor: colors.yellowDark,
          }
        }}
      >
        Back to Simulation
      </Button>

      {/* Auto-pause notification */}
      {isPaused && (
        <Alert 
          severity="info" 
          sx={{ 
            mb: 3,
            backgroundColor: colors.yellowLight,
            borderColor: colors.yellowDark,
            '& .MuiAlert-icon': {
              color: colors.textDark,
            }
          }}
        >
          <Typography variant="body2" sx={{ color: colors.textDark }}>
            ⏸️ Simulation paused for detailed analysis. Click "Back to Simulation" to resume.
          </Typography>
        </Alert>
      )}

      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <HomeIcon sx={{ fontSize: 40, color: getOccupancyColor(unit) }} />
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 'bold', color: colors.textDark }}>
            Property #{unit.id}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
            <Chip 
              label={getOccupancyStatus(unit)}
              sx={{ 
                backgroundColor: getOccupancyColor(unit),
                color: 'white',
                fontWeight: 600,
              }}
            />
            <Chip 
              label={frame ? `Period ${frame.period}` : 'No Data'}
              variant="outlined"
              sx={{ fontWeight: 500 }}
            />
          </Box>
        </Box>
      </Box>

      {/* Current Tenant Information */}
      {unit.is_occupied && unit.household && (
        <Paper 
          elevation={3} 
          sx={{ 
            p: 3, 
            mb: 4, 
            border: '2px solid',
            borderColor: unit.is_owner_occupied ? colors.ownerOccupied : colors.occupied,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Background decoration */}
          <Box
            sx={{
              position: 'absolute',
              right: -50,
              top: -50,
              width: 200,
              height: 200,
              borderRadius: '50%',
              background: unit.is_owner_occupied 
                ? `linear-gradient(45deg, ${colors.ownerOccupied}22, ${colors.ownerOccupied}11)`
                : `linear-gradient(45deg, ${colors.occupied}22, ${colors.occupied}11)`,
              zIndex: 0,
            }}
          />

          {/* Content */}
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Typography variant="h4" sx={{ mb: 3, color: colors.textDark, display: 'flex', alignItems: 'center', gap: 2 }}>
              <PersonIcon sx={{ fontSize: 32, color: unit.is_owner_occupied ? colors.ownerOccupied : colors.occupied }} />
              {unit.is_owner_occupied ? 'Property Owner' : 'Current Tenant'}
            </Typography>

            <Grid container spacing={4}>
              {/* Basic Information */}
              <Grid item xs={12} md={4} component="div">
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2, color: colors.textDark }}>
                    Household Information
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">Name</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 500 }}>
                        {unit.household.name}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">Age & Life Stage</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {unit.household.age} years old
                      </Typography>
                      <Typography variant="body1" color="textSecondary">
                        {formatLifeStage(unit.household.life_stage)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">Household Size</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {unit.household.size} {unit.household.size === 1 ? 'person' : 'people'}
                      </Typography>
                    </Box>
                  </Stack>
                </Box>
              </Grid>

              {/* Financial Information */}
              <Grid item xs={12} md={4} component="div">
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2, color: colors.textDark }}>
                    Financial Status
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">Monthly Income</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 500, color: colors.success }}>
                        ${unit.household.income.toLocaleString()}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">Wealth</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 500, color: colors.info }}>
                        ${unit.household.wealth.toLocaleString()}
                      </Typography>
                    </Box>
                    {unit.is_owner_occupied && unit.household.mortgage_balance && (
                      <Box>
                        <Typography variant="subtitle2" color="textSecondary">Mortgage Details</Typography>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          Balance: ${unit.household.mortgage_balance.toLocaleString()}
                        </Typography>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          Rate: {((unit.household.mortgage_interest_rate || 0) * 100).toFixed(2)}%
                        </Typography>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          Term: {unit.household.mortgage_term} years
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </Box>
              </Grid>

              {/* Housing Costs & Satisfaction */}
              <Grid item xs={12} md={4} component="div">
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ mb: 2, color: colors.textDark }}>
                    Housing Status
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">
                        {unit.is_owner_occupied ? 'Monthly Payment' : 'Monthly Rent'}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 500 }}>
                        ${unit.rent.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {currentRentBurden.toFixed(1)}% of monthly income
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">Time in Property</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {unit.household.months_in_current_unit ? (
                          `${Math.floor(unit.household.months_in_current_unit / 12)} years, ${unit.household.months_in_current_unit % 12} months`
                        ) : (
                          'Recently moved in'
                        )}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2" color="textSecondary">Satisfaction Level</Typography>
                      <Box sx={{ 
                        p: 1.5, 
                        mt: 1,
                        borderRadius: 1, 
                        backgroundColor: satisfactionScore >= 70 ? '#e8f5e8' : 
                                      satisfactionScore >= 40 ? '#fff3e0' : '#ffebee',
                        border: `1px solid ${satisfactionScore >= 70 ? '#c8e6c9' : 
                                          satisfactionScore >= 40 ? '#ffe0b2' : '#ffcdd2'}`,
                      }}>
                        <Typography variant="h6" sx={{ 
                          fontWeight: 500,
                          color: satisfactionScore >= 70 ? '#2e7d32' : 
                                satisfactionScore >= 40 ? '#ef6c00' : '#c62828',
                        }}>
                          {satisfactionScore.toFixed(0)}%
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                            {satisfactionScore >= 70 ? '😊 Very Happy' : 
                             satisfactionScore >= 40 ? '😐 Moderately Satisfied' : '😟 Unsatisfied'}
                          </Typography>
                        </Typography>
                      </Box>
                    </Box>
                  </Stack>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Paper>
      )}

      {/* Key Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }} component="div">
        <Grid item xs={12} sm={6} md={3} component="div">
          <MetricCard
            title="Monthly Rent"
            value={`$${unit.rent.toLocaleString()}`}
            icon={<AttachMoneyIcon />}
            subtitle="Current rate"
            trend={analytics && analytics.rentGrowth > 0 ? 'up' : analytics && analytics.rentGrowth < 0 ? 'down' : 'neutral'}
            color={colors.info}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3} component="div">
          <MetricCard
            title="Occupants"
            value={unit.occupants}
            icon={<PersonIcon />}
            subtitle={unit.is_occupied ? `${unit.household?.size || 0} person household` : 'Vacant'}
            color={colors.occupied}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3} component="div">
          <MetricCard
            title="Quality Score"
            value={`${qualityScore.toFixed(0)}%`}
            icon={<StarIcon />}
            subtitle={unit.lastRenovation ? `Renovated ${unit.lastRenovation} months ago` : 'Never renovated'}
            color={colors.warning}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3} component="div">
          <MetricCard
            title="Satisfaction"
            value={unit.is_occupied ? `${satisfactionScore.toFixed(0)}%` : 'N/A'}
            icon={<SentimentSatisfiedIcon />}
            subtitle={unit.is_occupied ? 'Resident satisfaction' : 'No residents'}
            color={colors.success}
          />
        </Grid>
      </Grid>

      {/* Resident Information */}
      {unit.is_occupied && unit.household && (
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" sx={{ mb: 3, fontWeight: 600, color: colors.textDark }}>
            {unit.is_owner_occupied ? 'Property Owner' : 'Current Residents'}
          </Typography>
          <Grid container spacing={3} component="div">
            {/* Basic Information */}
            <Grid item xs={12} md={4} component="div">
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Household Information
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon sx={{ color: colors.textDark }} />
                  <Typography variant="body1">
                    <strong>Name:</strong> {unit.household.name}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon sx={{ color: colors.textDark }} />
                  <Typography variant="body1">
                    <strong>Age:</strong> {unit.household.age} years
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon sx={{ color: colors.textDark }} />
                  <Typography variant="body1">
                    <strong>Life Stage:</strong> {formatLifeStage(unit.household.life_stage)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon sx={{ color: colors.textDark }} />
                  <Typography variant="body1">
                    <strong>Household Size:</strong> {unit.household.size} people
                  </Typography>
                </Box>
              </Box>
            </Grid>

            {/* Financial Information */}
            <Grid item xs={12} md={4} component="div">
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Financial Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountBalanceWalletIcon sx={{ color: colors.info }} />
                  <Typography variant="body1">
                    <strong>Monthly Income:</strong> ${unit.household.income.toLocaleString()}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountBalanceWalletIcon sx={{ color: colors.info }} />
                  <Typography variant="body1">
                    <strong>Wealth:</strong> ${unit.household.wealth.toLocaleString()}
                  </Typography>
                </Box>
                {unit.is_owner_occupied && unit.household.monthly_payment && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AccountBalanceWalletIcon sx={{ color: colors.info }} />
                    <Typography variant="body1">
                      <strong>Monthly Payment:</strong> ${unit.household.monthly_payment.toLocaleString()}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Grid>

            {/* Housing Cost Analysis */}
            <Grid item xs={12} md={4} component="div">
              <Box>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                  {unit.is_owner_occupied ? 'Mortgage Analysis' : 'Rent Burden Analysis'}
                </Typography>
                {unit.is_owner_occupied && unit.household?.mortgage_balance ? (
                  <Box 
                    sx={{ 
                      p: 2, 
                      borderRadius: 2, 
                      backgroundColor: colors.yellowLight,
                      border: `2px solid ${colors.info}`,
                    }}
                  >
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="body1">
                        <strong>Mortgage Balance:</strong> ${unit.household.mortgage_balance.toLocaleString()}
                      </Typography>
                      <Typography variant="body1">
                        <strong>Interest Rate:</strong> {(unit.household.mortgage_interest_rate || 0) * 100}%
                      </Typography>
                      <Typography variant="body1">
                        <strong>Term:</strong> {unit.household.mortgage_term} years
                      </Typography>
                      <Typography variant="body1">
                        <strong>Monthly Payment:</strong> ${unit.household.monthly_payment?.toLocaleString()}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          Mortgage Progress
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={100 - (unit.household.mortgage_balance / (unit.household.monthly_payment || 1) / (unit.household.mortgage_term || 30) / 12 * 100)} 
                          sx={{ 
                            height: 8, 
                            borderRadius: 4,
                            backgroundColor: '#e0e0e0',
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: colors.info,
                              borderRadius: 4,
                            }
                          }} 
                        />
                      </Box>
                    </Box>
                  </Box>
                ) : (
                  <Box 
                    sx={{ 
                      p: 2, 
                      borderRadius: 2, 
                      backgroundColor: isAffordable ? '#e8f5e8' : '#ffebee',
                      border: `2px solid ${isAffordable ? colors.success : colors.vacant}`,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {isAffordable ? 
                        <CheckCircleIcon sx={{ color: colors.success }} /> : 
                        <WarningIcon sx={{ color: colors.vacant }} />
                      }
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {currentRentBurden.toFixed(1)}% of income
                      </Typography>
                    </Box>
                    <Typography variant="body2">
                      {isAffordable ? 
                        'Within recommended 30% threshold' : 
                        'Above recommended 30% threshold'
                      }
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.min(currentRentBurden, 100)} 
                      sx={{ 
                        mt: 1, 
                        height: 8, 
                        borderRadius: 4,
                        backgroundColor: '#e0e0e0',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: isAffordable ? colors.success : colors.vacant,
                          borderRadius: 4,
                        }
                      }} 
                    />
                  </Box>
                )}
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Analytics Overview */}
      {analytics && (
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" sx={{ mb: 3, fontWeight: 600, color: colors.textDark }}>
            Performance Analytics
          </Typography>
          <Grid container spacing={3} component="div">
            <Grid item xs={12} sm={6} md={6} component="div">
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: colors.info }}>
                  {analytics.avgOccupancy.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">Average Occupancy</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={6} component="div">
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: colors.success }}>
                  ${analytics.totalRevenue.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {unit.is_owner_occupied ? 'Property Value' : 'Total Revenue'}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Event Log */}
      <EventLog 
        unitId={unit.id}
        events={frame?.events || []}
        moves={frame?.moves || []}
        period={frame?.period || 0}
        isOccupied={unit.is_occupied}
        currentHousehold={unit.household}
      />
    </Container>
  );
};

export default PropertyDetailPage; 