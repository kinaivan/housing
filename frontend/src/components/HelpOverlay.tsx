import React from 'react';
import {
  Drawer,
  IconButton,
  Typography,
  Box,
  useTheme,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

interface HelpOverlayProps {
  open: boolean;
  onClose: () => void;
}

const HelpOverlay: React.FC<HelpOverlayProps> = ({ open, onClose }) => {
  const theme = useTheme();

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: '50%',
          maxWidth: '800px',
          p: 3,
          bgcolor: theme.palette.background.paper,
        },
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" component="h2">
          How It Works
        </Typography>
        <IconButton onClick={onClose} size="large">
          <CloseIcon />
        </IconButton>
      </Box>
      
      <Divider sx={{ mb: 3 }} />

      <Box sx={{ overflow: 'auto', pr: 2 }}>
        <Typography variant="h6" gutterBottom>
          Simulation Loop
        </Typography>
        <Typography paragraph>
          The simulation models a housing market where households make decisions about where to live based on their income,
          wealth, and preferences. Landlords manage properties and set rents, while policies can influence market behavior.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Key Equations
        </Typography>
        
        <Typography variant="subtitle1" gutterBottom>
          Household Decisions
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText 
              primary="Rent Burden = Monthly Rent / Monthly Income"
              secondary="Above 40%: High risk of moving, Above 50%: Risk of eviction"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Wealth Trend = (Current Wealth - Initial Wealth) / Initial Wealth"
              secondary="Negative trend increases probability of seeking cheaper housing"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Satisfaction = Quality Score × (1 - Rent Burden Penalty)"
              secondary="Below 0.5: Likely to consider moving"
            />
          </ListItem>
        </List>

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
          Landlord Behavior
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText 
              primary="Base Rent = Market Rate × Quality Factor × Location Multiplier"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Profit = Total Rent - (Maintenance + Tax)"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Quality Decay = -0.1 per year without renovation"
            />
          </ListItem>
        </List>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Policies
        </Typography>
        
        <Typography variant="subtitle1" gutterBottom>
          Land Value Tax (LVT)
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText 
              primary="Tax Amount = Land Value × LVT Rate"
              secondary="Only taxes undeveloped land value, not improvements"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Encourages development and efficient land use"
              secondary="Landlords are incentivized to improve properties rather than speculate on land value"
            />
          </ListItem>
        </List>

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
          Rent Cap Policy
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText 
              primary="Maximum Increase = 10% per year"
              secondary="Limits how much rent can increase for existing tenants"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Inspection Rate = 5% of units per period"
              secondary="Forces improvements when quality falls below 0.4"
            />
          </ListItem>
        </List>

        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Glossary
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText 
              primary="Migration Rate"
              secondary="Probability of new households entering/leaving the market"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Initial Households"
              secondary="Starting number of renters in the simulation"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Quality"
              secondary="Physical condition and amenities of a unit (0-1 scale)"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Market Conditions"
              secondary="External factors affecting prices and demand"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Land Value"
              secondary="Worth of the location, independent of buildings"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Improvement Value"
              secondary="Worth of buildings and renovations"
            />
          </ListItem>
        </List>
      </Box>
    </Drawer>
  );
};

export default HelpOverlay; 