// src/components/TopBar.js
import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';

export default function TopBar() {
  return (
    <AppBar position="static" color="primary">
      <Toolbar variant="dense">
        {/* Spacer to maintain layout after removing About link */}
        <Box sx={{ flexGrow: 1 }} />
      </Toolbar>
    </AppBar>
  );
}
