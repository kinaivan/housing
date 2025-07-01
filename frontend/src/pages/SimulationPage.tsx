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
  Slider,
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
  currentPeriod,
}: { 
  currentStep: number; 
  totalSteps: number;
  currentYear: number;
  currentPeriod: number;
}) {
  // Create markers for every 5 years
  const yearMarkers = [0, 5, 10, 15, 20, 25, 30];
  
  return (
    <Box sx={{ width: '100%', mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Year {currentYear} of 30, Period {currentPeriod}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Progress: {Math.round((currentStep / (totalSteps - 1)) * 100)}%
        </Typography>
      </Box>
      <Box sx={{ position: 'relative', height: '60px', mb: 1 }}>
        <Slider
          value={currentStep}
          min={0}
          max={totalSteps - 1}
          step={1}
          marks={yearMarkers.map(year => ({
            value: year * 2, // Each year has 2 periods
            label: `${year}`
          }))}
          disabled
          sx={{
            '& .MuiSlider-rail': {
              backgroundColor: colors.yellowLight,
              height: 8,
            },
            '& .MuiSlider-track': {
              backgroundColor: colors.yellowDark,
              height: 8,
            },
            '& .MuiSlider-thumb': {
              backgroundColor: colors.yellowDark,
              width: 20,
              height: 20,
              '&.Mui-disabled': {
                backgroundColor: colors.yellowDark,
              },
            },
            '& .MuiSlider-mark': {
              backgroundColor: colors.textDark,
              height: 12,
              width: 2,
            },
            '& .MuiSlider-markLabel': {
              fontSize: '0.75rem',
              color: colors.textDark,
            },
          }}
        />
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
  const [isStarting, setIsStarting] = useState(false);
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
    seekToStep
  } = useSimulation();

  // Calculate current step (0-based)
  const totalSteps = 60; // 30 years * 2 periods per year
  const currentStep = ((currentYear - 1) * 2) + (currentPeriod - 1);

  const handlePlayPause = async () => {
    if (isPaused) {
      resumeSimulation();
    } else if (isRunning) {
      pauseSimulation();
    } else if (!isStarting) {
      setIsStarting(true);
      try {
        await startSimulation({ 
          rent_cap_enabled: rentCapEnabled,
          years: 30
        });
      } catch (err) {
        console.error('Failed to start simulation:', err);
      } finally {
        setIsStarting(false);
      }
    }
  };

  const handleReset = async () => {
    try {
      await resetSimulation();
    } catch (err) {
      console.error('Failed to reset simulation:', err);
    }
  };

  const handleRentCapToggle = async (event: React.ChangeEvent<HTMLInputElement>) => {
    setRentCapEnabled(event.target.checked);
    if (isRunning || isPaused) {
      await resetSimulation();
      setTimeout(async () => {
        setIsStarting(true);
        try {
          await startSimulation({ 
            rent_cap_enabled: event.target.checked,
            years: 30
          });
        } catch (err) {
          console.error('Failed to start simulation:', err);
        } finally {
          setIsStarting(false);
        }
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

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}



        {/* Loading State */}
        {isStarting && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Timeline */}
        {(isRunning || isPaused) && (
          <Timeline 
            currentStep={currentStep} 
            totalSteps={totalSteps}
            currentYear={currentYear}
            currentPeriod={currentPeriod}
          />
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <ButtonGroup variant="contained" size="large">
            <Button
              onClick={handlePlayPause}
              startIcon={isPaused || !isRunning ? <PlayArrowIcon /> : <PauseIcon />}
              disabled={status === 'error' || isStarting}
              sx={{
                backgroundColor: colors.yellowDark,
                '&:hover': {
                  backgroundColor: colors.yellowPrimary,
                },
              }}
            >
              {isPaused ? 'Resume' : (isRunning ? 'Pause' : 'Start')}
            </Button>
            <Button
              onClick={handleReset}
              startIcon={<RestartAltIcon />}
              disabled={status === 'error' || isStarting}
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