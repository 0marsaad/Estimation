import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './state/AuthContext';
import { GameProvider } from './state/GameContext';
import LoginPage from './pages/LoginPage';
import LobbyPage from './pages/LobbyPage';
import RoomPage from './pages/RoomPage';
import GamePage from './pages/GamePage';

function RequireAuth({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  const { loadUser } = useAuth();
  useEffect(() => { loadUser(); }, []);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/lobby" element={<RequireAuth><LobbyPage /></RequireAuth>} />
      <Route path="/room/:roomId" element={<RequireAuth><RoomPage /></RequireAuth>} />
      <Route path="/game/:roomId" element={<RequireAuth><GamePage /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/lobby" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <GameProvider>
          <AppRoutes />
        </GameProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
