// src/components/TopBar.js
import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

export default function TopBar({ themeMode, toggleTheme }) {
  return (
    <AppBar position="static" color="primary">
      <Toolbar variant="dense">
        {/* Spacer to push controls to the right */}
        <Box sx={{ flexGrow: 1 }} />

        <Tooltip title="Toggle light/dark theme">
          <IconButton onClick={toggleTheme} color="inherit" sx={{ mr: 1 }}>
            {themeMode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
        </Tooltip>

        <Link
          href="https://about.databookman.com"
          target="_blank"
          rel="noopener noreferrer"
          color="inherit"
          underline="none"
          sx={{ fontWeight: 500 }}
        >
          About
        </Link>
      </Toolbar>
    </AppBar>
  );
}
