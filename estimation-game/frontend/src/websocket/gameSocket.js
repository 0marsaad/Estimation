/**
 * websocketClient.js
 *
 * Manages the WebSocket connection for a game room.
 *
 * Usage:
 *   const ws = createGameSocket(roomCode, onMessage);
 *   ws.send({ type: 'bid_submitted', tricks_called: 5, trump: 'SPADES' });
 *   ws.close();
 */

export function createGameSocket(roomCode, onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.host;
  const url = `${protocol}://${host}/ws/game/${roomCode}/`;

  const socket = new WebSocket(url);

  socket.onopen = () => console.log(`[WS] Connected to room ${roomCode}`);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.error('[WS] Failed to parse message:', event.data);
    }
  };

  socket.onerror = (err) => console.error('[WS] Error:', err);

  socket.onclose = (event) => console.log(`[WS] Disconnected (code ${event.code})`);

  return {
    send: (payload) => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
      }
    },
    close: () => socket.close(),
    socket,
  };
}
