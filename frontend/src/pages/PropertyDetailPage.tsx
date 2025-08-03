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
}>;

// Theme colors
const colors = {
  yellowPrimary: '#FFD700',
  yellowLight: '#FFF4B8',
  yellowDark: '#FFC000',
  textDark: '#2C2C2C',
  white: '#FFFFFF',
  occupied: '#28a745',
  vacant: '#dc3545',
  warning: '#ff9800',
  info: '#2196f3',
  success: '#4caf50',
};

interface Unit {
  id: number;
  occupants: number;
  rent: number;
  is_occupied: boolean;
  quality?: number;
  lastRenovation?: number;
  household?: {
    income: number;
    satisfaction: number;
    size: number;
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

        const rentBurden = unit.household ? ((unit.rent * 12) / unit.household.income * 100) : 0;
        
        // Ensure satisfaction is a valid number
        let satisfaction = 0;
        if (unit.household?.satisfaction !== undefined && unit.household?.satisfaction !== null) {
          satisfaction = Math.max(0, Math.min(1, unit.household.satisfaction)) * 100;
        }
        
        const newEntry: UnitHistoryEntry = {
          period: frame.period,
          occupants: unit.occupants,
          rent: unit.rent,
          occupancyRate: unit.is_occupied ? 100 : 0,
          quality: (unit.quality || 0) * 100,
          satisfaction: satisfaction,
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

  const currentRentBurden = unit.household ? ((unit.rent * 12) / unit.household.income * 100) : 0;
  const isAffordable = currentRentBurden <= 30;
  const qualityScore = (unit.quality || 0) * 100;
  const satisfactionScore = unit.household?.satisfaction !== undefined ? unit.household.satisfaction * 100 : 0;

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
        <HomeIcon sx={{ fontSize: 40, color: unit.is_occupied ? colors.occupied : colors.vacant }} />
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 'bold', color: colors.textDark }}>
            Property #{unit.id}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
            <Chip 
              label={unit.is_occupied ? 'Occupied' : 'Vacant'}
              sx={{ 
                backgroundColor: unit.is_occupied ? colors.occupied : colors.vacant,
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

      {/* Key Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Monthly Rent"
            value={`$${unit.rent.toLocaleString()}`}
            icon={<AttachMoneyIcon />}
            subtitle="Current rate"
            trend={analytics && analytics.rentGrowth > 0 ? 'up' : analytics && analytics.rentGrowth < 0 ? 'down' : 'neutral'}
            color={colors.info}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Occupants"
            value={unit.occupants}
            icon={<PersonIcon />}
            subtitle={unit.is_occupied ? `${unit.household?.size || 0} person household` : 'Vacant'}
            color={colors.occupied}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Quality Score"
            value={`${qualityScore.toFixed(0)}%`}
            icon={<StarIcon />}
            subtitle={unit.lastRenovation ? `Renovated ${unit.lastRenovation} months ago` : 'Never renovated'}
            color={colors.warning}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
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
            Current Residents
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountBalanceWalletIcon sx={{ color: colors.info }} />
                  <Typography variant="body1">
                    <strong>Annual Income:</strong> ${unit.household.income.toLocaleString()}
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
            <Grid item xs={12} md={6}>
              <Box>
                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                  Rent Burden Analysis
                </Typography>
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
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: colors.info }}>
                  {analytics.avgOccupancy.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">Average Occupancy</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: colors.success }}>
                  ${analytics.totalRevenue.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">Total Revenue</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    fontWeight: 'bold', 
                    color: analytics.rentGrowth >= 0 ? colors.success : colors.vacant 
                  }}
                >
                  {analytics.rentGrowth >= 0 ? '+' : ''}{analytics.rentGrowth.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">Rent Growth</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: colors.warning }}>
                  {analytics.vacancyRate.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">Vacancy Rate</Typography>
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