import { useState } from "react";
import {
  useNavigate,
  useSearchParams,
  useLocation,
  Link,
} from "react-router-dom";
import { Telescope } from "lucide-react";
import toast from "react-hot-toast";
import api, { errMsg } from "../api/api";
import { useAuth } from "../context/AuthContext";

export default function AuthPage() {
  const [params] = useSearchParams();
  const [isLogin, setIsLogin] = useState(params.get("mode") !== "register");
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      let resp;
      if (isLogin) {
        const fd = new FormData();
        fd.append("username", form.username);
        fd.append("password", form.password);
        resp = await api.post("/login", fd);
      } else {
        resp = await api.post("/register", form);
      }
      login(resp.data.access_token);
      toast.success(isLogin ? "Welcome back" : "Account created");
      navigate(location.state?.from || "/app", { replace: true });
    } catch (err) {
      const m = errMsg(
        err,
        isLogin ? "Invalid credentials" : "Could not create account"
      );
      setError(m);
      toast.error(m);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <Link to="/" className="brand" style={{ marginBottom: 18 }}>
          <span className="brand-mark">
            <Telescope size={17} />
          </span>{" "}
          ResearchLens
        </Link>
        <h2>{isLogin ? "Sign in" : "Create your account"}</h2>
        <p>
          {isLogin
            ? "Pick up where you left off."
            : "Free to start — no card required."}
        </p>

        <div className="tabs">
          <button
            className={`tab ${isLogin ? "active" : ""}`}
            onClick={() => {
              setIsLogin(true);
              setError("");
            }}
          >
            Sign in
          </button>
          <button
            className={`tab ${!isLogin ? "active" : ""}`}
            onClick={() => {
              setIsLogin(false);
              setError("");
            }}
          >
            Register
          </button>
        </div>

        {error && <div className="error-box">{error}</div>}

        <form onSubmit={submit}>
          {!isLogin && (
            <div className="field">
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                value={form.email}
                onChange={set("email")}
                placeholder="you@lab.edu"
                required
              />
            </div>
          )}
          <div className="field">
            <label className="label">Username</label>
            <input
              className="input"
              value={form.username}
              onChange={set("username")}
              placeholder="researcher"
              required
            />
          </div>
          <div className="field">
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              value={form.password}
              onChange={set("password")}
              placeholder="••••••••"
              required
            />
          </div>
          <button
            className="btn btn-primary"
            style={{ width: "100%", marginTop: 6 }}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" />{" "}
                {isLogin ? "Signing in…" : "Creating account…"}
              </>
            ) : isLogin ? (
              "Sign in"
            ) : (
              "Create account"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
