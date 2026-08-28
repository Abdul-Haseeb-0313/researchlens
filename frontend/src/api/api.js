import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem("token")) {
      localStorage.removeItem("token");
      window.dispatchEvent(new Event("auth:expired"));
    }
    return Promise.reject(err);
  }
);

export const errMsg = (err, fallback = "Something went wrong") => {
  const d = err?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d[0]?.msg) return d[0].msg;
  return err?.message === "Network Error"
    ? "Cannot reach the server"
    : fallback;
};

export default api;
