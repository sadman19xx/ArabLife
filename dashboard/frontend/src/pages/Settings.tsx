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
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';
import useAuth from '../hooks/useAuth';

interface GuildSettings {
  prefix: string;
  mod_role_id: string | null;
  admin_role_id: string | null;
  mute_role_id: string | null;
  welcome_channel_id: string | null;
  log_channel_id: string | null;
  auto_role_id: string | null;
  level_up_channel_id: string | null;
  ticket_category_id: string | null;
  verification_level: number;
  anti_spam: boolean;
  anti_raid: boolean;
  max_warnings: number;
}

const Settings: React.FC = () => {
  const { guildId } = useParams<{ guildId: string }>();
  const { user } = useAuth();
  const [settings, setSettings] = React.useState<GuildSettings | null>(null);
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
        `${process.env.REACT_APP_API_URL}/settings/${guildId}`,
        {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch settings');
      }

      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching settings:', error);
      showSnackbar('Failed to load settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/settings/${guildId}`,
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

  const handleChange = (field: keyof GuildSettings, value: any) => {
    if (!settings) return;
    setSettings({ ...settings, [field]: value });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!settings) {
    return <div>Failed to load settings</div>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Server Settings
      </Typography>

      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                General Settings
              </Typography>
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Command Prefix"
                  value={settings.prefix}
                  onChange={(e) => handleChange('prefix', e.target.value)}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="Max Warnings"
                  type="number"
                  value={settings.max_warnings}
                  onChange={(e) =>
                    handleChange('max_warnings', parseInt(e.target.value))
                  }
                  margin="normal"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Role Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Role Settings
              </Typography>
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Mod Role ID"
                  value={settings.mod_role_id || ''}
                  onChange={(e) => handleChange('mod_role_id', e.target.value)}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="Admin Role ID"
                  value={settings.admin_role_id || ''}
                  onChange={(e) => handleChange('admin_role_id', e.target.value)}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="Mute Role ID"
                  value={settings.mute_role_id || ''}
                  onChange={(e) => handleChange('mute_role_id', e.target.value)}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="Auto Role ID"
                  value={settings.auto_role_id || ''}
                  onChange={(e) => handleChange('auto_role_id', e.target.value)}
                  margin="normal"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Channel Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Channel Settings
              </Typography>
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Welcome Channel ID"
                  value={settings.welcome_channel_id || ''}
                  onChange={(e) =>
                    handleChange('welcome_channel_id', e.target.value)
                  }
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="Log Channel ID"
                  value={settings.log_channel_id || ''}
                  onChange={(e) => handleChange('log_channel_id', e.target.value)}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="Level Up Channel ID"
                  value={settings.level_up_channel_id || ''}
                  onChange={(e) =>
                    handleChange('level_up_channel_id', e.target.value)
                  }
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="Ticket Category ID"
                  value={settings.ticket_category_id || ''}
                  onChange={(e) =>
                    handleChange('ticket_category_id', e.target.value)
                  }
                  margin="normal"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Security Settings
              </Typography>
              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.anti_spam}
                      onChange={(e) =>
                        handleChange('anti_spam', e.target.checked)
                      }
                    />
                  }
                  label="Anti-Spam"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.anti_raid}
                      onChange={(e) =>
                        handleChange('anti_raid', e.target.checked)
                      }
                    />
                  }
                  label="Anti-Raid"
                />
                <TextField
                  fullWidth
                  label="Verification Level"
                  type="number"
                  value={settings.verification_level}
                  onChange={(e) =>
                    handleChange(
                      'verification_level',
                      parseInt(e.target.value)
                    )
                  }
                  margin="normal"
                />
              </Box>
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

export default Settings;
