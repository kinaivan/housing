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
  from_unit_id?: number | null;
  to_unit_id?: number | null;
  reason?: string;
  rent_burden?: number;
  original_size?: number;
  remaining_size?: number;
  new_household_id?: number;
  new_household_size?: number;
  other_household_id?: number;
  other_household_size?: number;
  combined_size?: number;
}

interface Move {
  household_id: number;
  household_name: string;
  from_unit_id: number | null;
  to_unit_id: number | null;
  type?: string;
}

interface EventLogProps {
  unitId: number;
  events: Event[];
  moves: Move[];
  period: number;
  isOccupied: boolean;
  currentHousehold?: {
    income: number;
    satisfaction: number;
    size: number;
  };
}

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
        case 'household_split':
          return `Part of the ${event.household_name} family moved out to start their own household (${event.remaining_size} members stayed)`;
        case 'household_merge':
          return `The ${event.household_name} family welcomed new members as households merged into a ${event.combined_size}-person family`;
        case 'rent_adjustment':
          return `Monthly rent was adjusted to ${event.rent_burden?.toFixed(1)}% of the household's income`;
        case 'renovation':
          return 'The property underwent renovations to improve living conditions';
        case 'HOUSING_SEARCH':
          return `The ${event.household_name} family considered moving here - ${event.reason.toLowerCase()}`;
        default:
          return `${event.type} event for the ${event.household_name} family`;
      }
    }
    // Handle moves
    if (event.to_unit_id === unitId) {
      return `The ${event.household_name} family moved in as new residents`;
    }
    if (event.from_unit_id === unitId) {
      return `The ${event.household_name} family found a new home elsewhere`;
    }
    return `The ${event.household_name} family moved to another property`;
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
            <Box sx={{ display: 'flex', gap: 3 }}>
              <Box>
                <Typography variant="body2" color="textSecondary">Household Size</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {currentHousehold.size} people
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">Annual Income</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {formatCurrency(currentHousehold.income)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary">Satisfaction</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {(currentHousehold.satisfaction * 100).toFixed(0)}%
                </Typography>
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
                  secondary={`Period ${(event as any).period || period}${event.reason ? ` - ${event.reason}` : ''}`}
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