import React, { useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  ButtonGroup,
  Alert,
  CircularProgress,
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
  const {
    units,
    stats,
    isRunning,
    isPaused,
    error,
    status,
    startSimulation,
    pauseSimulation,
    resumeSimulation,
    resetSimulation,
  } = useSimulation();

  // Start simulation automatically when the page loads
  useEffect(() => {
    if (status === 'idle') {
      startSimulation();
    }
  }, [status, startSimulation]);

  const handlePlayPause = () => {
    if (isPaused) {
      resumeSimulation();
    } else if (isRunning) {
      pauseSimulation();
    } else {
      startSimulation();
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
        <ButtonGroup variant="contained" size="large" sx={{ mb: 4 }}>
          <Button
            onClick={handlePlayPause}
            startIcon={isPaused || !isRunning ? <PlayArrowIcon /> : <PauseIcon />}
            disabled={status === 'error'}
          >
            {isPaused || !isRunning ? 'Start' : 'Pause'}
          </Button>
          <Button
            onClick={resetSimulation}
            startIcon={<RestartAltIcon />}
            disabled={status === 'error'}
          >
            Reset
          </Button>
        </ButtonGroup>
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