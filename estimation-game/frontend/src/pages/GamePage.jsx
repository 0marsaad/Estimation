import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getGameState, submitBid, submitEstimate,
  recordTricks, nextRound, getScores,
} from '../api/gameApi';
import { useGame } from '../state/GameContext';
import { useAuth } from '../state/AuthContext';
import Scoreboard from '../components/Scoreboard';
import BiddingPanel from '../components/BiddingPanel';
import EstimationPanel from '../components/EstimationPanel';
import TrickEntryPanel from '../components/TrickEntryPanel';

export default function GamePage() {
  const { roomId } = useParams();
  const { game, setGame, room, events, sendEvent } = useGame();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [gameState, setGameState] = useState(null);
  const [scores, setScores] = useState([]);
  const [error, setError] = useState('');

  const refresh = () =>
    getGameState(roomId).then(({ data }) => setGameState(data)).catch(console.error);

  useEffect(() => {
    refresh();
  }, [roomId]);

  // Re-fetch game state whenever a WS event arrives
  useEffect(() => {
    if (events.length > 0) refresh();
  }, [events]);

  const loadScores = () =>
    getScores(roomId).then(({ data }) => setScores(data));

  useEffect(() => {
    loadScores();
  }, [gameState?.current_round]);

  if (!gameState) return <p>Loading game...</p>;

  const currentRound = gameState.rounds.find(
    (r) => r.round_number === gameState.current_round
  );

  const handleNextRound = async () => {
    setError('');
    try {
      await nextRound(roomId);
      await refresh();
      sendEvent({ type: 'round_finished', round_number: gameState.current_round });
    } catch (err) {
      setError(err.response?.data?.detail || 'Error advancing round.');
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: '20px auto', padding: 24 }}>
      <h2>Round {gameState.current_round} / 18</h2>
      {currentRound && (
        <>
          <p>Phase: <strong>{currentRound.phase}</strong></p>
          <p>Trump: <strong>{currentRound.trump_suit || '—'}</strong></p>
          {currentRound.double_score && <p style={{ color: 'orange' }}>⚡ Double Score Round!</p>}
        </>
      )}

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {currentRound?.phase === 'BIDDING' && (
        <BiddingPanel roomId={roomId} onDone={refresh} sendEvent={sendEvent} />
      )}

      {currentRound?.phase === 'ESTIMATION' && (
        <EstimationPanel
          roomId={roomId}
          callerBid={currentRound.bids.find((b) => !b.is_pass)?.tricks_called}
          onDone={refresh}
          sendEvent={sendEvent}
        />
      )}

      {currentRound?.phase === 'PLAYING' && (
        <TrickEntryPanel
          roomId={roomId}
          players={room?.players || []}
          onDone={async () => { await refresh(); await loadScores(); }}
        />
      )}

      {currentRound?.phase === 'ROUND_END' && !gameState.is_finished && (
        <button onClick={handleNextRound}>Next Round →</button>
      )}

      {gameState.is_finished && (
        <div>
          <h3>🏆 Game Finished!</h3>
          <button onClick={() => navigate('/lobby')}>Back to Lobby</button>
        </div>
      )}

      <hr />
      <Scoreboard scores={scores} />
    </div>
  );
}
