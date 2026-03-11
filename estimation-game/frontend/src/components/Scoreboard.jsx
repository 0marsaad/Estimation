export default function Scoreboard({ scores }) {
  if (!scores.length) return null;
  return (
    <div>
      <h3>Scoreboard</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Player</th>
            <th>Total Score</th>
          </tr>
        </thead>
        <tbody>
          {scores
            .slice()
            .sort((a, b) => b.total_score - a.total_score)
            .map((s) => (
              <tr key={s.player}>
                <td>{s.player}</td>
                <td>{s.total_score}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
