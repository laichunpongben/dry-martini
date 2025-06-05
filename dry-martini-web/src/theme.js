// src/theme.js
import { createTheme } from '@mui/material/styles';

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    background: { default: '#fafafa', paper: '#fff' },
    primary: { main: '#1976d2' },
    text: { primary: '#000', secondary: '#333' },
  },
});

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: { default: '#121212', paper: '#1e1e1e' },
    primary: { main: '#90caf9' },
    text: { primary: '#fff', secondary: '#bbb' },
  },
});