import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createRoom, joinRoom } from '../api/gameApi';
import { useGame } from '../state/GameContext';
import { useAuth } from '../state/AuthContext';

export default function LobbyPage() {
  const { setRoom, connectSocket } = useGame();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [roomCode, setRoomCode] = useState('');
  const [error, setError] = useState('');

  const handleCreate = async () => {
    setError('');
    try {
      const { data } = await createRoom();
      setRoom(data);
      connectSocket(data.room_code);
      navigate(`/room/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create room.');
    }
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const { data } = await joinRoom(roomCode.toUpperCase());
      setRoom(data);
      connectSocket(data.room_code);
      navigate(`/room/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to join room.');
    }
  };

  return (
    <div style={{ maxWidth: 480, margin: '80px auto', padding: 24 }}>
      <h2>Welcome, {user?.username}</h2>
      <button onClick={handleCreate}>Create Room</button>
      <hr />
      <form onSubmit={handleJoin}>
        <input
          placeholder="Room Code"
          value={roomCode}
          onChange={(e) => setRoomCode(e.target.value)}
          maxLength={6}
          required
        />
        <button type="submit">Join Room</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <hr />
      <button onClick={logout}>Logout</button>
    </div>
  );
}
