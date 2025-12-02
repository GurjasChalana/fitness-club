import React, { createContext, useContext, useMemo, useState } from "react";
import { API_BASE } from "./config";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    try {
      const saved = localStorage.getItem("auth");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const login = async (username, password) => {
    const token = `Basic ${btoa(`${username}:${password}`)}`;
    const res = await fetch(`${API_BASE}/auth/whoami`, {
      headers: { Authorization: token },
    });
    if (!res.ok) {
      throw new Error("Invalid credentials");
    }
    const whoami = await res.json();
    const payload = { ...whoami, username, token };
    setAuth(payload);
    localStorage.setItem("auth", JSON.stringify(payload));
    return payload;
  };

  const logout = () => {
    setAuth(null);
    localStorage.removeItem("auth");
  };

  const value = useMemo(
    () => ({
      auth,
      authHeader: auth ? { Authorization: auth.token } : {},
      login,
      logout,
    }),
    [auth]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
