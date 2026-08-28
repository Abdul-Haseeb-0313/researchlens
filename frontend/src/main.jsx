import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#151925",
              color: "#e8ecf6",
              border: "1px solid #262c3d",
              borderRadius: "10px",
              fontSize: "14px",
            },
            success: {
              iconTheme: { primary: "#6ee7b7", secondary: "#0b0d12" },
            },
            error: { iconTheme: { primary: "#f87171", secondary: "#0b0d12" } },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
