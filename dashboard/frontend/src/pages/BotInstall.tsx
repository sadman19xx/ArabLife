import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Stack,
  Divider
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface BotStatus {
  status: 'running' | 'stopped';
  logs: string[];
}

const BotInstall: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [formData, setFormData] = useState({
    token: '',
    guild_id: '',
    role_ids_allowed: '',
    role_id_to_give: '',
    role_id_remove_allowed: '',
    role_activity_log_channel_id: '',
    audit_log_channel_id: '',
    visa_image_url: 'https://i.imgur.com/default.png'
  });

  // Fetch bot status periodically
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get('/api/bot/status');
        setBotStatus(response.data);
      } catch (error) {
        console.error('Failed to fetch bot status:', error);
      }
    };

    // Fetch immediately and then every 5 seconds
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleInstall = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Convert string IDs to numbers
      const installData = {
        ...formData,
        guild_id: parseInt(formData.guild_id),
        role_ids_allowed: formData.role_ids_allowed.split(',').map(id => parseInt(id.trim())),
        role_id_to_give: parseInt(formData.role_id_to_give),
        role_id_remove_allowed: parseInt(formData.role_id_remove_allowed),
        role_activity_log_channel_id: parseInt(formData.role_activity_log_channel_id),
        audit_log_channel_id: parseInt(formData.audit_log_channel_id)
      };

      await axios.post('/api/bot/install', installData);
      setSuccess('Bot installed successfully!');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to install bot');
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    try {
      await axios.post('/api/bot/start');
      setSuccess('Bot started successfully!');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to start bot');
    }
  };

  const handleStop = async () => {
    try {
      await axios.post('/api/bot/stop');
      setSuccess('Bot stopped successfully!');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to stop bot');
    }
  };

  return (
    <Container maxWidth="md">
      <Paper sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Bot Installation & Control
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <Box component="form" sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Bot Token"
            name="token"
            value={formData.token}
            onChange={handleInputChange}
            margin="normal"
            type="password"
          />
          <TextField
            fullWidth
            label="Server ID"
            name="guild_id"
            value={formData.guild_id}
            onChange={handleInputChange}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Allowed Role IDs (comma-separated)"
            name="role_ids_allowed"
            value={formData.role_ids_allowed}
            onChange={handleInputChange}
            margin="normal"
            helperText="Example: 123456789,987654321"
          />
          <TextField
            fullWidth
            label="Role ID to Give"
            name="role_id_to_give"
            value={formData.role_id_to_give}
            onChange={handleInputChange}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Role ID Remove Allowed"
            name="role_id_remove_allowed"
            value={formData.role_id_remove_allowed}
            onChange={handleInputChange}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Role Activity Log Channel ID"
            name="role_activity_log_channel_id"
            value={formData.role_activity_log_channel_id}
            onChange={handleInputChange}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Audit Log Channel ID"
            name="audit_log_channel_id"
            value={formData.audit_log_channel_id}
            onChange={handleInputChange}
            margin="normal"
          />

          <Button
            variant="contained"
            color="primary"
            onClick={handleInstall}
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Install Bot'}
          </Button>
        </Box>

        <Divider sx={{ my: 4 }} />

        <Typography variant="h5" gutterBottom>
          Bot Control
        </Typography>

        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <Button
            variant="contained"
            color="success"
            onClick={handleStart}
            disabled={botStatus?.status === 'running'}
          >
            Start Bot
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleStop}
            disabled={botStatus?.status === 'stopped'}
          >
            Stop Bot
          </Button>
        </Stack>

        <Typography variant="h6" gutterBottom>
          Status: {botStatus?.status || 'Unknown'}
        </Typography>

        {botStatus?.logs.length > 0 && (
          <Paper
            sx={{
              p: 2,
              mt: 2,
              maxHeight: 300,
              overflow: 'auto',
              bgcolor: 'grey.900',
              color: 'grey.100',
              fontFamily: 'monospace'
            }}
          >
            {botStatus.logs.map((log, index) => (
              <Typography key={index} variant="body2">
                {log}
              </Typography>
            ))}
          </Paper>
        )}
      </Paper>
    </Container>
  );
};

export default BotInstall;
