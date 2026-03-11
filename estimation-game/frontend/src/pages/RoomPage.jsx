import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRoom, startGame } from '../api/gameApi';
import { useGame } from '../state/GameContext';
import { useAuth } from '../state/AuthContext';

export default function RoomPage() {
  const { roomId } = useParams();
  const { room, setRoom, setGame, sendEvent } = useGame();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    getRoom(roomId).then(({ data }) => setRoom(data)).catch(console.error);
  }, [roomId]);

  const handleStart = async () => {
    setError('');
    try {
      const { data } = await startGame(roomId);
      setGame(data);
      navigate(`/game/${roomId}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start game.');
    }
  };

  const handleReady = () => {
    sendEvent({ type: 'player_ready' });
  };

  if (!room) return <p>Loading room...</p>;

  return (
    <div style={{ maxWidth: 480, margin: '40px auto', padding: 24 }}>
      <h2>Room: {room.room_code}</h2>
      <p>Status: {room.status}</p>
      <h3>Players ({room.players.length}/4):</h3>
      <ul>
        {room.players.map((p) => (
          <li key={p.id}>
            {p.user.username} — Seat {p.seat_position}
          </li>
        ))}
      </ul>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button onClick={handleReady}>Ready</button>
      {room.players.length === 4 && (
        <button onClick={handleStart} style={{ marginLeft: 12 }}>Start Game</button>
      )}
    </div>
  );
}
