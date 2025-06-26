import React from 'react';
import { Box, Paper, Typography, Tooltip } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700',
  yellowLight: '#FFF4B8',
  yellowDark: '#FFC000',
  textDark: '#2C2C2C',
  white: '#FFFFFF',
  occupied: '#28a745',
  vacant: '#dc3545',
};

interface HouseProps {
  occupants: number;
  id: number;
  rent: number;
  is_occupied: boolean;
}

const House: React.FC<HouseProps> = ({ occupants, id, rent, is_occupied }) => {
  // Create an array of occupant icons based on the number of occupants
  const occupantIcons = Array(occupants).fill(null).map((_, index) => (
    <PersonIcon 
      key={`${id}-occupant-${index}`}
      sx={{ 
        fontSize: '16px',
        color: colors.textDark,
        marginRight: '2px'
      }}
    />
  ));

  return (
    <Tooltip 
      title={`Unit ${id + 1}: ${is_occupied ? 'Occupied' : 'Vacant'}
Rent: $${rent}
${occupants} resident${occupants !== 1 ? 's' : ''}`}
      arrow
    >
      <Paper
        elevation={3}
        sx={{
          p: 2,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1,
          backgroundColor: colors.white,
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'scale(1.05)',
          },
        }}
      >
        <HomeIcon 
          sx={{ 
            fontSize: '40px',
            color: is_occupied ? colors.occupied : colors.vacant,
          }}
        />
        
        {/* Occupants row */}
        <Box 
          sx={{ 
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: 0.5,
            minHeight: '24px'
          }}
        >
          {occupantIcons}
        </Box>

        {/* Rent display */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <AttachMoneyIcon sx={{ fontSize: '16px', color: colors.textDark }} />
          <Typography variant="body2" color={colors.textDark}>
            {rent}
          </Typography>
        </Box>
      </Paper>
    </Tooltip>
  );
};

interface HousingGridProps {
  units: Array<{
    id: number;
    occupants: number;
    rent: number;
    is_occupied: boolean;
  }>;
}

const HousingGrid: React.FC<HousingGridProps> = ({ units }) => {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: 'repeat(2, 1fr)',
          sm: 'repeat(3, 1fr)',
          md: 'repeat(4, 1fr)',
          lg: 'repeat(5, 1fr)',
          xl: 'repeat(6, 1fr)',
        },
        gap: 3,
        p: 3,
      }}
    >
      {units.map((unit) => (
        <House
          key={unit.id}
          id={unit.id}
          occupants={unit.occupants}
          rent={unit.rent}
          is_occupied={unit.is_occupied}
        />
      ))}
    </Box>
  );
};

export default HousingGrid; 