import React, { useState } from 'react';
import {
  Container,
  Box,
  Button,
  Typography,
  Slider,
  Paper,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { useSimulation } from '../contexts/SimulationContext';
import HousingGrid from '../components/HousingGrid';
import EventLog from '../components/EventLog';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700',
  yellowLight: '#FFF4B8',
  yellowDark: '#FFC000',
  textDark: '#2C2C2C',
  white: '#FFFFFF',
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
  const yearMarkers = Array.from({ length: Math.ceil(totalSteps / 10) + 1 }, (_, i) => i * 5);
  
  return (
    <Box sx={{ width: '100%', mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Year {currentYear}, Period {currentPeriod}
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

interface SimulationControls {
  initial_households: number;
  migration_rate: number;
  years: number;
  policy_type: 'none' | 'rent_cap' | 'lvt';
  rent_cap_enabled?: boolean;
  lvt_rate?: number;
}

const SimulationPage = () => {
  const { startSimulation, pauseSimulation, resumeSimulation, resetSimulation, frame, isRunning, isPaused, error, currentYear, currentPeriod } = useSimulation();
  const [controls, setControls] = useState<SimulationControls>({
    initial_households: 20,
    migration_rate: 0.1,
    years: 10,
    policy_type: 'none',
    rent_cap_enabled: false,
    lvt_rate: 0.10,
  });

  // Calculate current step (0-based)
  const totalSteps = controls.years * 2; // years * 2 periods per year
  const currentStep = ((currentYear - 1) * 2) + (currentPeriod - 1);

  const handleStart = async () => {
    try {
      const params: any = {
        initial_households: controls.initial_households,
        migration_rate: controls.migration_rate,
        years: controls.years,
      };

      // Add policy-specific parameters
      switch (controls.policy_type) {
        case 'rent_cap':
          params.rent_cap_enabled = true;
          break;
        case 'lvt':
          params.lvt_enabled = true;
          params.lvt_rate = controls.lvt_rate;
          break;
        default:
          // No policy parameters needed
          break;
      }

      await startSimulation(params);
    } catch (error) {
      console.error('Failed to start simulation:', error);
    }
  };

  const handlePolicyChange = (event: any) => {
    setControls(prev => ({
      ...prev,
      policy_type: event.target.value,
    }));
  };

  const eventsToShow = frame ? (
    (frame.events && frame.events.length > 0)
      ? frame.events
      : (frame.moves || []).map(m => ({ ...m, type: (m as any).type ?? 'MOVE' }))
  ) : [];

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 3, color: colors.textDark }}>
          Housing Market Simulation
        </Typography>

        {/* Simulation Controls */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Stack spacing={3}>
            <Typography variant="h6" sx={{ color: colors.textDark }}>
              Simulation Settings
            </Typography>

            {/* Initial Households */}
            <Box>
              <Typography gutterBottom>Initial Households: {controls.initial_households}</Typography>
              <Slider
                value={controls.initial_households}
                onChange={(_, value) => setControls(prev => ({ ...prev, initial_households: value as number }))}
                min={5}
                max={50}
                step={5}
                disabled={isRunning}
              />
            </Box>

            {/* Migration Rate */}
            <Box>
              <Typography gutterBottom>Migration Rate: {controls.migration_rate}</Typography>
              <Slider
                value={controls.migration_rate}
                onChange={(_, value) => setControls(prev => ({ ...prev, migration_rate: value as number }))}
                min={0}
                max={0.5}
                step={0.05}
                disabled={isRunning}
              />
            </Box>

            {/* Simulation Years */}
            <Box>
              <Typography gutterBottom>Simulation Years: {controls.years}</Typography>
              <Slider
                value={controls.years}
                onChange={(_, value) => setControls(prev => ({ ...prev, years: value as number }))}
                min={1}
                max={20}
                step={1}
                disabled={isRunning}
              />
            </Box>

            {/* Policy Selection */}
            <FormControl fullWidth>
              <InputLabel>Policy Type</InputLabel>
              <Select
                value={controls.policy_type}
                onChange={handlePolicyChange}
                disabled={isRunning}
                label="Policy Type"
              >
                <MenuItem value="none">No Policy</MenuItem>
                <MenuItem value="rent_cap">Rent Cap</MenuItem>
                <MenuItem value="lvt">Land Value Tax (No Property Tax)</MenuItem>
              </Select>
            </FormControl>

            {/* Policy-specific controls */}
            {controls.policy_type === 'lvt' && (
              <Box>
                <Typography gutterBottom>Land Value Tax Rate: {(controls.lvt_rate! * 100).toFixed(1)}%</Typography>
                <Slider
                  value={controls.lvt_rate}
                  onChange={(_, value) => setControls(prev => ({ ...prev, lvt_rate: value as number }))}
                  min={0.05}
                  max={0.20}
                  step={0.01}
                  disabled={isRunning}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${(value * 100).toFixed(1)}%`}
                />
              </Box>
            )}

            {/* Control Buttons */}
            <Stack direction="row" spacing={2}>
              {!isRunning ? (
                <Button
                  variant="contained"
                  startIcon={<PlayArrowIcon />}
                  onClick={handleStart}
                  sx={{
                    backgroundColor: colors.yellowPrimary,
                    color: colors.textDark,
                    '&:hover': {
                      backgroundColor: colors.yellowDark,
                    },
                  }}
                >
                  Start Simulation
                </Button>
              ) : (
                <Button
                  variant="contained"
                  startIcon={isPaused ? <PlayArrowIcon /> : <PauseIcon />}
                  onClick={isPaused ? resumeSimulation : pauseSimulation}
                  sx={{
                    backgroundColor: colors.yellowPrimary,
                    color: colors.textDark,
                    '&:hover': {
                      backgroundColor: colors.yellowDark,
                    },
                  }}
                >
                  {isPaused ? 'Resume' : 'Pause'}
                </Button>
              )}
              <Button
                variant="outlined"
                startIcon={<RestartAltIcon />}
                onClick={resetSimulation}
                sx={{
                  borderColor: colors.yellowPrimary,
                  color: colors.textDark,
                  '&:hover': {
                    borderColor: colors.yellowDark,
                    backgroundColor: colors.yellowLight,
                  },
                }}
              >
                Reset
              </Button>
            </Stack>
          </Stack>
        </Paper>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
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

        {/* Simulation Status */}
        {frame?.metrics?.policy_metrics && controls.policy_type === 'lvt' && (
          <Paper sx={{ p: 2, mb: 3, backgroundColor: colors.yellowLight }}>
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" sx={{ color: colors.textDark }}>
                Policy Metrics: LVT Collected: ${Math.round(frame.metrics.policy_metrics.total_lvt_collected ?? 0).toLocaleString()},
                Improvements Required: {frame.metrics.policy_metrics.improvements_required ?? 0}
              </Typography>
            </Box>
          </Paper>
        )}

        {/* Housing Grid */}
        <HousingGrid units={frame?.units || []} />

        {/* Event Log */}
        {frame && (
          <EventLog
            events={eventsToShow as any}
            policyMetrics={frame.metrics.policy_metrics}
            year={frame.year}
            period={frame.period}
          />
        )}
      </Box>
    </Container>
  );
};

export default SimulationPage; 