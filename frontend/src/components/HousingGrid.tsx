import React from 'react';
import { Box, Paper, Typography, Tooltip } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import { useNavigate } from 'react-router-dom';

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
  quality?: number;
  lastRenovation?: number;
  household?: {
    income: number;
    satisfaction: number;
    size: number;
  };
}

const House: React.FC<HouseProps> = ({ 
  occupants, 
  id, 
  rent, 
  is_occupied, 
  quality = 0, 
  lastRenovation = 0,
  household 
}) => {
  const navigate = useNavigate();

  // Calculate rent burden if unit is occupied
  const rentBurden = household ? ((rent * 12) / household.income * 100).toFixed(1) : 0;

  // Format tooltip content
  const tooltipContent = `Unit ${id}: ${is_occupied ? 'Occupied' : 'Vacant'}
Quality: ${(quality * 100).toFixed(0)}%
${lastRenovation > 0 ? `Last Renovation: ${lastRenovation} months ago` : 'Never Renovated'}
Rent: $${rent}/month

${is_occupied ? `Residents: ${occupants}
Tenant Satisfaction: ${(household?.satisfaction ?? 0 * 100).toFixed(0)}%
Household Income: $${household?.income?.toLocaleString() ?? 0}/year
Rent Burden: ${rentBurden}% of income` : 'No Current Residents'}`;

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

  const handleClick = () => {
    navigate(`/property/${id}`);
  };

  return (
    <Tooltip 
      title={tooltipContent}
      arrow
      placement="top"
      sx={{
        '& .MuiTooltip-tooltip': {
          fontSize: '0.875rem',
          whiteSpace: 'pre-line',
        },
      }}
    >
      <Paper
        elevation={3}
        onClick={handleClick}
        sx={{
          p: 2,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1,
          backgroundColor: colors.white,
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          '&:hover': {
            transform: 'scale(1.05)',
            boxShadow: 6,
          },
          // Add quality indicator through border color
          border: '2px solid',
          borderColor: quality >= 0.8 ? '#4caf50' : 
                      quality >= 0.6 ? '#8bc34a' :
                      quality >= 0.4 ? '#ffeb3b' :
                      quality >= 0.2 ? '#ff9800' : '#f44336',
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
    quality?: number;
    lastRenovation?: number;
    household?: {
      income: number;
      satisfaction: number;
      size: number;
    };
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
          quality={unit.quality}
          lastRenovation={unit.lastRenovation}
          household={unit.household}
        />
      ))}
    </Box>
  );
};

export default HousingGrid; 