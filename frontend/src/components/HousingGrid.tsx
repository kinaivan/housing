import React from 'react';
import { Box, Paper, Typography, Tooltip, Chip, Divider, Stack } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import StarIcon from '@mui/icons-material/Star';
import BuildIcon from '@mui/icons-material/Build';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
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

// Custom Tooltip Content Component
const HouseTooltipContent: React.FC<HouseProps> = ({
  id,
  is_occupied,
  quality = 0,
  lastRenovation = 0,
  rent,
  occupants,
  household
}) => {
  const rentBurden = household ? ((rent * 12) / household.income * 100) : 0;
  
  return (
    <Paper 
      elevation={8}
      sx={{ 
        p: 2.5,
        minWidth: 280,
        maxWidth: 320,
        background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
        border: '1px solid rgba(0,0,0,0.12)',
        borderRadius: 2,
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <HomeIcon sx={{ color: is_occupied ? colors.occupied : colors.vacant, fontSize: 24 }} />
        <Typography variant="h6" sx={{ fontWeight: 600, color: colors.textDark }}>
          Unit #{id}
        </Typography>
        <Chip 
          label={is_occupied ? 'Occupied' : 'Vacant'}
          size="small"
          sx={{ 
            ml: 'auto',
            backgroundColor: is_occupied ? colors.occupied : colors.vacant,
            color: 'white',
            fontWeight: 500,
          }}
        />
      </Box>

      {/* Property Details */}
      <Stack spacing={1.5}>
        {/* Quality & Renovation */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StarIcon sx={{ fontSize: 18, color: '#ffa726' }} />
          <Typography variant="body2" sx={{ color: colors.textDark }}>
            <strong>Quality:</strong> {(quality * 100).toFixed(0)}%
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BuildIcon sx={{ fontSize: 18, color: '#66bb6a' }} />
          <Typography variant="body2" sx={{ color: colors.textDark }}>
            <strong>Renovation:</strong> {lastRenovation > 0 ? `${lastRenovation} months ago` : 'Never'}
          </Typography>
        </Box>

        {/* Rent */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AttachMoneyIcon sx={{ fontSize: 18, color: '#42a5f5' }} />
          <Typography variant="body2" sx={{ color: colors.textDark }}>
            <strong>Rent:</strong> ${rent.toLocaleString()}/month
          </Typography>
        </Box>

        <Divider sx={{ my: 1 }} />

        {/* Occupancy Information */}
        {is_occupied ? (
          <Stack spacing={1}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: colors.textDark }}>
              Current Residents
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PersonIcon sx={{ fontSize: 18, color: colors.textDark }} />
              <Typography variant="body2" sx={{ color: colors.textDark }}>
                <strong>People:</strong> {occupants}
              </Typography>
            </Box>

            {household && (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SentimentSatisfiedIcon sx={{ fontSize: 18, color: '#4caf50' }} />
                  <Typography variant="body2" sx={{ color: colors.textDark }}>
                    <strong>Satisfaction:</strong> {((household.satisfaction ?? 0) * 100).toFixed(0)}%
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountBalanceWalletIcon sx={{ fontSize: 18, color: '#9c27b0' }} />
                  <Typography variant="body2" sx={{ color: colors.textDark }}>
                    <strong>Income:</strong> ${household.income?.toLocaleString() ?? 0}/year
                  </Typography>
                </Box>

                <Box 
                  sx={{ 
                    p: 1.5, 
                    borderRadius: 1, 
                    backgroundColor: rentBurden > 30 ? '#ffebee' : '#e8f5e8',
                    border: `1px solid ${rentBurden > 30 ? '#ffcdd2' : '#c8e6c9'}`,
                  }}
                >
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontWeight: 500,
                      color: rentBurden > 30 ? '#c62828' : '#2e7d32',
                    }}
                  >
                    <strong>Rent Burden:</strong> {rentBurden.toFixed(1)}% of income
                    {rentBurden > 30 && (
                      <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                        ⚠️ Above recommended 30%
                      </Typography>
                    )}
                  </Typography>
                </Box>
              </>
            )}
          </Stack>
        ) : (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
              No current residents
            </Typography>
          </Box>
        )}
      </Stack>
    </Paper>
  );
};

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

  // Create an array of occupant icons based on the number of occupants
  const occupantIcons = Array(occupants).fill(null).map((_, index) => (
    <PersonIcon 
      key={`${id}-occupant-${index}`}
      sx={{ 
        fontSize: '14px',
        color: colors.textDark,
        display: 'block',
      }}
    />
  ));

  const handleClick = () => {
    navigate(`/property/${id}`);
  };

  return (
    <Tooltip 
      title={
        <HouseTooltipContent
          id={id}
          occupants={occupants}
          rent={rent}
          is_occupied={is_occupied}
          quality={quality}
          lastRenovation={lastRenovation}
          household={household}
        />
      }
      arrow
      placement="top"
      componentsProps={{
        tooltip: {
          sx: {
            backgroundColor: 'transparent',
            maxWidth: 'none',
          }
        }
      }}
    >
      <Paper
        elevation={3}
        onClick={handleClick}
        sx={{
          p: 2,
          width: '100%',
          height: '160px', // Fixed height for uniform boxes (increased for vertical people)
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between', // Distribute content evenly
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
        
        {/* Occupants column */}
        <Box 
          sx={{ 
            display: 'flex',
            flexDirection: 'column', // Stack people vertically
            justifyContent: 'center',
            alignItems: 'center',
            gap: 0.2,
            height: '60px', // Increased height for vertical stacking
            width: '100%',
            overflow: 'hidden', // Hide overflow if too many occupants
          }}
        >
          {occupants > 6 ? (
            // Show count if too many occupants to display icons vertically
            <Typography variant="body2" color={colors.textDark} sx={{ fontWeight: 'bold' }}>
              {occupants} people
            </Typography>
          ) : (
            occupantIcons
          )}
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
          xs: 'repeat(auto-fit, minmax(130px, 1fr))', // Auto-fit with minimum width
          sm: 'repeat(auto-fit, minmax(150px, 1fr))',
          md: 'repeat(auto-fit, minmax(170px, 1fr))',
        },
        gap: 2,
        p: 3,
        justifyContent: 'center',
        alignItems: 'start',
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