import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import useAuth from './hooks/useAuth';

// Pages
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Login = React.lazy(() => import('./pages/Login'));
const GuildDashboard = React.lazy(() => import('./pages/GuildDashboard'));
const Commands = React.lazy(() => import('./pages/Commands'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Welcome = React.lazy(() => import('./pages/Welcome'));
const AutoMod = React.lazy(() => import('./pages/AutoMod'));
const Leveling = React.lazy(() => import('./pages/Leveling'));

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        Loading...
      </Box>
    );
  }

  return (
    <React.Suspense
      fallback={
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="100vh"
        >
          Loading...
        </Box>
      }
    >
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
          }
        />
        <Route
          path="/auth/callback"
          element={<Login />}
        />
        
        {/* Protected Routes */}
        <Route element={<ProtectedRoute isAuthenticated={isAuthenticated} />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/guilds/:guildId" element={<GuildDashboard />} />
            <Route path="/guilds/:guildId/commands" element={<Commands />} />
            <Route path="/guilds/:guildId/settings" element={<Settings />} />
            <Route path="/guilds/:guildId/welcome" element={<Welcome />} />
            <Route path="/guilds/:guildId/automod" element={<AutoMod />} />
            <Route path="/guilds/:guildId/leveling" element={<Leveling />} />
          </Route>
        </Route>

        {/* Redirect root to dashboard or login */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        {/* 404 - Redirect to dashboard or login */}
        <Route
          path="*"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </React.Suspense>
  );
}

export default App;
