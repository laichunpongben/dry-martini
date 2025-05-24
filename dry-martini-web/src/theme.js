// src/theme.js
import { createTheme } from '@mui/material/styles';

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: { default: '#121212', paper: '#1e1e1e' },
    primary: { main: '#90caf9' },
    text: { primary: '#fff', secondary: '#bbb' },
  },
});