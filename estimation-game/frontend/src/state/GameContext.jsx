import { createContext, useContext, useState, useRef, useCallback } from 'react';
import { createGameSocket } from '../websocket/gameSocket';

const GameContext = createContext(null);

export function GameProvider({ children }) {
  const [room, setRoom] = useState(null);
  const [game, setGame] = useState(null);
  const [events, setEvents] = useState([]);
  const socketRef = useRef(null);

  const connectSocket = useCallback((roomCode) => {
    if (socketRef.current) socketRef.current.close();
    socketRef.current = createGameSocket(roomCode, (msg) => {
      setEvents((prev) => [...prev, msg]);
    });
  }, []);

  const disconnectSocket = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const sendEvent = useCallback((payload) => {
    if (socketRef.current) socketRef.current.send(payload);
  }, []);

  return (
    <GameContext.Provider value={{
      room, setRoom,
      game, setGame,
      events,
      connectSocket, disconnectSocket, sendEvent,
    }}>
      {children}
    </GameContext.Provider>
  );
}

export const useGame = () => useContext(GameContext);
