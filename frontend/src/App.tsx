import React from 'react';
import { Link as RouterLink, Route, Routes, Navigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  Link,
  CssBaseline,
} from '@mui/material';
import SimulationPage from './pages/SimulationPage';
import LandlordPage from './pages/LandlordPage';
import AboutPage from './pages/AboutPage';
import PropertyDetailPage from './pages/PropertyDetailPage';
import ScenarioPage from './pages/ScenarioPage';
import { SimulationProvider } from './contexts/SimulationContext';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700', // Golden yellow
  yellowLight: '#FFF4B8',   // Light yellow
  yellowDark: '#FFC000',    // Dark yellow
  textDark: '#2C2C2C',     // Dark text
};

function App() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <SimulationProvider>
      <CssBaseline />
      <AppBar 
        position="sticky" 
        sx={{ 
          background: `linear-gradient(145deg, ${colors.yellowPrimary} 0%, ${colors.yellowDark} 100%)`,
          boxShadow: `0 4px 20px rgba(255, 215, 0, 0.15)`,
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: 'bold',
              letterSpacing: '0.5px',
              color: colors.textDark,
              textShadow: '1px 1px 2px rgba(255, 255, 255, 0.5)',
            }}
          >
            Housing Market Simulator
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Link
              component={RouterLink}
              to="/simulation"
              sx={{
                color: colors.textDark,
                textDecoration: 'none',
                borderBottom: isActive('/simulation') || isActive('/') ? `2px solid ${colors.textDark}` : 'none',
                pb: 0.5,
                fontWeight: 500,
                '&:hover': {
                  borderBottom: `2px solid ${colors.textDark}`,
                },
              }}
            >
              Simulation
            </Link>
            <Link
              component={RouterLink}
              to="/landlord"
              sx={{
                color: colors.textDark,
                textDecoration: 'none',
                borderBottom: isActive('/landlord') ? `2px solid ${colors.textDark}` : 'none',
                pb: 0.5,
                fontWeight: 500,
                '&:hover': {
                  borderBottom: `2px solid ${colors.textDark}`,
                },
              }}
            >
              Landlord Calculator
            </Link>
            <Link
              component={RouterLink}
              to="/about"
              sx={{
                color: colors.textDark,
                textDecoration: 'none',
                borderBottom: isActive('/about') ? `2px solid ${colors.textDark}` : 'none',
                pb: 0.5,
                fontWeight: 500,
                '&:hover': {
                  borderBottom: `2px solid ${colors.textDark}`,
                },
              }}
            >
              About
            </Link>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth={false} sx={{ mt: 4 }}>
        <Routes>
          <Route path="/simulation" element={<SimulationPage />} />
          <Route path="/property/:id" element={<PropertyDetailPage />} />
          <Route path="/landlord" element={<LandlordPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/" element={<Navigate to="/simulation" replace />} />
        </Routes>
      </Container>
    </SimulationProvider>
  );
}

export default App; 