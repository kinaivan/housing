import React from 'react';
import { Paper, Typography, Box, Stack } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import BuildIcon from '@mui/icons-material/Build';
import WarningIcon from '@mui/icons-material/Warning';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';
import GroupIcon from '@mui/icons-material/Group';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import GroupRemoveIcon from '@mui/icons-material/GroupRemove';
import NoMeetingRoomIcon from '@mui/icons-material/NoMeetingRoom';

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

interface EventLogProps {
  events: Event[];
  policyMetrics?: {
    total_lvt_collected?: number;
    violations_found?: number;
    improvements_required?: number;
    lvt_rate?: number;
  };
  year: number;
  period: number;
}

const EventLog: React.FC<EventLogProps> = ({ events = [], policyMetrics, year, period }) => {
  // Count actual events
  const hasEvents = 
    events.length > 0 || 
    (policyMetrics?.violations_found ?? 0) > 0 ||
    (policyMetrics?.improvements_required ?? 0) > 0 ||
    (policyMetrics?.total_lvt_collected ?? 0) > 0;

  // Debug log
  console.log('EventLog props:', { events, policyMetrics, hasEvents });

  const renderEvent = (event: Event) => {
    switch (event.type) {
      case 'MOVE':
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PersonIcon sx={{ color: colors.info }} />
            <Typography variant="body2">
              {event.household_name} moved from unit {event.from_unit_id} to unit {event.to_unit_id}
            </Typography>
          </Box>
        );
      
      case 'MOVE_IN':
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HomeIcon sx={{ color: colors.occupied }} />
            <Typography variant="body2">
              {event.household_name} moved into unit {event.to_unit_id}
            </Typography>
          </Box>
        );

      case 'MOVE_OUT':
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <NoMeetingRoomIcon sx={{ color: colors.vacant }} />
            <Typography variant="body2">
              {event.household_name} moved out of unit {event.from_unit_id}
            </Typography>
          </Box>
        );

      case 'EVICTED':
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon sx={{ color: colors.warning }} />
            <Typography variant="body2">
              {event.household_name} was evicted from unit {event.from_unit_id} 
              ({event.reason}{`, rent burden: ${Math.round(((event.rent_burden ?? 0) * 100))}%`})
            </Typography>
          </Box>
        );

      case 'HOUSEHOLD_BREAKUP':
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <GroupRemoveIcon sx={{ color: colors.warning }} />
            <Typography variant="body2">
              Household split in unit {event.from_unit_id}: {event.original_size} → {event.remaining_size} + {event.new_household_size} people
            </Typography>
          </Box>
        );

      case 'HOUSEHOLD_MERGER':
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <GroupAddIcon sx={{ color: colors.occupied }} />
            <Typography variant="body2">
              Households merged in unit {event.from_unit_id}: {event.original_size} + {event.other_household_size} → {event.combined_size} people
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Paper sx={{ p: 2, mt: 3, backgroundColor: colors.white }}>
      <Typography variant="h6" sx={{ mb: 2, color: colors.textDark }}>
        Events Log - Year {year}, Period {period}
      </Typography>
      
      <Stack spacing={1}>
        {/* Events */}
        {events.map((event, index) => (
          <React.Fragment key={index}>
            {renderEvent(event)}
          </React.Fragment>
        ))}

        {/* Policy Events */}
        {policyMetrics && (
          <>
            {(policyMetrics.violations_found ?? 0) > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon sx={{ color: colors.warning }} />
                <Typography variant="body2">
                  {policyMetrics.violations_found} housing violations found
                </Typography>
              </Box>
            )}
            
            {(policyMetrics.improvements_required ?? 0) > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BuildIcon sx={{ color: colors.occupied }} />
                <Typography variant="body2">
                  {policyMetrics.improvements_required} units required improvements
                </Typography>
              </Box>
            )}

            {(policyMetrics.total_lvt_collected ?? 0) > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountBalanceIcon sx={{ color: colors.info }} />
                <Typography variant="body2">
                  ${Math.round((policyMetrics.total_lvt_collected || 0)).toLocaleString()} collected in Land Value Tax
                </Typography>
              </Box>
            )}
          </>
        )}

        {/* No Events Message */}
        {!hasEvents && (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            No events this period
          </Typography>
        )}
      </Stack>
    </Paper>
  );
};

export default EventLog; 