// src/App.jsx
import React, { useState } from "react";
import MemberPage from "./pages/MemberPage.jsx";
import TrainerPage from "./pages/TrainerPage.jsx";
import AdminPage from "./pages/AdminPage.jsx";
import { AuthProvider, useAuth } from "./AuthContext.jsx";
import { API_BASE } from "./config";

function LoginCard() {
  const { login } = useAuth();
  const [form, setForm] = useState({ username: "", password: "" });
  const [registerForm, setRegisterForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    username: "",
    password: "",
    phone: "",
  });
  const [mode, setMode] = useState("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.username.trim(), form.password);
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/members/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(registerForm),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Registration failed");
      }
      await login(registerForm.username.trim(), registerForm.password);
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="section card stack" style={{ maxWidth: 460 }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ marginBottom: "0.25rem" }}>
          {mode === "login" ? "Fitness Club Login" : "Create Member Account"}
        </h1>
        <button
          type="button"
          className="secondary"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Need an account?" : "Have an account?"}
        </button>
      </div>
      <p className="muted">
        {mode === "login"
          ? "Sign in with your role credentials to see your dashboard."
          : "Register as a member; we’ll log you in right after."}
      </p>
      {mode === "login" ? (
        <form className="stack" onSubmit={handleSubmit}>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span>Username</span>
            <input
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              autoComplete="username"
              required
            />
          </label>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span>Password</span>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <div className="callout" style={{ color: "var(--del-color)" }}>{error}</div>}
          <button type="submit" disabled={loading}>{loading ? "Signing in..." : "Login"}</button>
        </form>
      ) : (
        <form className="stack" onSubmit={handleRegister}>
          <div className="grid-2">
            <label className="stack" style={{ gap: "0.25rem" }}>
              <span>First name</span>
              <input
                value={registerForm.first_name}
                onChange={(e) => setRegisterForm({ ...registerForm, first_name: e.target.value })}
                required
              />
            </label>
            <label className="stack" style={{ gap: "0.25rem" }}>
              <span>Last name</span>
              <input
                value={registerForm.last_name}
                onChange={(e) => setRegisterForm({ ...registerForm, last_name: e.target.value })}
                required
              />
            </label>
          </div>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span>Email</span>
            <input
              type="email"
              value={registerForm.email}
              onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
              required
            />
          </label>
          <div className="grid-2">
            <label className="stack" style={{ gap: "0.25rem" }}>
              <span>Username</span>
              <input
                value={registerForm.username}
                onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                required
              />
            </label>
            <label className="stack" style={{ gap: "0.25rem" }}>
              <span>Password</span>
              <input
                type="password"
                value={registerForm.password}
                onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                required
              />
            </label>
          </div>
          <label className="stack" style={{ gap: "0.25rem" }}>
            <span>Phone (optional)</span>
            <input
              value={registerForm.phone}
              onChange={(e) => setRegisterForm({ ...registerForm, phone: e.target.value })}
            />
          </label>
          {error && <div className="callout" style={{ color: "var(--del-color)" }}>{error}</div>}
          <button type="submit" disabled={loading}>{loading ? "Creating..." : "Create & Login"}</button>
        </form>
      )}
      <div className="muted" style={{ fontSize: "0.9rem" }}>
        Demo creds: admin/admin, members alice|bob|carol (password), trainers tom|lisa|mark (password).
      </div>
    </section>
  );
}

function DashboardHost() {
  const { auth, logout } = useAuth();

  if (!auth) {
    return (
      <main className="container-narrow">
        <LoginCard />
      </main>
    );
  }

  const roleView = {
    member: <MemberPage />,
    trainer: <TrainerPage />,
    admin: <AdminPage />,
  }[auth.role] || <p>Unsupported role</p>;

  return (
    <main className="container-narrow stack">
      <header className="card section row" style={{ alignItems: "center", justifyContent: "space-between" }}>
        <div className="stack" style={{ gap: "0.15rem" }}>
          <h1 style={{ margin: 0 }}>Fitness Club</h1>
          <p className="muted" style={{ margin: 0 }}>
            Signed in as {auth.username} · <strong>{auth.role}</strong>
          </p>
        </div>
        <button className="secondary" onClick={logout}>Log out</button>
      </header>
      {roleView}
    </main>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DashboardHost />
    </AuthProvider>
  );
}
