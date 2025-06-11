// src/components/FundHoldingsPanel.js
import React from 'react';
import { Box, Typography, Chip, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';

export default function FundHoldingsPanel({ holdings }) {
  const theme = useTheme();
  const softBlue = alpha(theme.palette.primary.main, 0.2);

  return (
    <Box sx={{ mt: 2 }}>
      <Typography
        variant="h6"
        sx={{ color: 'text.primary', mb: 1, pl: 2 }}
      >
        Funds Holding This Security
      </Typography>

      {(!holdings || holdings.length === 0) ? (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: 1, pl: 2 }}
        >
          No fund holdings data available.
        </Typography>
      ) : (
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 1,
            mt: 1,
            pl: 2,
            alignItems: 'center'
          }}
        >
          {holdings.map(h => (
            <Chip
              key={h.fund_name}
              label={h.fund_name}
              sx={{
                bgcolor: softBlue,
                color: theme.palette.text.primary,
                fontWeight: 'bold'
              }}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
