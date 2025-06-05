// src/components/ThemeToggle.js
import React from 'react';
import Box from '@mui/material/Box';
import Switch from '@mui/material/Switch';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';

export default function ThemeToggle({ mode, toggleMode }) {
  return (
    <Box sx={{ position: 'relative', ml: 2, mr: 1 }}>
      <LightModeIcon
        sx={{
          position: 'absolute',
          top: '50%',
          left: 4,
          transform: 'translateY(-50%)',
          fontSize: 16,
        }}
      />
      <DarkModeIcon
        sx={{
          position: 'absolute',
          top: '50%',
          right: 4,
          transform: 'translateY(-50%)',
          fontSize: 16,
        }}
      />
      <Switch
        checked={mode === 'dark'}
        onChange={toggleMode}
        size="small"
        sx={{
          width: 40,
          '& .MuiSwitch-switchBase': { p: 0, m: 0 },
          '& .MuiSwitch-thumb': { width: 16, height: 16 },
          '& .MuiSwitch-track': { opacity: 1, px: 3 },
        }}
      />
    </Box>
  );
}
