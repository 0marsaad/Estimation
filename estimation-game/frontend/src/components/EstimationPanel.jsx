import { useState } from 'react';
import { submitEstimate } from '../api/gameApi';

export default function EstimationPanel({ roomId, callerBid, onDone, sendEvent }) {
  const [tricks, setTricks] = useState(0);
  const [isDash, setIsDash] = useState(false);
  const [error, setError] = useState('');

  const maxValue = callerBid != null ? callerBid : 13;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await submitEstimate(roomId, isDash ? 0 : tricks, isDash);
      sendEvent({ type: 'estimate_submitted', tricks_estimated: isDash ? 0 : tricks });
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit estimate.');
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: 16, marginTop: 16 }}>
      <h4>Estimation Phase</h4>
      <p>Caller bid: <strong>{callerBid ?? '—'}</strong> — Your estimate must be ≤ {maxValue}</p>
      <form onSubmit={handleSubmit}>
        <label>
          <input type="checkbox" checked={isDash} onChange={(e) => setIsDash(e.target.checked)} />
          {' '}Dash Call (0 tricks)
        </label>
        {!isDash && (
          <div>
            <label>Estimated tricks: </label>
            <input
              type="number" min={0} max={maxValue}
              value={tricks}
              onChange={(e) => setTricks(Number(e.target.value))}
            />
          </div>
        )}
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit">Submit Estimate</button>
      </form>
    </div>
  );
}
