import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Grid,
  TextField,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  Alert,
  Snackbar,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Chip,
  Stack,
} from '@mui/material';
import useAuth from '../hooks/useAuth';

interface AutoModSettings {
  banned_words: string[];
  banned_links: string[];
  spam_threshold: number;
  spam_interval: number;
  raid_threshold: number;
  raid_interval: number;
  action_type: 'warn' | 'mute' | 'kick' | 'ban';
  is_enabled: boolean;
}

const AutoMod: React.FC = () => {
  const { guildId } = useParams<{ guildId: string }>();
  const { user } = useAuth();
  const [settings, setSettings] = React.useState<AutoModSettings>({
    banned_words: [],
    banned_links: [],
    spam_threshold: 5,
    spam_interval: 5,
    raid_threshold: 10,
    raid_interval: 30,
    action_type: 'warn',
    is_enabled: true,
  });
  const [newWord, setNewWord] = React.useState('');
  const [newLink, setNewLink] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [snackbar, setSnackbar] = React.useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error',
  });

  React.useEffect(() => {
    fetchSettings();
  }, [guildId]);

  const fetchSettings = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/automod/${guildId}`,
        {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch automod settings');
      }

      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching automod settings:', error);
      showSnackbar('Failed to load settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/automod/${guildId}`,
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

  const addBannedWord = () => {
    if (newWord && !settings.banned_words.includes(newWord)) {
      setSettings({
        ...settings,
        banned_words: [...settings.banned_words, newWord],
      });
      setNewWord('');
    }
  };

  const removeBannedWord = (word: string) => {
    setSettings({
      ...settings,
      banned_words: settings.banned_words.filter((w) => w !== word),
    });
  };

  const addBannedLink = () => {
    if (newLink && !settings.banned_links.includes(newLink)) {
      setSettings({
        ...settings,
        banned_links: [...settings.banned_links, newLink],
      });
      setNewLink('');
    }
  };

  const removeBannedLink = (link: string) => {
    setSettings({
      ...settings,
      banned_links: settings.banned_links.filter((l) => l !== link),
    });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AutoMod Settings
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
                label="Enable AutoMod"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Banned Words
              </Typography>
              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  label="Add Banned Word"
                  value={newWord}
                  onChange={(e) => setNewWord(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addBannedWord()}
                />
                <Button
                  variant="contained"
                  onClick={addBannedWord}
                  sx={{ mt: 1 }}
                >
                  Add Word
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                {settings.banned_words.map((word) => (
                  <Chip
                    key={word}
                    label={word}
                    onDelete={() => removeBannedWord(word)}
                  />
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Banned Links
              </Typography>
              <Box sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  label="Add Banned Link"
                  value={newLink}
                  onChange={(e) => setNewLink(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addBannedLink()}
                />
                <Button
                  variant="contained"
                  onClick={addBannedLink}
                  sx={{ mt: 1 }}
                >
                  Add Link
                </Button>
              </Box>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                {settings.banned_links.map((link) => (
                  <Chip
                    key={link}
                    label={link}
                    onDelete={() => removeBannedLink(link)}
                  />
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Spam Protection
              </Typography>
              <TextField
                fullWidth
                type="number"
                label="Message Threshold"
                value={settings.spam_threshold}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    spam_threshold: parseInt(e.target.value) || 0,
                  })
                }
                margin="normal"
              />
              <TextField
                fullWidth
                type="number"
                label="Time Interval (seconds)"
                value={settings.spam_interval}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    spam_interval: parseInt(e.target.value) || 0,
                  })
                }
                margin="normal"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Raid Protection
              </Typography>
              <TextField
                fullWidth
                type="number"
                label="Join Threshold"
                value={settings.raid_threshold}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    raid_threshold: parseInt(e.target.value) || 0,
                  })
                }
                margin="normal"
              />
              <TextField
                fullWidth
                type="number"
                label="Time Interval (seconds)"
                value={settings.raid_interval}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    raid_interval: parseInt(e.target.value) || 0,
                  })
                }
                margin="normal"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Action Settings
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Action Type</InputLabel>
                <Select
                  value={settings.action_type}
                  label="Action Type"
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      action_type: e.target.value as AutoModSettings['action_type'],
                    })
                  }
                >
                  <MenuItem value="warn">Warn</MenuItem>
                  <MenuItem value="mute">Mute</MenuItem>
                  <MenuItem value="kick">Kick</MenuItem>
                  <MenuItem value="ban">Ban</MenuItem>
                </Select>
              </FormControl>
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

export default AutoMod;
