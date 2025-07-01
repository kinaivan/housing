import { Box, Typography, Grid, Card, CardContent, CardMedia, Chip, Stack } from '@mui/material';
import { House } from '../types';
import { houses } from '../data/houses';
import { colors } from '../theme';
import { formatCurrency } from '../utils/formatters';

interface Props {
  selectedYear: number;
  onSelect: (house: House) => void;
  selectedHouse?: House | null;
}

function HouseCard({ house, isSelected, onSelect }: { house: House; isSelected: boolean; onSelect: (house: House) => void }) {
  return (
    <Card 
      sx={{ 
        height: '100%',
        cursor: 'pointer',
        border: isSelected ? `2px solid ${colors.yellowDark}` : 'none',
        '&:hover': {
          boxShadow: 6,
          transform: 'translateY(-4px)',
          transition: 'all 0.2s ease-in-out',
        },
      }}
      onClick={() => onSelect(house)}
    >
      <CardMedia
        component="img"
        height="200"
        image={house.imageUrl}
        alt={house.name}
      />
      <CardContent>
        <Typography variant="h5" component="h2" gutterBottom color={colors.textDark}>
          {house.name}
        </Typography>
        
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          {house.neighborhood}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          {house.description}
        </Typography>

        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Price
            </Typography>
            <Typography variant="h6" color={colors.textDark}>
              {formatCurrency(house.basePrice)}
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Details
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {house.squareMeters}m² • {house.bedrooms} bed • {house.bathrooms} bath
            </Typography>
          </Box>

          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {house.features.map((feature, index) => (
              <Chip 
                key={index}
                label={feature}
                size="small"
                sx={{ 
                  backgroundColor: colors.yellowLight,
                  color: colors.textDark,
                }}
              />
            ))}
          </Stack>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Rental Yield
            </Typography>
            <Typography variant="body2" color={colors.textDark}>
              {(house.rentalYield * 100).toFixed(1)}%
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function HouseOptionSection({ selectedYear, onSelect, selectedHouse }: Props) {
  // Filter houses based on the selected year
  const availableHouses = houses.filter(
    house => selectedYear >= house.availableFrom && selectedYear <= house.availableTo
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom color={colors.textDark}>
        Available Houses
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary">
        These properties are available for your selected time period ({selectedYear})
      </Typography>

      <Grid container spacing={3}>
        {availableHouses.map((house) => (
          <Grid item component="div" xs={12} sm={6} md={4} key={house.id}>
            <HouseCard
              house={house}
              isSelected={selectedHouse?.id === house.id}
              onSelect={onSelect}
            />
          </Grid>
        ))}
      </Grid>

      {availableHouses.length === 0 && (
        <Typography variant="h6" color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
          No houses available for the selected year ({selectedYear}).
          Please try a different time period.
        </Typography>
      )}
    </Box>
  );
} 