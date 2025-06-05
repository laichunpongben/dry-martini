// src/components/TopBar.js
import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';
import ThemeToggle from './ThemeToggle';

export default function TopBar({ themeMode, toggleTheme }) {
  return (
    <AppBar position="static" color="primary">
      <Toolbar variant="dense">
        {/* Spacer to push controls to the right */}
        <Box sx={{ flexGrow: 1 }} />

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

        <Tooltip title="Toggle light/dark theme">
          <Box sx={{ ml: 2 }}>
            <ThemeToggle themeMode={themeMode} toggleTheme={toggleTheme} />
          </Box>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
