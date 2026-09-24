import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

export function Register() {
  const { register, user } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      toast("Password must be at least 8 characters.", "error");
      return;
    }
    setBusy(true);
    try {
      await register(email, password, fullName || undefined);
      navigate("/");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Registration failed.", "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1 className="auth-brand">
          <span className="brand-mark">◐</span> Create your account
        </h1>
        <label>
          Full name (optional)
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </label>
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
            minLength={8}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? "Creating…" : "Create account"}
        </button>
        <p className="auth-alt">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
