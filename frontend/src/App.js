import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AppProvider } from './contexts/AppContext';
import Layout from './components/Layout';

// Create a custom theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1e3a8a', // Deep blue
    },
    secondary: {
      main: '#2d6b5a', // Teal
    },
    background: {
      default: '#f8fafc',
    },
  },
  typography: {
    fontFamily: "'Poppins', 'Roboto', 'Helvetica', 'Arial', sans-serif",
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        },
      },
    },
  },
});

function App() {
  return (
    <Router>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppProvider>
          <Layout />
        </AppProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;