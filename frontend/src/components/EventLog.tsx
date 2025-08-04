import React from 'react';
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  Grid,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import BuildIcon from '@mui/icons-material/Build';
import GroupsIcon from '@mui/icons-material/Groups';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import { formatCurrency } from '../utils/formatters';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700',
  yellowLight: '#FFF4B8',
  yellowDark: '#FFC000',
  textDark: '#2C2C2C',
  white: '#FFFFFF',
  occupied: '#28a745',
  vacant: '#dc3545',
  warning: '#ff9800',
  info: '#2196f3',
  success: '#4caf50',
};

interface Event {
  type: string;
  household_id: number;
  household_name: string;
  from_unit_id?: number;
  to_unit_id?: number;
  reason?: string;
  rent_burden?: number;
  original_size?: number;
  remaining_size?: number;
  new_household_id?: number;
  new_household_size?: number;
  other_household_id?: number;
  other_household_size?: number;
  combined_size?: number;
  age?: number;
  life_stage?: string;
  income?: number;
  wealth?: number;
  satisfaction?: number;
  unit_id?: number;
  household_size?: number;  // For migration events
  was_housed?: boolean;     // For departure events
}

interface Move {
  household_id: number;
  household_name: string;
  from_unit_id: number | null;
  to_unit_id: number | null;
  type?: string;
  reason?: string;
  rent_burden?: number;
  remaining_size?: number;
  combined_size?: number;
  life_stage?: string;
}

interface EventLogProps {
  unitId: number;
  events: Event[];
  moves: Move[];
  period: number;
  isOccupied: boolean;
  currentHousehold?: {
    id: number;
    name: string;
    age: number;
    size: number;
    income: number;
    wealth: number;
    satisfaction: number;
    life_stage: string;
    monthly_payment?: number;
    mortgage_balance?: number;
    mortgage_interest_rate?: number;
    mortgage_term?: number;
  };
}

// Helper function to format life stage
const formatLifeStage = (stage: string) => {
  return stage
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const EventLog: React.FC<EventLogProps> = ({ 
  unitId, 
  events, 
  moves, 
  period,
  isOccupied,
  currentHousehold
}) => {
  // Filter events and moves relevant to this unit
  const relevantEvents = events?.filter(event => 
    event.from_unit_id === unitId || event.to_unit_id === unitId ||
    // Include events that happened while the household was in this unit
    (event.type === 'rent_adjustment' && event.unit_id === unitId) ||
    (event.type === 'renovation' && event.unit_id === unitId)
  ) || [];

  const relevantMoves = moves?.filter(move => 
    move.from_unit_id === unitId || move.to_unit_id === unitId
  ) || [];

  // Combine and sort all events chronologically
  const allEvents = [...relevantEvents, ...relevantMoves]
    .sort((a, b) => {
      // Sort by period if available, otherwise maintain relative order
      const periodA = (a as any).period || 0;
      const periodB = (b as any).period || 0;
      return periodB - periodA;
    });

  const getEventIcon = (event: Event | Move) => {
    if ('type' in event && event.type) {
      switch (event.type) {
        case 'household_split':
          return <GroupsIcon sx={{ color: colors.warning }} />;
        case 'household_merge':
          return <GroupsIcon sx={{ color: colors.success }} />;
        case 'rent_adjustment':
          return <AttachMoneyIcon sx={{ color: colors.info }} />;
        case 'renovation':
          return <BuildIcon sx={{ color: colors.warning }} />;
        default:
          return <PersonIcon sx={{ color: colors.info }} />;
      }
    }
    // Handle moves
    if (event.to_unit_id === unitId) {
      return <ArrowDownwardIcon sx={{ color: colors.success }} />;
    }
    if (event.from_unit_id === unitId) {
      return <ArrowUpwardIcon sx={{ color: colors.vacant }} />;
    }
    return <ArrowForwardIcon sx={{ color: colors.info }} />;
  };

  const getEventDescription = (event: Event | Move) => {
    if ('type' in event && event.type) {
      switch (event.type) {
        case 'HOUSEHOLD_SPLIT':
        case 'HOUSEHOLD_BREAKUP':
        case 'household_split':
        case 'household_breakup':
          if ('original_size' in event) {
            const splitReason = (event.original_size && event.original_size > 4) ? 'found the space too crowded' : 
                               (event.remaining_size === 1) ? 'wanted their own place' : 
                               'decided to go their separate ways';
            const leftBehind = event.new_household_size || ((event.original_size || 0) - (event.remaining_size || 0));
            return `The ${event.household_name} household split up after they ${splitReason}. ${event.remaining_size || 0} members stayed while ${leftBehind} moved out to start fresh elsewhere.`;
          }
          return `The ${event.household_name} household split up and some members moved out to start fresh elsewhere.`;
        
        case 'HOUSEHOLD_MERGE':
        case 'HOUSEHOLD_MERGER':
        case 'household_merge':
        case 'household_merger':
          if ('combined_size' in event) {
            const mergeReason = (event.combined_size && event.combined_size > 4) ? 'pooling resources to afford better housing' :
                               'wanting to live together as a larger family';
            return `The ${event.household_name} family welcomed another household to live with them, ${mergeReason}. Their home now houses ${event.combined_size || 0} people total.`;
          }
          return `The ${event.household_name} family welcomed another household to live with them as a larger family.`;
        
        case 'RENT_ADJUSTMENT':
        case 'rent_adjustment':
          const direction = event.rent_burden && event.rent_burden > 0 ? 'increased' : 'decreased';
          return `Monthly rent was ${direction} to ${formatCurrency(event.rent_burden || 0)} (${Math.abs(event.rent_burden || 0).toFixed(1)}% of income)`;
        
        case 'RENOVATION':
        case 'renovation':
          return 'The property was renovated to improve living conditions';
        
        case 'HOUSING_SEARCH':
          return `${event.household_name} looked at this property but ${event.reason?.toLowerCase() || 'decided not to move in'}`;
        
        case 'MOVE_IN':
          const moveInReason = event.reason ? ` seeking ${event.reason.toLowerCase().replace('better ', '')}` : '';
          return `${event.household_name} moved in as the new resident${moveInReason}`;
        
        case 'MOVE_OUT':
          const reason = event.reason || 'Became Unhoused';
          let moveOutDescription = '';
          
          if (reason === 'Became Unhoused') {
            moveOutDescription = `${event.household_name} had to move out due to financial difficulties and is now looking for affordable housing`;
          } else if (reason.includes('Affordability')) {
            moveOutDescription = `${event.household_name} moved out to find more affordable housing that better fits their budget`;
          } else if (reason.includes('Quality')) {
            moveOutDescription = `${event.household_name} moved out to find better quality housing with improved living conditions`;
          } else if (reason.includes('Size')) {
            moveOutDescription = `${event.household_name} moved out to find a home that better suits their family size`;
          } else if (reason.includes('Location')) {
            moveOutDescription = `${event.household_name} moved out to relocate to a more desirable area`;
          } else {
            moveOutDescription = `${event.household_name} moved out to find a home that better meets their needs`;
          }
          
          return moveOutDescription;
        
        case 'FINANCIAL_STRESS':
          return `${event.household_name} experienced financial difficulties with their housing costs`;
        
        case 'HOME_PURCHASE':
          return `${event.household_name} purchased this property as their new home`;
        
        case 'HOME_SALE':
          return `${event.household_name} sold this property and moved elsewhere`;
        
        case 'LIFE_STAGE_TRANSITION':
          return `${event.household_name} entered a new life stage: ${formatLifeStage(event.life_stage || '')}`;
        
        case 'HOUSEHOLD_ARRIVAL':
          const arrivalSize = ('household_size' in event && event.household_size) ? event.household_size : 
                             ('new_household_size' in event && event.new_household_size) ? event.new_household_size : 'unknown';
          return `${event.household_name} moved into the area as new residents looking for housing (family of ${arrivalSize})`;
        
        case 'HOUSEHOLD_DEPARTURE':
          const wasHousedText = ('was_housed' in event && event.was_housed) ? 'moved away' : 'left the area after being unable to find suitable housing';
          return `${event.household_name} ${wasHousedText} and are no longer part of the local housing market`;
        
        default:
          return `${event.household_name}: ${event.type.toLowerCase().replace(/_/g, ' ')}`;
      }
    }
    
    // Handle moves
    if (event.to_unit_id === unitId) {
      return `${event.household_name} moved in as the new resident`;
    }
    if (event.from_unit_id === unitId) {
      return `${event.household_name} moved out to a different home`;
    }
    return `${event.household_name} relocated to another property`;
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, color: colors.textDark }}>
          Property History
        </Typography>
        <Chip 
          icon={<HomeIcon />}
          label={isOccupied ? 'Currently Occupied' : 'Currently Vacant'}
          sx={{ 
            backgroundColor: isOccupied ? colors.occupied : colors.vacant,
            color: 'white',
            fontWeight: 500,
          }}
        />
      </Box>

      {/* Current Occupants Section */}
      {isOccupied && currentHousehold && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
            Current Residents
          </Typography>
          <Box sx={{ 
            p: 2, 
            backgroundColor: colors.yellowLight, 
            borderRadius: 1,
            border: `1px solid ${colors.yellowDark}`,
          }}>
            <Typography variant="h6" sx={{ mb: 2, color: colors.textDark }}>
              {currentHousehold.name}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">Age & Life Stage</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentHousehold.age} years old
                  </Typography>
                  <Typography variant="body2" sx={{ color: colors.textDark }}>
                    {formatLifeStage(currentHousehold.life_stage)}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">Household Size</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentHousehold.size} people
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">Financial Status</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    Income: {formatCurrency(currentHousehold.income)}/year
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    Wealth: {formatCurrency(currentHousehold.wealth)}
                  </Typography>
                </Box>
                {currentHousehold.mortgage_balance && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">Mortgage Details</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      Balance: {formatCurrency(currentHousehold.mortgage_balance)}
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      Monthly Payment: {formatCurrency(currentHousehold.monthly_payment || 0)}
                    </Typography>
                  </Box>
                )}
              </Box>
              <Box sx={{ width: '100%' }}>
                <Box sx={{ 
                  p: 1.5, 
                  borderRadius: 1, 
                  backgroundColor: currentHousehold.satisfaction >= 0.7 ? '#e8f5e8' : 
                                 currentHousehold.satisfaction >= 0.4 ? '#fff3e0' : '#ffebee',
                  border: `1px solid ${currentHousehold.satisfaction >= 0.7 ? '#c8e6c9' : 
                                    currentHousehold.satisfaction >= 0.4 ? '#ffe0b2' : '#ffcdd2'}`,
                }}>
                  <Typography variant="body2" sx={{ 
                    fontWeight: 500,
                    color: currentHousehold.satisfaction >= 0.7 ? '#2e7d32' : 
                           currentHousehold.satisfaction >= 0.4 ? '#ef6c00' : '#c62828',
                  }}>
                    Satisfaction Level: {(currentHousehold.satisfaction * 100).toFixed(0)}%
                    <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                      {currentHousehold.satisfaction >= 0.7 ? '😊 Very Happy' : 
                       currentHousehold.satisfaction >= 0.4 ? '😐 Moderately Satisfied' : '😟 Unsatisfied'}
                    </Typography>
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
      )}

      <Divider sx={{ my: 2 }} />

      {/* Events List */}
      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
        Event History
      </Typography>
      {allEvents.length > 0 ? (
        <List>
          {allEvents.map((event, index) => (
            <React.Fragment key={index}>
              <ListItem>
                <ListItemIcon>
                  {getEventIcon(event)}
                </ListItemIcon>
                <ListItemText
                  primary={getEventDescription(event)}
                  secondary={`Period ${(event as any).period || period}`}
                />
              </ListItem>
              {index < allEvents.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      ) : (
        <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
          No events recorded yet
        </Typography>
      )}
    </Paper>
  );
};

export default EventLog;