import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Paper,
  Typography,
  useTheme,
} from '@mui/material';
import { Discord as DiscordIcon } from '@mui/icons-material';
import useAuth from '../hooks/useAuth';

const Login: React.FC = () => {
  const theme = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

  useEffect(() => {
    // Handle OAuth callback
    const params = new URLSearchParams(location.search);
    const code = params.get('code');

    if (code) {
      handleOAuthCallback(code);
    }
  }, [location]);

  const handleOAuthCallback = async (code: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/auth/login/discord`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data = await response.json();
      login(data.access_token, data.user);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      // Handle error (show notification, etc.)
    }
  };

  const handleLogin = () => {
    window.location.href = `https://discord.com/api/oauth2/authorize?client_id=${
      process.env.REACT_APP_DISCORD_CLIENT_ID
    }&redirect_uri=${encodeURIComponent(
      process.env.REACT_APP_DISCORD_REDIRECT_URI || ''
    )}&response_type=code&scope=identify%20email%20guilds`;
  };

  if (isAuthenticated) {
    return null; // or loading spinner
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            backgroundColor: theme.palette.background.paper,
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom>
            ArabLife Bot Dashboard
          </Typography>
          <Typography variant="body1" color="textSecondary" align="center" sx={{ mb: 4 }}>
            Manage your Discord server with powerful tools and features
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<DiscordIcon />}
            onClick={handleLogin}
            sx={{
              backgroundColor: '#5865F2',
              '&:hover': {
                backgroundColor: '#4752C4',
              },
            }}
          >
            Login with Discord
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
