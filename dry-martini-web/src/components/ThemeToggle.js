// src/components/ThemeToggle.js
import React from 'react';
import { styled } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Switch from '@mui/material/Switch';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

const ToggleContainer = styled(Box)({
  position: 'relative',
  display: 'inline-flex',
  alignItems: 'center',
});

const IconWrapper = styled(Box)({
  position: 'absolute',
  top: '50%',
  transform: 'translateY(-50%)',
  pointerEvents: 'none',
});

export default function ThemeToggle({ themeMode, toggleTheme }) {
  return (
    <ToggleContainer sx={{ width: 48 }}>
      <IconWrapper sx={{ left: 4 }}>
        <Brightness7Icon fontSize="small" />
      </IconWrapper>
      <Switch
        checked={themeMode === 'dark'}
        onChange={toggleTheme}
        color="default"
        size="small"
      />
      <IconWrapper sx={{ right: 4 }}>
        <Brightness4Icon fontSize="small" />
      </IconWrapper>
    </ToggleContainer>
  );
}
