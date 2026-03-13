import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

// Read Django's csrftoken cookie and attach it as X-CSRFToken on every
// mutating request so SessionAuthentication's CSRF check passes.
function getCsrfToken() {
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='));
  return match ? match.split('=')[1] : null;
}

api.interceptors.request.use((config) => {
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

// ---- Auth ----
export const register = (username, password) =>
  api.post('/auth/register/', { username, password });

export const login = (username, password) =>
  api.post('/auth/login/', { username, password });

export const logout = () => api.post('/auth/logout/');

export const getMe = () => api.get('/auth/me/');

// ---- Rooms ----
export const createRoom = () => api.post('/rooms/create/');

export const joinRoom = (room_code) => api.post('/rooms/join/', { room_code });

export const getRoom = (room_id) => api.get(`/rooms/${room_id}/`);

// ---- Game ----
export const startGame = (room_id) => api.post('/game/start/', { room_id });

export const getGameState = (room_id) =>
  api.get('/game/state/', { params: { room_id } });

export const submitBid = (room_id, tricks_called, trump, is_pass = false) =>
  api.post('/game/bid/', { room_id, tricks_called, trump, is_pass });

export const submitEstimate = (room_id, tricks_estimated, is_dash_call = false) =>
  api.post('/game/estimate/', { room_id, tricks_estimated, is_dash_call });

export const recordTricks = (room_id, results) =>
  api.post('/game/play/', { room_id, results });

export const nextRound = (room_id) =>
  api.post('/game/next-round/', { room_id });

export const getScores = (room_id) =>
  api.get('/game/scores/', { params: { room_id } });

// ---- Scoring history ----
export const getRoundScores = (room_id, round_number) =>
  api.get('/scoring/round/', { params: { room_id, round_number } });

export const getGameScores = (room_id) =>
  api.get('/scoring/game/', { params: { room_id } });

export default api;
