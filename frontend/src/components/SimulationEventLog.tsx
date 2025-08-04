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
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import BuildIcon from '@mui/icons-material/Build';
import GroupsIcon from '@mui/icons-material/Groups';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import PersonRemoveIcon from '@mui/icons-material/PersonRemove';

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
  household_size?: number;
  was_housed?: boolean;
}

interface PolicyMetrics {
  total_lvt_collected?: number;
  violations_found?: number;
  improvements_required?: number;
  lvt_rate?: number;
}

interface EventLogProps {
  events: Event[];
  policyMetrics?: PolicyMetrics;
  year: number;
  period: number;
}

const EventLog: React.FC<EventLogProps> = ({ events, policyMetrics, year, period }) => {
  const getEventIcon = (event: Event) => {
    switch (event.type) {
      case 'household_split':
        return <GroupsIcon sx={{ color: colors.warning }} />;
      case 'household_merge':
        return <GroupsIcon sx={{ color: colors.success }} />;
      case 'rent_adjustment':
        return <AttachMoneyIcon sx={{ color: colors.info }} />;
      case 'renovation':
        return <BuildIcon sx={{ color: colors.warning }} />;
      case 'MOVE':
        if (event.to_unit_id !== null && event.from_unit_id === null) {
          return <ArrowDownwardIcon sx={{ color: colors.success }} />;
        }
        if (event.from_unit_id !== null && event.to_unit_id === null) {
          return <ArrowUpwardIcon sx={{ color: colors.vacant }} />;
        }
        return <ArrowForwardIcon sx={{ color: colors.info }} />;
      case 'HOUSEHOLD_ARRIVAL':
        return <PersonAddIcon sx={{ color: colors.success }} />;
      case 'HOUSEHOLD_DEPARTURE':
        return <PersonRemoveIcon sx={{ color: colors.warning }} />;
      default:
        return <PersonIcon sx={{ color: colors.info }} />;
    }
  };

  const getEventDescription = (event: Event) => {
    switch (event.type) {
      case 'HOUSEHOLD_SPLIT':
      case 'HOUSEHOLD_BREAKUP':
      case 'household_split':
      case 'household_breakup':
        const splitReason = (event.original_size && event.original_size > 4) ? 'overcrowding' : 
                           (event.remaining_size === 1) ? 'seeking independence' : 
                           'family changes';
        return `${event.household_name} family split due to ${splitReason} (${event.original_size || 0} → ${event.remaining_size || 0} members)`;
      
      case 'HOUSEHOLD_MERGE':
      case 'HOUSEHOLD_MERGER':
      case 'household_merge':
      case 'household_merger':
        return `${event.household_name} welcomed another family to live together (now ${event.combined_size || 0} people)`;
      
      case 'rent_adjustment':
        return `Rent adjusted for ${event.household_name} (Burden: ${event.rent_burden?.toFixed(1)}%)`;
      
      case 'renovation':
        return `Property ${event.to_unit_id} renovated to improve conditions`;
      
      case 'HOUSING_SEARCH':
        return `${event.household_name} searched for housing - ${event.reason}`;
      
      case 'MOVE':
      case 'MOVE_IN':
      case 'MOVE_OUT':
        if (event.to_unit_id !== null && event.from_unit_id === null) {
          return `${event.household_name} found housing and moved into Unit ${event.to_unit_id}`;
        }
        if (event.from_unit_id !== null && event.to_unit_id === null) {
          const reason = event.reason;
          if (reason === 'Became Unhoused') {
            return `${event.household_name} had to leave Unit ${event.from_unit_id} due to financial difficulties`;
          } else if (reason?.includes('Affordability')) {
            return `${event.household_name} left Unit ${event.from_unit_id} to find more affordable housing`;
          } else {
            return `${event.household_name} moved out of Unit ${event.from_unit_id} seeking better housing`;
          }
        }
        const moveReason = event.reason ? ` seeking ${event.reason.toLowerCase().replace('better ', '')}` : '';
        return `${event.household_name} moved from Unit ${event.from_unit_id} to Unit ${event.to_unit_id}${moveReason}`;
      
      case 'HOUSEHOLD_ARRIVAL':
        return `${event.household_name} arrived in the area as new residents looking for housing (family of ${event.household_size || event.new_household_size || 'unknown'})`;
      
      case 'HOUSEHOLD_DEPARTURE':
        const wasHousedText = event.was_housed ? 'relocated out of the area' : 'left after being unable to find suitable housing';
        return `${event.household_name} ${wasHousedText}`;
      
      default:
        return `${event.household_name}: ${event.type.toLowerCase().replace(/_/g, ' ')}`;
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: colors.textDark }}>
          Event Log
        </Typography>
        <Typography variant="subtitle1" sx={{ color: colors.textDark }}>
          Year {year}, Period {period}
        </Typography>
      </Box>

      {events.length > 0 ? (
        <List>
          {events.map((event, index) => (
            <React.Fragment key={index}>
              <ListItem>
                <ListItemIcon>
                  {getEventIcon(event)}
                </ListItemIcon>
                <ListItemText
                  primary={getEventDescription(event)}
                  secondary={event.reason || `Year ${year}, Period ${period}`}
                />
              </ListItem>
              {index < events.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      ) : (
        <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 2 }}>
          No events in this period
        </Typography>
      )}

      {policyMetrics && (
        <>
          <Divider sx={{ my: 2 }} />
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, color: colors.textDark, mb: 1 }}>
              Policy Metrics
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {policyMetrics.total_lvt_collected !== undefined && (
                <Typography variant="body2">
                  Total LVT Collected: ${Math.round(policyMetrics.total_lvt_collected).toLocaleString()}
                </Typography>
              )}
              {policyMetrics.violations_found !== undefined && (
                <Typography variant="body2">
                  Violations Found: {policyMetrics.violations_found}
                </Typography>
              )}
              {policyMetrics.improvements_required !== undefined && (
                <Typography variant="body2">
                  Improvements Required: {policyMetrics.improvements_required}
                </Typography>
              )}
            </Box>
          </Box>
        </>
      )}
    </Paper>
  );
};

export default EventLog;