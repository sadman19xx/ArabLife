import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Paper,
} from '@mui/material';
import {
  People as PeopleIcon,
  Message as MessageIcon,
  Security as SecurityIcon,
  EmojiEvents as LevelingIcon,
} from '@mui/icons-material';
import useAuth from '../hooks/useAuth';

interface GuildStats {
  member_count: number;
  online_members: number;
  message_count_24h: number;
  new_members_24h: number;
  voice_channels_active: number;
  total_channels: number;
  total_roles: number;
  bot_commands_used_24h: number;
}

interface ActivityData {
  date: string;
  count: number;
}

interface GuildActivity {
  message_activity: ActivityData[];
  member_growth: ActivityData[];
  command_usage: ActivityData[];
}

const GuildDashboard: React.FC = () => {
  const { guildId } = useParams<{ guildId: string }>();
  const { user } = useAuth();
  const [stats, setStats] = React.useState<GuildStats | null>(null);
  const [activity, setActivity] = React.useState<GuildActivity | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (guildId) {
      fetchGuildData();
    }
  }, [guildId]);

  const fetchGuildData = async () => {
    try {
      const [statsResponse, activityResponse] = await Promise.all([
        fetch(`${process.env.REACT_APP_API_URL}/guilds/${guildId}/stats`, {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }),
        fetch(`${process.env.REACT_APP_API_URL}/guilds/${guildId}/activity`, {
          headers: {
            Authorization: `Bearer ${user?.token}`,
          },
        }),
      ]);

      if (!statsResponse.ok || !activityResponse.ok) {
        throw new Error('Failed to fetch guild data');
      }

      const statsData = await statsResponse.json();
      const activityData = await activityResponse.json();

      setStats(statsData);
      setActivity(activityData);
    } catch (error) {
      console.error('Error fetching guild data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LinearProgress />;
  }

  if (!stats || !activity) {
    return (
      <Box p={3}>
        <Typography color="error">Failed to load guild data</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <PeopleIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">{stats.member_count}</Typography>
                  <Typography color="textSecondary">Total Members</Typography>
                </Box>
              </Box>
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  {stats.online_members} members online
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  +{stats.new_members_24h} new today
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <MessageIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">{stats.message_count_24h}</Typography>
                  <Typography color="textSecondary">Messages Today</Typography>
                </Box>
              </Box>
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  {stats.voice_channels_active} active voice channels
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {stats.total_channels} total channels
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <SecurityIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">{stats.bot_commands_used_24h}</Typography>
                  <Typography color="textSecondary">Commands Used</Typography>
                </Box>
              </Box>
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  AutoMod Actions: 15
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Warnings Issued: 3
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <LevelingIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">{stats.total_roles}</Typography>
                  <Typography color="textSecondary">Total Roles</Typography>
                </Box>
              </Box>
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  Level Roles: 5
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Custom Commands: 8
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Activity Charts would go here */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Server Activity
            </Typography>
            {/* Add charts here using react-chartjs-2 */}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default GuildDashboard;
