import React, { useRef, useEffect } from 'react';
import { Box, Paper, Typography, Tooltip, Stack } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import StarIcon from '@mui/icons-material/Star';
import BuildIcon from '@mui/icons-material/Build';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useNavigate } from 'react-router-dom';
import { useSimulation } from '../contexts/SimulationContext';

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

interface Move {
  household_id: number;
  household_name: string;
  from_unit_id: number | null;
  to_unit_id: number | null;
}

interface UnhousedHousehold {
  id: number;
  name: string;
  size: number;
  income: number;
  wealth: number;
}

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

interface Frame {
  year: number;
  period: number;
  units: Unit[];
  metrics: {
    total_units: number;
    occupied_units: number;
    average_rent: number;
    total_population: number;
    policy_metrics?: {
      total_lvt_collected?: number;
      violations_found?: number;
      improvements_required?: number;
      lvt_rate?: number;
    };
  };
  moves?: Array<{
    household_id: number;
    household_name: string;
    from_unit_id: number | null;
    to_unit_id: number | null;
  }>;
  unhoused_households?: Array<{
    id: number;
    name: string;
    size: number;
    income: number;
    wealth: number;
  }>;
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
        {/* Chip component was removed, so this will cause a linter error */}
        {/* <Chip 
          label={is_occupied ? 'Occupied' : 'Vacant'}
          size="small"
          sx={{ 
            ml: 'auto',
            backgroundColor: is_occupied ? colors.occupied : colors.vacant,
            color: 'white',
            fontWeight: 500,
          }}
        /> */}
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

        {/* Divider component was removed, so this will cause a linter error */}
        {/* <Divider sx={{ my: 1 }} /> */}

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

const UnhousedHouseholdCard: React.FC<UnhousedHousehold> = ({ name, size, income, wealth }) => (
  <Paper
    elevation={2}
    sx={{
      p: 1.5,
      mb: 1,
      backgroundColor: colors.yellowLight,
      border: `1px solid ${colors.yellowDark}`,
      width: '100%',
    }}
  >
    <Stack spacing={1}>
      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: colors.textDark }}>
        {name}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <PersonIcon sx={{ fontSize: 16 }} />
        <Typography variant="body2">{size} people</Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AttachMoneyIcon sx={{ fontSize: 16 }} />
        <Typography variant="body2">{Math.round(income).toLocaleString()}/yr</Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AccountBalanceWalletIcon sx={{ fontSize: 16 }} />
        <Typography variant="body2">{Math.round(wealth).toLocaleString()} savings</Typography>
      </Box>
    </Stack>
  </Paper>
);

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
  const { isRunning, isPaused, pauseSimulation } = useSimulation();

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

  const handleClick = async () => {
    // Auto-pause simulation if it's currently running
    if (isRunning && !isPaused) {
      try {
        await pauseSimulation();
        console.log('Simulation auto-paused for property detail view');
      } catch (error) {
        console.error('Failed to auto-pause simulation:', error);
        // Continue navigation even if pause fails
      }
    }
    
    navigate(`/property/${id}`);
  };

  return (
    <Tooltip 
      title={
        <Box>
          <HouseTooltipContent
            id={id}
            occupants={occupants}
            rent={rent}
            is_occupied={is_occupied}
            quality={quality}
            lastRenovation={lastRenovation}
            household={household}
          />
          {isRunning && !isPaused && (
            <Box sx={{ 
              mt: 1, 
              p: 1, 
              backgroundColor: 'rgba(255, 193, 7, 0.9)', 
              borderRadius: 1,
              border: '1px solid #ffc107'
            }}>
              <Typography variant="caption" sx={{ color: '#000', fontWeight: 500 }}>
                💡 Click to pause simulation and view detailed stats
              </Typography>
            </Box>
          )}
        </Box>
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
  const { frame } = useSimulation();
  const gridRef = useRef<HTMLDivElement>(null);
  const moveArrowsRef = useRef<SVGSVGElement>(null);

  // Update move arrows when frame changes
  useEffect(() => {
    if (!frame?.moves || !gridRef.current || !moveArrowsRef.current) return;

    const svg = moveArrowsRef.current;
    const grid = gridRef.current;
    
    // Use requestAnimationFrame to avoid layout thrashing
    const drawArrows = () => {
      // Clear existing arrows
      while (svg.firstChild) {
        svg.removeChild(svg.firstChild);
      }

      // Only draw moves between units (not moves in/out of the system)
      const validMoves = (frame.moves || []).filter(move => 
        move.from_unit_id !== null && move.to_unit_id !== null
      );

      if (validMoves.length === 0) return;

      const gridRect = grid.getBoundingClientRect();

      // Create arrows in a document fragment to minimize DOM updates
      const fragment = document.createDocumentFragment();

      // Add arrow marker definition
      const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
      const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
      marker.setAttribute('id', 'arrowhead');
      marker.setAttribute('markerWidth', '10');
      marker.setAttribute('markerHeight', '7');
      marker.setAttribute('refX', '9');
      marker.setAttribute('refY', '3.5');
      marker.setAttribute('orient', 'auto');
      
      const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
      polygon.setAttribute('fill', '#28a745'); // Green color
      
      marker.appendChild(polygon);
      defs.appendChild(marker);
      fragment.appendChild(defs);

      validMoves.forEach(move => {
        const fromElement = grid.querySelector(`[data-unit-id="${move.from_unit_id}"]`);
        const toElement = grid.querySelector(`[data-unit-id="${move.to_unit_id}"]`);

        if (fromElement && toElement) {
          const fromRect = fromElement.getBoundingClientRect();
          const toRect = toElement.getBoundingClientRect();

          // Calculate arrow points relative to the grid
          const fromX = fromRect.left + fromRect.width / 2 - gridRect.left;
          const fromY = fromRect.top + fromRect.height / 2 - gridRect.top;
          const toX = toRect.left + toRect.width / 2 - gridRect.left;
          const toY = toRect.top + toRect.height / 2 - gridRect.top;

          // Create straight line arrow
          const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          arrow.setAttribute('x1', String(fromX));
          arrow.setAttribute('y1', String(fromY));
          arrow.setAttribute('x2', String(toX));
          arrow.setAttribute('y2', String(toY));
          arrow.setAttribute('stroke', '#28a745'); // Green color
          arrow.setAttribute('stroke-width', '3');
          arrow.setAttribute('marker-end', 'url(#arrowhead)');
          arrow.setAttribute('opacity', '0.8');

          // Add filter for glow effect
          const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
          filter.setAttribute('id', 'glow');
          filter.innerHTML = `
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          `;
          defs.appendChild(filter);

          // Add animation
          arrow.setAttribute('stroke-dasharray', '8,8');
          arrow.setAttribute('class', 'moving-dash');

          // Add both glow and arrow
          //fragment.appendChild(glow);
          fragment.appendChild(arrow);

          // Add household name label at midpoint of the line
          const midX = (fromX + toX) / 2;
          const midY = (fromY + toY) / 2;
          
          const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          text.setAttribute('x', String(midX));
          text.setAttribute('y', String(midY - 10));
          text.setAttribute('text-anchor', 'middle');
          text.setAttribute('fill', '#28a745'); // Green color
          text.setAttribute('font-size', '12px');
          text.textContent = move.household_name;
          
          // Add white background to text for better readability
          const textBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
          const textWidth = text.getComputedTextLength ? text.getComputedTextLength() : 50;
          textBg.setAttribute('x', String(midX - textWidth/2 - 2));
          textBg.setAttribute('y', String(midY - 22));
          textBg.setAttribute('width', String(textWidth + 4));
          textBg.setAttribute('height', '16');
          textBg.setAttribute('fill', 'white');
          textBg.setAttribute('opacity', '0.8');
          
          fragment.appendChild(textBg);
          fragment.appendChild(text);
        }
      });

      // Add all arrows at once
      svg.appendChild(fragment);
    };

    requestAnimationFrame(drawArrows);

    // Cleanup function
    return () => {
      while (svg.firstChild) {
        svg.removeChild(svg.firstChild);
      }
    };
  }, [frame?.moves]);

  return (
    <Box sx={{ display: 'flex', gap: 3, p: 3 }}>
      {/* Unhoused households sidebar - always visible */}
      <Box
        sx={{
          width: 250,
          flexShrink: 0,
          p: 2,
          bgcolor: 'background.paper',
          borderRadius: 1,
          boxShadow: 1,
        }}
      >
        <Typography variant="h6" sx={{ mb: 2, color: colors.textDark }}>
          Looking for Housing ({frame?.unhoused_households?.length || 0})
        </Typography>
        {frame?.unhoused_households && frame.unhoused_households.length > 0 ? (
          <Stack spacing={1}>
            {frame.unhoused_households.map(household => (
              <UnhousedHouseholdCard key={household.id} {...household} />
            ))}
          </Stack>
        ) : (
          <Box sx={{ 
            p: 2, 
            textAlign: 'center', 
            bgcolor: colors.yellowLight,
            borderRadius: 1,
            border: `1px solid ${colors.yellowDark}`
          }}>
            <Typography variant="body2" sx={{ color: colors.textDark }}>
              No households currently looking for housing
            </Typography>
          </Box>
        )}
      </Box>

      {/* Main housing grid with move arrows overlay */}
      <Box sx={{ position: 'relative', flexGrow: 1 }}>
        {/* Legends */}
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          {/* Occupancy Status */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: colors.textDark, mb: 1 }}>
              Occupancy Status
            </Typography>
            <Box sx={{ display: 'flex', gap: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HomeIcon sx={{ color: colors.occupied }} />
                <Typography variant="body2">Occupied</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HomeIcon sx={{ color: colors.vacant }} />
                <Typography variant="body2">Vacant</Typography>
              </Box>
            </Box>
          </Box>

          {/* Quality Indicators */}
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: colors.textDark, mb: 1 }}>
            Property Quality Indicators
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, border: '2px solid #4caf50', borderRadius: 1 }} />
            <Typography variant="body2">Excellent (80-100%)</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, border: '2px solid #8bc34a', borderRadius: 1 }} />
            <Typography variant="body2">Good (60-80%)</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, border: '2px solid #ffeb3b', borderRadius: 1 }} />
            <Typography variant="body2">Fair (40-60%)</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, border: '2px solid #ff9800', borderRadius: 1 }} />
            <Typography variant="body2">Poor (20-40%)</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, border: '2px solid #f44336', borderRadius: 1 }} />
            <Typography variant="body2">Very Poor (0-20%)</Typography>
          </Box>
        </Paper>

        {/* Container for grid and arrows */}
        <Box sx={{ position: 'relative' }}>
          {/* SVG overlay for move arrows */}
          <svg
            ref={moveArrowsRef}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              zIndex: 1,
            }}
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#28a745" />
              </marker>
            </defs>
          </svg>

          {/* Grid */}
          <Box
            ref={gridRef}
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: 'repeat(auto-fit, minmax(130px, 1fr))',
                sm: 'repeat(auto-fit, minmax(150px, 1fr))',
                md: 'repeat(auto-fit, minmax(170px, 1fr))',
              },
              gap: 2,
              position: 'relative',
              zIndex: 0,
            }}
          >
            {units.map((unit) => (
              <Box key={unit.id} data-unit-id={unit.id}>
                <House
                  id={unit.id}
                  occupants={unit.occupants}
                  rent={unit.rent}
                  is_occupied={unit.is_occupied}
                  quality={unit.quality}
                  lastRenovation={unit.lastRenovation}
                  household={unit.household}
                />
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default HousingGrid; 