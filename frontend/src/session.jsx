import { createContext, useContext, useEffect, useState } from "react";
import api, { clearTokens, getAccess, saveTokens } from "./api";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getAccess()));

  const refreshUser = async () => {
    const { data } = await api.get("/auth/me/");
    setUser(data);
    return data;
  };

  useEffect(() => {
    if (getAccess()) {
      refreshUser()
        .catch(() => clearTokens())
        .finally(() => setLoading(false));
    }
    const onLogout = () => setUser(null);
    window.addEventListener("shiftsync:logout", onLogout);
    return () => window.removeEventListener("shiftsync:logout", onLogout);
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login/", { email, password });
    saveTokens(data);
    await refreshUser();
  };

  const register = async (form) => {
    const { data } = await api.post("/auth/register/", form);
    saveTokens(data);
    setUser(data.user);
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  return (
    <SessionContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = () => useContext(SessionContext);
