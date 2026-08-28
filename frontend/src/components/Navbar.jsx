import { Link, useNavigate } from "react-router-dom";
import { Telescope, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

export default function Navbar() {
  const { isAuthed, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="appbar">
      <div className="container appbar-inner">
        <Link to={isAuthed ? "/app" : "/"} className="brand">
          <span className="brand-mark">
            <Telescope size={17} />
          </span>
          ResearchLens
        </Link>
        <nav style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {isAuthed ? (
            <button
              className="btn btn-ghost"
              onClick={() => {
                logout();
                toast.success("Signed out");
                navigate("/");
              }}
            >
              <LogOut size={16} /> Sign out
            </button>
          ) : (
            <>
              <Link to="/auth" className="btn btn-ghost">
                Sign in
              </Link>
              <Link to="/auth?mode=register" className="btn btn-primary">
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
