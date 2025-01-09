import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  CardActionArea,
  CardActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import useAuth from '../hooks/useAuth';

interface Guild {
  id: string;
  name: string;
  icon_url?: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [guilds, setGuilds] = React.useState<Guild[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetchGuilds();
  }, []);

  const fetchGuilds = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/guilds`, {
        headers: {
          Authorization: `Bearer ${user?.token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch guilds');
      }

      const data = await response.json();
      setGuilds(data);
    } catch (error) {
      console.error('Error fetching guilds:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGuildClick = (guildId: string) => {
    navigate(`/guilds/${guildId}`);
  };

  const handleAddBot = () => {
    window.location.href = `https://discord.com/api/oauth2/authorize?client_id=${
      process.env.REACT_APP_DISCORD_CLIENT_ID
    }&permissions=8&scope=bot%20applications.commands`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        Loading...
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Your Servers
      </Typography>
      <Grid container spacing={3}>
        {guilds.map((guild) => (
          <Grid item xs={12} sm={6} md={4} key={guild.id}>
            <Card>
              <CardActionArea onClick={() => handleGuildClick(guild.id)}>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    {guild.icon_url ? (
                      <img
                        src={guild.icon_url}
                        alt={guild.name}
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: '50%',
                          marginRight: 16,
                        }}
                      />
                    ) : (
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: '50%',
                          backgroundColor: 'primary.main',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginRight: 2,
                        }}
                      >
                        {guild.name.charAt(0)}
                      </Box>
                    )}
                    <Typography variant="h6">{guild.name}</Typography>
                  </Box>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Box display="flex" flexDirection="column" alignItems="center">
                        <CodeIcon color="primary" />
                        <Typography variant="body2">Commands</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box display="flex" flexDirection="column" alignItems="center">
                        <SecurityIcon color="primary" />
                        <Typography variant="body2">AutoMod</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box display="flex" flexDirection="column" alignItems="center">
                        <SettingsIcon color="primary" />
                        <Typography variant="body2">Settings</Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </CardActionArea>
              <CardActions>
                <Button size="small" color="primary">
                  Manage
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
        <Grid item xs={12} sm={6} md={4}>
          <Card
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              p: 3,
              backgroundColor: 'background.paper',
              cursor: 'pointer',
            }}
            onClick={handleAddBot}
          >
            <AddIcon sx={{ fontSize: 48, mb: 2 }} />
            <Typography variant="h6" align="center">
              Add to Another Server
            </Typography>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
