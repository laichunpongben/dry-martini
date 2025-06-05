// src/components/ThemeToggle.js
import React from 'react';
import Box from '@mui/material/Box';
import Switch from '@mui/material/Switch';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

// Show only the active theme icon next to the switch without overlaying
// to keep the UI clean.

export default function ThemeToggle({ themeMode, toggleTheme }) {
  const isDark = themeMode === 'dark';

  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      {isDark ? (
        <Brightness4Icon fontSize="small" sx={{ mr: 0.5 }} />
      ) : (
        <Brightness7Icon fontSize="small" sx={{ mr: 0.5 }} />
      )}
      <Switch
        checked={isDark}
        onChange={toggleTheme}
        color="default"
        size="small"
      />
    </Box>
  );
}
