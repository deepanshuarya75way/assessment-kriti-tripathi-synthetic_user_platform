import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { researchApi } from "../api/endpoints";
import { EmptyState, ErrorState, Spinner } from "../components/States";
import { StatusBadge } from "../components/StatusBadge";
import type { DashboardStats } from "../types";

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    setError(null);
    researchApi
      .dashboard()
      .then(setStats)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load dashboard."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <Spinner label="Loading dashboard…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!stats) return null;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">Your synthetic research projects at a glance.</p>
        </div>
        <Link to="/research/new" className="btn btn-primary">
          + New research
        </Link>
      </div>

      <div className="stat-grid">
        <Stat label="Total" value={stats.total} tone="default" />
        <Stat label="Completed" value={stats.completed} tone="completed" />
        <Stat label="Running" value={stats.running} tone="running" />
        <Stat label="Pending" value={stats.pending} tone="pending" />
        <Stat label="Failed" value={stats.failed} tone="failed" />
      </div>

      <h2 className="section-title">Recent projects</h2>
      {stats.recent.length === 0 ? (
        <EmptyState
          title="No research yet"
          hint="Create your first synthetic research project to generate personas and insights."
          action={
            <Link to="/research/new" className="btn btn-primary">
              Create research
            </Link>
          }
        />
      ) : (
        <div className="list">
          {stats.recent.map((p) => (
            <button key={p.id} className="list-row" onClick={() => navigate(`/research/${p.id}`)}>
              <div className="list-row-main">
                <span className="list-row-title">{p.title}</span>
                <span className="muted">
                  {p.num_personas} personas · {p.num_questions} questions
                </span>
              </div>
              <StatusBadge status={p.status} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`stat-card stat-${tone}`}>
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
