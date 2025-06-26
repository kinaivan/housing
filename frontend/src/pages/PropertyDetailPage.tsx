import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid as MuiGrid,
  Divider,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import useSimulation from '../hooks/useSimulation';

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
}>;

interface Unit {
  id: number;
  occupants: number;
  rent: number;
  is_occupied: boolean;
}

interface UnitHistoryEntry {
  period: number;
  occupants: number;
  rent: number;
}

const PropertyDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { units, frame } = useSimulation();
  const [unitHistory, setUnitHistory] = useState<UnitHistoryEntry[]>([]);
  
  // Convert the URL parameter to a number
  const unitId = Number(id);
  
  // Find the unit with the matching ID
  const unit = units.find(u => u.id === unitId);
  
  // Update history when frame changes
  useEffect(() => {
    if (frame && unit) {
      setUnitHistory(prev => {
        const newEntry = {
          period: frame.period,
          occupants: unit.occupants,
          rent: unit.rent,
        };
        
        // Check if we already have this period
        const exists = prev.some(p => p.period === frame.period);
        if (exists) {
          return prev;
        }
        
        // Add new entry and sort by period
        return [...prev, newEntry].sort((a, b) => a.period - b.period);
      });
    }
  }, [frame, unit]);
  
  if (!unit) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography>Property #{unitId} not found</Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)}>
          Go Back
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Button 
        startIcon={<ArrowBackIcon />} 
        onClick={() => navigate(-1)}
        sx={{ mb: 3 }}
      >
        Back to Simulation
      </Button>

      <Typography variant="h4" gutterBottom>
        Property #{unit.id} Details
      </Typography>

      {/* Current Status */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Current Status</Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              '& > *': {
                borderBottom: '1px solid',
                borderColor: 'divider',
                pb: 2,
                '&:last-child': {
                  borderBottom: 'none',
                },
              },
            }}>
              <Typography>
                Status: {unit.is_occupied ? 'Occupied' : 'Vacant'}
              </Typography>
              <Typography>
                Current Rent: €{unit.rent}
              </Typography>
              <Typography>
                Number of Occupants: {unit.occupants}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Historical Data */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Historical Performance</Typography>
        
        <Typography variant="subtitle1" gutterBottom>Occupancy History</Typography>
        <Box sx={{ width: '100%', height: 300, mb: 2 }}>
          <ResponsiveContainer>
            <LineChart
              data={unitHistory}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="period" 
                label={{ value: 'Period', position: 'bottom' }}
              />
              <YAxis 
                label={{ value: 'Occupants', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Legend />
              <Line
                type="stepAfter"
                dataKey="occupants"
                name="Occupants"
                stroke="#8884d8"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 4 }}>Rent History</Typography>
        <Box sx={{ width: '100%', height: 300, mb: 2 }}>
          <ResponsiveContainer>
            <LineChart
              data={unitHistory}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="period" 
                label={{ value: 'Period', position: 'bottom' }}
              />
              <YAxis 
                label={{ value: 'Rent (€)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="rent"
                name="Rent"
                stroke="#82ca9d"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Container>
  );
};

export default PropertyDetailPage; 