// src/components/TopBar.js
import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

export default function TopBar() {
  return (
    <AppBar position="static" color="primary">
      <Toolbar variant="dense">
        {/* Spacer to push "About" to the right */}
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
      </Toolbar>
    </AppBar>
  );
}
