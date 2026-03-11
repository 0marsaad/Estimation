import { useState } from 'react';
import { recordTricks } from '../api/gameApi';

export default function TrickEntryPanel({ roomId, players, onDone }) {
  const [entries, setEntries] = useState(
    players.reduce((acc, p) => ({ ...acc, [p.id]: 0 }), {})
  );
  const [error, setError] = useState('');

  const total = Object.values(entries).reduce((s, v) => s + Number(v), 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (total !== 13) {
      setError('Total tricks must equal 13.');
      return;
    }
    try {
      const results = players.map((p) => ({
        player_id: p.id,
        tricks_won: Number(entries[p.id]),
      }));
      await recordTricks(roomId, results);
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record tricks.');
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: 16, marginTop: 16 }}>
      <h4>Record Tricks Won (total must = 13, current: {total})</h4>
      <form onSubmit={handleSubmit}>
        {players.map((p) => (
          <div key={p.id}>
            <label>{p.user.username}: </label>
            <input
              type="number" min={0} max={13}
              value={entries[p.id]}
              onChange={(e) =>
                setEntries((prev) => ({ ...prev, [p.id]: e.target.value }))
              }
            />
          </div>
        ))}
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit">Calculate Scores</button>
      </form>
    </div>
  );
}
