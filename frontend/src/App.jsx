import { useEffect, useState } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import api from "./api/api";
import Navbar from "./components/Navbar";
import Landing from "./pages/Landing";
import AuthPage from "./pages/AuthPage";
import Workspaces from "./pages/Workspaces";
import WorkspaceChat from "./pages/WorkspaceChat";

function Protected({ children }) {
  const { isAuthed } = useAuth();
  const location = useLocation();
  if (!isAuthed) {
    return <Navigate to="/auth" state={{ from: location.pathname }} replace />;
  }
  return children;
}

export default function App() {
  const { isAuthed } = useAuth();
  const { pathname } = useLocation();
  const showNav = pathname !== "/auth";
  const [serverDown, setServerDown] = useState(false);
  const [checkingServer, setCheckingServer] = useState(true);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        await api.get("/health");
        if (alive) setServerDown(false);
      } catch (err) {
        if (alive) setServerDown(true);
      } finally {
        if (alive) setCheckingServer(false);
      }
    };
    check();
    const interval = setInterval(check, 30000); // re-check every 30s
    return () => {
      alive = false;
      clearInterval(interval);
    };
  }, []);

  if (checkingServer) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          color: "var(--muted)",
        }}
      >
        <span className="spinner" style={{ width: 28, height: 28 }} />
      </div>
    );
  }

  if (serverDown) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          textAlign: "center",
          padding: 20,
        }}
      >
        <div>
          <h1 style={{ fontSize: 28, marginBottom: 8 }}>Server is down</h1>
          <p style={{ color: "var(--muted)", marginBottom: 20 }}>
            Please try again later.
          </p>
          <button
            className="btn btn-primary"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {showNav && <Navbar />}
      <Routes>
        <Route
          path="/"
          element={isAuthed ? <Navigate to="/app" replace /> : <Landing />}
        />
        <Route
          path="/auth"
          element={isAuthed ? <Navigate to="/app" replace /> : <AuthPage />}
        />
        <Route
          path="/app"
          element={
            <Protected>
              <Workspaces />
            </Protected>
          }
        />
        <Route
          path="/app/w/:workspaceId"
          element={
            <Protected>
              <WorkspaceChat />
            </Protected>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
