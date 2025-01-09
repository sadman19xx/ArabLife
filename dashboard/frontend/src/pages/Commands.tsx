import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  TextField,
  Typography,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import useAuth from '../hooks/useAuth';

interface Command {
  id: number;
  name: string;
  response: string;
  description?: string;
  is_enabled: boolean;
  required_role_id?: string;
  cooldown: number;
}

const Commands: React.FC = () => {
  const { guildId } = useParams<{ guildId: string }>();
  const { user } = useAuth();
  const [commands, setCommands] = React.useState<Command[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editingCommand, setEditingCommand] = React.useState<Command | null>(null);
  const [formData, setFormData] = React.useState({
    name: '',
    response: '',
    description: '',
    is_enabled: true,
    required_role_id: '',
    cooldown: 0,
  });

  React.useEffect(() => {
    fetchCommands();
  }, [guildId]);

  const fetchCommands = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/commands/${guildId}`,
        {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch commands');
      }

      const data = await response.json();
      setCommands(data);
    } catch (error) {
      console.error('Error fetching commands:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (command?: Command) => {
    if (command) {
      setEditingCommand(command);
      setFormData({
        name: command.name,
        response: command.response,
        description: command.description || '',
        is_enabled: command.is_enabled,
        required_role_id: command.required_role_id || '',
        cooldown: command.cooldown,
      });
    } else {
      setEditingCommand(null);
      setFormData({
        name: '',
        response: '',
        description: '',
        is_enabled: true,
        required_role_id: '',
        cooldown: 0,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingCommand(null);
  };

  const handleSubmit = async () => {
    try {
      const url = `${process.env.REACT_APP_API_URL}/commands/${guildId}${
        editingCommand ? `/${editingCommand.id}` : ''
      }`;
      const method = editingCommand ? 'PATCH' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${user?.token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to save command');
      }

      fetchCommands();
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving command:', error);
    }
  };

  const handleDelete = async (commandId: number) => {
    if (!window.confirm('Are you sure you want to delete this command?')) {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/commands/${guildId}/${commandId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete command');
      }

      fetchCommands();
    } catch (error) {
      console.error('Error deleting command:', error);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Custom Commands</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Command
        </Button>
      </Box>

      <Grid container spacing={3}>
        {commands.map((command) => (
          <Grid item xs={12} md={6} lg={4} key={command.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6" component="div">
                    /{command.name}
                  </Typography>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(command)}
                      sx={{ mr: 1 }}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(command.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Box>
                <Typography color="textSecondary" gutterBottom>
                  {command.description || 'No description'}
                </Typography>
                <Typography variant="body2">Response: {command.response}</Typography>
                <Box mt={2}>
                  <Typography variant="body2" color="textSecondary">
                    Cooldown: {command.cooldown}s
                  </Typography>
                  {command.required_role_id && (
                    <Typography variant="body2" color="textSecondary">
                      Required Role: {command.required_role_id}
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingCommand ? 'Edit Command' : 'Create Command'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Command Name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              margin="normal"
            />
            <TextField
              fullWidth
              label="Response"
              value={formData.response}
              onChange={(e) =>
                setFormData({ ...formData, response: e.target.value })
              }
              margin="normal"
              multiline
              rows={3}
            />
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              margin="normal"
            />
            <TextField
              fullWidth
              label="Required Role ID"
              value={formData.required_role_id}
              onChange={(e) =>
                setFormData({ ...formData, required_role_id: e.target.value })
              }
              margin="normal"
            />
            <TextField
              fullWidth
              type="number"
              label="Cooldown (seconds)"
              value={formData.cooldown}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  cooldown: parseInt(e.target.value) || 0,
                })
              }
              margin="normal"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_enabled}
                  onChange={(e) =>
                    setFormData({ ...formData, is_enabled: e.target.checked })
                  }
                />
              }
              label="Enabled"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Commands;
