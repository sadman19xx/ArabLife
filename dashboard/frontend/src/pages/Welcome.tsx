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
  Paper,
} from '@mui/material';
import { ChromePicker } from 'react-color';
import useAuth from '../hooks/useAuth';

interface WelcomeMessage {
  content: string;
  embed_title: string | null;
  embed_description: string | null;
  embed_color: string | null;
  is_enabled: boolean;
}

const Welcome: React.FC = () => {
  const { guildId } = useParams<{ guildId: string }>();
  const { user } = useAuth();
  const [message, setMessage] = React.useState<WelcomeMessage>({
    content: '',
    embed_title: '',
    embed_description: '',
    embed_color: '#7289DA',
    is_enabled: true,
  });
  const [showColorPicker, setShowColorPicker] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [snackbar, setSnackbar] = React.useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error',
  });

  React.useEffect(() => {
    fetchWelcomeMessage();
  }, [guildId]);

  const fetchWelcomeMessage = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/welcome/${guildId}`,
        {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch welcome message');
      }

      const data = await response.json();
      setMessage(data);
    } catch (error) {
      console.error('Error fetching welcome message:', error);
      showSnackbar('Failed to load welcome message', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/welcome/${guildId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${user?.token}`,
          },
          body: JSON.stringify(message),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to save welcome message');
      }

      showSnackbar('Welcome message saved successfully', 'success');
    } catch (error) {
      console.error('Error saving welcome message:', error);
      showSnackbar('Failed to save welcome message', 'error');
    }
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
        Welcome Message
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <FormControlLabel
            control={
              <Switch
                checked={message.is_enabled}
                onChange={(e) =>
                  setMessage({ ...message, is_enabled: e.target.checked })
                }
              />
            }
            label="Enable Welcome Messages"
          />

          <TextField
            fullWidth
            multiline
            rows={4}
            label="Welcome Message"
            value={message.content}
            onChange={(e) => setMessage({ ...message, content: e.target.value })}
            margin="normal"
            helperText={
              <>
                Available variables:
                <br />
                {'{user}'} - Mentions the new member
                <br />
                {'{server}'} - Server name
                <br />
                {'{memberCount}'} - Total member count
              </>
            }
          />

          <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
            Embed Settings
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Embed Title"
                value={message.embed_title || ''}
                onChange={(e) =>
                  setMessage({ ...message, embed_title: e.target.value })
                }
                margin="normal"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  onClick={() => setShowColorPicker(!showColorPicker)}
                >
                  Choose Embed Color
                </Button>
                {showColorPicker && (
                  <Paper sx={{ position: 'absolute', zIndex: 1 }}>
                    <ChromePicker
                      color={message.embed_color || '#7289DA'}
                      onChange={(color) =>
                        setMessage({ ...message, embed_color: color.hex })
                      }
                    />
                  </Paper>
                )}
              </Box>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Embed Description"
                value={message.embed_description || ''}
                onChange={(e) =>
                  setMessage({ ...message, embed_description: e.target.value })
                }
                margin="normal"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

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

export default Welcome;
