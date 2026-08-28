import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import toast from "react-hot-toast";
import api from "../api/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem("token"));

  const login = useCallback((t) => {
    localStorage.setItem("token", t);
    setToken(t);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
  }, []);

  // Validate token on mount if it exists
  useEffect(() => {
    if (token) {
      api
        .get("/me")
        .then(() => {
          // token is valid, do nothing
        })
        .catch((err) => {
          if (err.response?.status === 401) {
            logout();
            toast.error("Session expired — please sign in again");
          }
          // network errors are handled elsewhere
        });
    }
  }, [token, logout]);

  useEffect(() => {
    const onExpired = () => {
      setToken(null);
      toast.error("Session expired — please sign in again");
    };
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isAuthed: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
