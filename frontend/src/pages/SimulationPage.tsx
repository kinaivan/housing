import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  ButtonGroup,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import HousingGrid from '../components/HousingGrid';
import useSimulation from '../hooks/useSimulation';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700', // Golden yellow
  yellowLight: '#FFF4B8',   // Light yellow
  yellowDark: '#FFC000',    // Dark yellow
  textDark: '#2C2C2C',     // Dark text
  white: '#FFFFFF',        // Pure white
};

// Custom Timeline component
function Timeline({ 
  currentStep, 
  totalSteps, 
  currentYear, 
  currentPeriod 
}: { 
  currentStep: number; 
  totalSteps: number;
  currentYear: number;
  currentPeriod: number;
}) {
  // Create markers for every 5 years (10 steps)
  const markers = Array.from({ length: 7 }, (_, i) => i * 5);
  
  // Calculate the actual step (0-based) and ensure it only increases
  const actualStep = Math.max(0, ((currentYear - 1) * 2) + (currentPeriod - 1));
  const fillPercentage = Math.min(100, (actualStep / totalSteps) * 100);
  
  return (
    <Box sx={{ width: '100%', mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Year {currentYear} of 30, Period {currentPeriod}
        </Typography>
      </Box>
      <Box sx={{ position: 'relative', height: '40px', mb: 1 }}>
        {/* Background track */}
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            transform: 'translateY(-50%)',
            width: '100%',
            height: '8px',
            backgroundColor: colors.yellowLight,
            borderRadius: '4px',
          }}
        />
        {/* Progress bar */}
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            transform: 'translateY(-50%)',
            width: `${fillPercentage}%`,
            height: '8px',
            backgroundColor: colors.yellowDark,
            borderRadius: '4px',
            transition: 'width 2s ease-in-out',
          }}
        />
        {/* Year markers */}
        {markers.map((year) => (
          <Box
            key={year}
            sx={{
              position: 'absolute',
              left: `${(year / 30) * 100}%`,
              top: 0,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: 'translateX(-50%)',
            }}
          >
            <Box
              sx={{
                width: '2px',
                height: '12px',
                backgroundColor: colors.textDark,
                opacity: 0.3,
                mb: 0.5,
              }}
            />
            <Typography variant="caption" color="text.secondary">
              Year {year}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

function StatCard({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        backgroundColor: colors.white,
      }}
    >
      <Typography variant="h6" gutterBottom color={colors.textDark}>
        {title}
      </Typography>
      <Typography variant="h4" color="primary" sx={{ mb: 1 }}>
        {value}
      </Typography>
      {subtitle && (
        <Typography variant="body2" color="text.secondary">
          {subtitle}
        </Typography>
      )}
    </Paper>
  );
}

function SimulationPage() {
  const [rentCapEnabled, setRentCapEnabled] = useState(false);
  const {
    units,
    stats,
    isRunning,
    isPaused,
    error,
    status,
    currentYear,
    currentPeriod,
    startSimulation,
    pauseSimulation,
    resumeSimulation,
    resetSimulation,
  } = useSimulation();

  // Calculate current step (0-based)
  const totalSteps = 60; // 30 years * 2 periods per year
  const currentStep = ((currentYear - 1) * 2) + (currentPeriod - 1);

  // Start simulation automatically when the page loads
  useEffect(() => {
    if (status === 'idle') {
      startSimulation({ 
        rent_cap_enabled: rentCapEnabled,
        years: 30
      });
    }
  }, [status, startSimulation, rentCapEnabled]);

  const handlePlayPause = () => {
    if (isPaused) {
      resumeSimulation();
    } else if (isRunning) {
      pauseSimulation();
    } else {
      startSimulation({ 
        rent_cap_enabled: rentCapEnabled,
        years: 30
      });
    }
  };

  const handleRentCapToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRentCapEnabled(event.target.checked);
    if (isRunning || isPaused) {
      resetSimulation();
      setTimeout(() => {
        startSimulation({ 
          rent_cap_enabled: event.target.checked,
          years: 30
        });
      }, 500);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Hero Section */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom color={colors.textDark}>
          Housing Market Simulation
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Watch how housing units evolve over time (6-month intervals)
        </Typography>

        {/* Timeline */}
        {isRunning && (
          <Timeline 
            currentStep={((currentYear - 1) * 2) + (currentPeriod - 1)} 
            totalSteps={60}
            currentYear={currentYear}
            currentPeriod={currentPeriod}
          />
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <ButtonGroup variant="contained" size="large">
            <Button
              onClick={handlePlayPause}
              startIcon={isPaused || !isRunning ? <PlayArrowIcon /> : <PauseIcon />}
              disabled={status === 'error'}
              sx={{
                backgroundColor: colors.yellowDark,
                '&:hover': {
                  backgroundColor: colors.yellowPrimary,
                },
              }}
            >
              {status === 'paused' ? 'Resume' : (isRunning ? 'Pause' : 'Start')}
            </Button>
            <Button
              onClick={resetSimulation}
              startIcon={<RestartAltIcon />}
              disabled={status === 'error'}
              sx={{
                backgroundColor: colors.yellowDark,
                '&:hover': {
                  backgroundColor: colors.yellowPrimary,
                },
              }}
            >
              Reset
            </Button>
          </ButtonGroup>
          <FormControlLabel
            control={
              <Switch
                checked={rentCapEnabled}
                onChange={handleRentCapToggle}
                color="primary"
              />
            }
            label={`Rent Cap Policy: ${rentCapEnabled ? 'Enabled' : 'Disabled'}`}
          />
        </Box>
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {status === 'running' && units.length === 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Statistics Grid */}
      <Box 
        sx={{ 
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(4, 1fr)',
          },
          gap: 3,
          mb: 4,
        }}
      >
        <StatCard 
          title="Total Units" 
          value={stats.totalUnits}
          subtitle="Available Housing Units"
        />
        <StatCard 
          title="Occupied Units" 
          value={stats.occupiedUnits}
          subtitle={`${Math.round((stats.occupiedUnits / stats.totalUnits) * 100)}% Occupancy Rate`}
        />
        <StatCard 
          title="Average Rent" 
          value={`$${stats.averageRent}`}
          subtitle="Per Month"
        />
        <StatCard 
          title="Total Residents" 
          value={stats.totalResidents}
          subtitle="People Housed"
        />
      </Box>

      {/* Housing Grid */}
      {units.length > 0 && (
        <HousingGrid units={units} />
      )}
    </Container>
  );
}

export default SimulationPage; 