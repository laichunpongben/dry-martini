// src/components/SummaryPanel.js
import React from 'react';
import { Box, Typography } from '@mui/material';

export default function SummaryPanel({ summary }) {
  return (
    <Box sx={{ mt: 2, mb: 2 }}>
      <Typography
        variant="h6"
        sx={{ color: 'text.primary', mb: 1, pl: 2 }}
      >
        Summary
      </Typography>
      <Typography
        variant="body1"
        sx={{ color: 'text.secondary', pl: 2, whiteSpace: 'pre-wrap' }}
      >
        {summary || 'No summary available.'}
      </Typography>
    </Box>
  );
}