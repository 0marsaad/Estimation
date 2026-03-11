import { useState } from 'react';
import { submitBid } from '../api/gameApi';

const TRUMPS = ['SANS', 'SPADES', 'HEARTS', 'DIAMONDS', 'CLUBS'];

export default function BiddingPanel({ roomId, onDone, sendEvent }) {
  const [tricks, setTricks] = useState(4);
  const [trump, setTrump] = useState('CLUBS');
  const [isPass, setIsPass] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await submitBid(roomId, isPass ? null : tricks, isPass ? 'PASS' : trump, isPass);
      sendEvent({ type: 'bid_submitted', tricks_called: tricks, trump, is_pass: isPass });
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit bid.');
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: 16, marginTop: 16 }}>
      <h4>Bidding Phase</h4>
      <form onSubmit={handleSubmit}>
        <label>
          <input type="checkbox" checked={isPass} onChange={(e) => setIsPass(e.target.checked)} />
          {' '}Pass
        </label>
        {!isPass && (
          <>
            <div>
              <label>Tricks (min 4): </label>
              <input
                type="number" min={4} max={13}
                value={tricks}
                onChange={(e) => setTricks(Number(e.target.value))}
              />
            </div>
            <div>
              <label>Trump: </label>
              <select value={trump} onChange={(e) => setTrump(e.target.value)}>
                {TRUMPS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </>
        )}
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit">Submit Bid</button>
      </form>
    </div>
  );
}
