import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Spinner } from "./States";

export function ProtectedRoute() {
  const { user, loading } = useAuth();
  if (loading) return <Spinner label="Loading…" />;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}
