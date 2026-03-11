import { createContext, useContext, useState, useCallback } from 'react';
import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister } from '../api/gameApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const loadUser = useCallback(async () => {
    try {
      const { data } = await getMe();
      setUser(data);
    } catch {
      setUser(null);
    }
  }, []);

  const login = async (username, password) => {
    const { data } = await apiLogin(username, password);
    setUser(data);
    return data;
  };

  const register = async (username, password) => {
    const { data } = await apiRegister(username, password);
    setUser(data);
    return data;
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
