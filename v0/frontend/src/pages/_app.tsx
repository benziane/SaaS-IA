/**
 * Next.js App Component with MUI Theme
 */
import type { AppProps } from 'next/app';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { SWRConfig } from 'swr';

// Create MUI theme (inspired by Sneat)
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#7367F0',
      light: '#9E95F5',
      dark: '#5E50EE',
    },
    secondary: {
      main: '#A8AAAE',
      light: '#C9CACC',
      dark: '#83858C',
    },
    error: {
      main: '#FF4C51',
    },
    warning: {
      main: '#FFB400',
    },
    info: {
      main: '#16B1FF',
    },
    success: {
      main: '#56CA00',
    },
    background: {
      default: '#F4F5FA',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 600,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 10px 0px rgba(76, 78, 100, 0.22)',
        },
      },
    },
  },
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <SWRConfig
      value={{
        revalidateOnFocus: false,
        revalidateOnReconnect: false,
      }}
    >
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Component {...pageProps} />
      </ThemeProvider>
    </SWRConfig>
  );
}
