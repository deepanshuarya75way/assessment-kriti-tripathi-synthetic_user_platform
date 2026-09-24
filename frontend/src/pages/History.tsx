import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { researchApi } from "../api/endpoints";
import { EmptyState, ErrorState, Spinner } from "../components/States";
import { StatusBadge } from "../components/StatusBadge";
import type { Page, ResearchSummary } from "../types";

const PAGE_SIZE = 10;

export function History() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<ResearchSummary> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = (p: number) => {
    setLoading(true);
    setError(null);
    researchApi
      .list(p, PAGE_SIZE)
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load history."))
      .finally(() => setLoading(false));
  };

  useEffect(() => load(page), [page]);

  if (loading && !data) return <Spinner label="Loading history…" />;
  if (error) return <ErrorState message={error} onRetry={() => load(page)} />;
  if (!data) return null;

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Research history</h1>
          <p className="muted">{data.total} project(s)</p>
        </div>
        <Link to="/research/new" className="btn btn-primary">
          + New research
        </Link>
      </div>

      {data.items.length === 0 ? (
        <EmptyState
          title="No projects yet"
          hint="Your research projects will appear here."
          action={
            <Link to="/research/new" className="btn btn-primary">
              Create research
            </Link>
          }
        />
      ) : (
        <>
          <div className="list">
            {data.items.map((p) => (
              <button key={p.id} className="list-row" onClick={() => navigate(`/research/${p.id}`)}>
                <div className="list-row-main">
                  <span className="list-row-title">{p.title}</span>
                  <span className="muted">
                    {new Date(p.created_at).toLocaleDateString()} · {p.num_personas} personas
                  </span>
                </div>
                <StatusBadge status={p.status} />
              </button>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-secondary btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span className="muted">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-secondary btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
