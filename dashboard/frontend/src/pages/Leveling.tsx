import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import useAuth from '../hooks/useAuth';

interface LevelingSettings {
  is_enabled: boolean;
  xp_per_message: number;
  xp_cooldown: number;
  level_up_channel_id: string | null;
  level_up_message: string;
  role_rewards: {
    level: number;
    role_id: string;
  }[];
}

interface LeaderboardEntry {
  user_discord_id: string;
  username: string;
  level: number;
  xp: number;
  rank: number;
}

const Leveling: React.FC = () => {
  const { guildId } = useParams<{ guildId: string }>();
  const { user } = useAuth();
  const [settings, setSettings] = React.useState<LevelingSettings>({
    is_enabled: true,
    xp_per_message: 15,
    xp_cooldown: 60,
    level_up_channel_id: null,
    level_up_message: 'Congratulations {user}! You reached level {level}!',
    role_rewards: [],
  });
  const [leaderboard, setLeaderboard] = React.useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [snackbar, setSnackbar] = React.useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error',
  });
  const [newReward, setNewReward] = React.useState({
    level: '',
    role_id: '',
  });

  React.useEffect(() => {
    Promise.all([fetchSettings(), fetchLeaderboard()]).finally(() =>
      setLoading(false)
    );
  }, [guildId]);

  const fetchSettings = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/leveling/${guildId}/settings`,
        {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch leveling settings');
      }

      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching leveling settings:', error);
      showSnackbar('Failed to load settings', 'error');
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/leveling/${guildId}/leaderboard`,
        {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }

      const data = await response.json();
      setLeaderboard(data);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      showSnackbar('Failed to load leaderboard', 'error');
    }
  };

  const handleSave = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/leveling/${guildId}/settings`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${user?.token}`,
          },
          body: JSON.stringify(settings),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      showSnackbar('Settings saved successfully', 'success');
    } catch (error) {
      console.error('Error saving settings:', error);
      showSnackbar('Failed to save settings', 'error');
    }
  };

  const addRoleReward = () => {
    const level = parseInt(newReward.level);
    if (level && newReward.role_id) {
      setSettings({
        ...settings,
        role_rewards: [
          ...settings.role_rewards,
          { level, role_id: newReward.role_id },
        ].sort((a, b) => a.level - b.level),
      });
      setNewReward({ level: '', role_id: '' });
    }
  };

  const removeRoleReward = (level: number) => {
    setSettings({
      ...settings,
      role_rewards: settings.role_rewards.filter((r) => r.level !== level),
    });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Leveling System
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.is_enabled}
                    onChange={(e) =>
                      setSettings({ ...settings, is_enabled: e.target.checked })
                    }
                  />
                }
                label="Enable Leveling System"
              />

              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="XP Per Message"
                    value={settings.xp_per_message}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        xp_per_message: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="XP Cooldown (seconds)"
                    value={settings.xp_cooldown}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        xp_cooldown: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </Grid>
              </Grid>

              <TextField
                fullWidth
                label="Level Up Channel ID"
                value={settings.level_up_channel_id || ''}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    level_up_channel_id: e.target.value,
                  })
                }
                sx={{ mt: 2 }}
              />

              <TextField
                fullWidth
                multiline
                rows={2}
                label="Level Up Message"
                value={settings.level_up_message}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    level_up_message: e.target.value,
                  })
                }
                sx={{ mt: 2 }}
                helperText="Available variables: {user}, {level}, {xp}"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Role Rewards
              </Typography>

              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} md={5}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Level"
                    value={newReward.level}
                    onChange={(e) =>
                      setNewReward({ ...newReward, level: e.target.value })
                    }
                  />
                </Grid>
                <Grid item xs={12} md={5}>
                  <TextField
                    fullWidth
                    label="Role ID"
                    value={newReward.role_id}
                    onChange={(e) =>
                      setNewReward({ ...newReward, role_id: e.target.value })
                    }
                  />
                </Grid>
                <Grid item xs={12} md={2}>
                  <Button
                    variant="contained"
                    onClick={addRoleReward}
                    fullWidth
                    sx={{ height: '100%' }}
                  >
                    Add
                  </Button>
                </Grid>
              </Grid>

              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Level</TableCell>
                      <TableCell>Role ID</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {settings.role_rewards.map((reward) => (
                      <TableRow key={reward.level}>
                        <TableCell>{reward.level}</TableCell>
                        <TableCell>{reward.role_id}</TableCell>
                        <TableCell align="right">
                          <Button
                            color="error"
                            onClick={() => removeRoleReward(reward.level)}
                          >
                            Remove
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Leaderboard
              </Typography>

              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Rank</TableCell>
                      <TableCell>User</TableCell>
                      <TableCell>Level</TableCell>
                      <TableCell>XP</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {leaderboard.map((entry) => (
                      <TableRow key={entry.user_discord_id}>
                        <TableCell>{entry.rank}</TableCell>
                        <TableCell>{entry.username}</TableCell>
                        <TableCell>{entry.level}</TableCell>
                        <TableCell>{entry.xp}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSave}
          size="large"
        >
          Save Changes
        </Button>
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Leveling;
