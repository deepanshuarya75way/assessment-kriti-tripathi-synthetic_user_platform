import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

export function Login() {
  const { login, user } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demopassword123");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Login failed.", "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1 className="auth-brand">
          <span className="brand-mark">◐</span> Synthetic User Research
        </h1>
        <p className="muted">Sign in to run AI-simulated product research.</p>
        <label>
          Email
          <input type="email" value={email} required onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="auth-alt">
          No account? <Link to="/register">Create one</Link>
        </p>
        <p className="muted auth-demo">Demo: demo@example.com / demopassword123 (after seeding)</p>
      </form>
    </div>
  );
}
