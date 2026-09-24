import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { researchApi } from "../api/endpoints";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { PersonaCard } from "../components/PersonaCard";
import { EmptyState, ErrorState, Spinner } from "../components/States";
import { StatusBadge } from "../components/StatusBadge";
import { useToast } from "../context/ToastContext";
import type {
  InsightReport,
  Persona,
  ResearchDetail as Detail,
  SurveyQuestion,
  SurveyResponseItem,
} from "../types";

type Tab = "overview" | "personas" | "survey" | "responses" | "insights";

export function ResearchDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [project, setProject] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const pollRef = useRef<number | null>(null);

  const fetchProject = useCallback(async () => {
    try {
      const p = await researchApi.get(id);
      setProject(p);
      return p;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load project.");
      return null;
    }
  }, [id]);

  useEffect(() => {
    fetchProject();
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [fetchProject]);

  // Poll while the run is in progress (real status — no fake progress).
  useEffect(() => {
    const active = project?.status === "PENDING" || project?.status === "RUNNING";
    if (active && !pollRef.current) {
      pollRef.current = window.setInterval(fetchProject, 2500);
    }
    if (!active && pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, [project?.status, fetchProject]);

  const onDelete = async () => {
    try {
      await researchApi.remove(id);
      toast("Project deleted.", "success");
      navigate("/history");
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Delete failed.", "error");
    }
  };

  if (error) return <ErrorState message={error} onRetry={fetchProject} />;
  if (!project) return <Spinner label="Loading project…" />;

  const done = project.status === "COMPLETED";

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{project.title}</h1>
          <p className="muted">
            <StatusBadge status={project.status} />
            {project.model_used && <> · model: {project.model_used}</>}
            {project.duration_seconds != null && <> · {project.duration_seconds}s</>}
          </p>
        </div>
        <div className="head-actions">
          {done && <DownloadReport id={id} />}
          <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(true)}>
            Delete
          </button>
        </div>
      </div>

      {project.status === "RUNNING" || project.status === "PENDING" ? (
        <div className="banner banner-info">
          <div className="spinner spinner-sm" aria-hidden /> Running the AI pipeline (persona →
          survey → responses → insights). This page updates automatically.
        </div>
      ) : null}
      {project.status === "FAILED" && (
        <div className="banner banner-error">{project.error_message ?? "This run failed."}</div>
      )}

      <nav className="tabs">
        {(["overview", "personas", "survey", "responses", "insights"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "tab-active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </nav>

      <div className="tab-panel">
        {tab === "overview" && <Overview project={project} />}
        {tab === "personas" && <PersonasTab id={id} done={done} />}
        {tab === "survey" && <SurveyTab id={id} done={done} />}
        {tab === "responses" && <ResponsesTab id={id} done={done} />}
        {tab === "insights" && <InsightsTab id={id} done={done} />}
      </div>

      <ConfirmDialog
        open={confirmDelete}
        title="Delete this project?"
        body="This permanently removes the project and all its generated personas, survey, responses and insights."
        confirmLabel="Delete"
        onConfirm={onDelete}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}

function Overview({ project }: { project: Detail }) {
  return (
    <div className="card overview">
      <Row label="Product">{project.product_description}</Row>
      <Row label="Target audience">{project.target_audience}</Row>
      <Row label="Research goal">{project.research_goal}</Row>
      <Row label="Configuration">
        {project.num_personas} personas · {project.num_questions} questions
      </Row>
      <Row label="Created">{new Date(project.created_at).toLocaleString()}</Row>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="overview-row">
      <span className="overview-label">{label}</span>
      <span>{children}</span>
    </div>
  );
}

function PendingHint({ done }: { done: boolean }) {
  return (
    <EmptyState
      title={done ? "Nothing here" : "Not ready yet"}
      hint={done ? "No data was generated." : "This appears once the run completes."}
    />
  );
}

function PersonasTab({ id, done }: { id: string; done: boolean }) {
  const [data, setData] = useState<Persona[] | null>(null);
  const navigate = useNavigate();
  useEffect(() => {
    if (done) researchApi.personas(id).then(setData).catch(() => setData([]));
  }, [id, done]);
  if (!done) return <PendingHint done={false} />;
  if (!data) return <Spinner />;
  if (!data.length) return <PendingHint done />;
  return (
    <div className="persona-grid">
      {data.map((p) => (
        <PersonaCard
          key={p.id}
          persona={p}
          onChat={() => navigate(`/research/${id}/personas/${p.id}/chat`)}
        />
      ))}
    </div>
  );
}

function SurveyTab({ id, done }: { id: string; done: boolean }) {
  const [data, setData] = useState<SurveyQuestion[] | null>(null);
  useEffect(() => {
    if (done) researchApi.survey(id).then(setData).catch(() => setData([]));
  }, [id, done]);
  if (!done) return <PendingHint done={false} />;
  if (!data) return <Spinner />;
  return (
    <div className="list">
      {data.map((q) => (
        <div key={q.id} className="card survey-q">
          <div className="survey-q-head">
            <span className="chip chip-type">{q.question_type}</span>
            <span className="muted">{q.slug}</span>
          </div>
          <p className="survey-q-text">{q.text}</p>
          {q.options && (
            <div className="tag-row">
              {q.options.map((o, i) => (
                <span key={i} className="tag">
                  {o}
                </span>
              ))}
            </div>
          )}
          <p className="muted survey-rationale">Why: {q.rationale}</p>
        </div>
      ))}
    </div>
  );
}

function ResponsesTab({ id, done }: { id: string; done: boolean }) {
  const [responses, setResponses] = useState<SurveyResponseItem[] | null>(null);
  const [questions, setQuestions] = useState<SurveyQuestion[]>([]);
  useEffect(() => {
    if (done) {
      Promise.all([researchApi.responses(id), researchApi.survey(id)])
        .then(([r, q]) => {
          setResponses(r);
          setQuestions(q);
        })
        .catch(() => setResponses([]));
    }
  }, [id, done]);
  if (!done) return <PendingHint done={false} />;
  if (!responses) return <Spinner />;
  const qText = new Map(questions.map((q) => [q.id, q.text]));
  const byPersona = new Map<string, SurveyResponseItem[]>();
  responses.forEach((r) => {
    byPersona.set(r.persona_slug, [...(byPersona.get(r.persona_slug) ?? []), r]);
  });
  return (
    <div className="list">
      {[...byPersona.entries()].map(([slug, items]) => (
        <div key={slug} className="card">
          <h3 className="persona-slug-head">{slug}</h3>
          {items.map((r) => (
            <div key={r.id} className="response-item">
              <p className="response-q">{qText.get(r.question_id) ?? r.question_id}</p>
              <p className="response-a">{r.answer}</p>
              <span className={`chip chip-sentiment chip-${r.sentiment}`}>
                {r.sentiment} · {(r.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function InsightsTab({ id, done }: { id: string; done: boolean }) {
  const [data, setData] = useState<InsightReport | null | "empty">(null);
  useEffect(() => {
    if (done)
      researchApi
        .insights(id)
        .then((r) => setData(r ?? "empty"))
        .catch(() => setData("empty"));
  }, [id, done]);
  if (!done) return <PendingHint done={false} />;
  if (data === null) return <Spinner />;
  if (data === "empty") return <PendingHint done />;
  return (
    <div className="insights">
      <div className="banner banner-warn">{data.disclaimer}</div>
      <div className="card">
        <h3>Executive summary</h3>
        <p>{data.executive_summary}</p>
        <p className="muted">Overall sentiment: {data.overall_sentiment}</p>
      </div>
      <div className="card">
        <h3>Key themes</h3>
        {data.themes.map((t) => (
          <div key={t.id} className="theme">
            <div className="theme-head">
              <strong>{t.title}</strong>
              <span className={`chip chip-${t.prevalence}`}>{t.prevalence}</span>
            </div>
            <p>{t.description}</p>
            {t.supporting_persona_ids.length > 0 && (
              <p className="muted">Supported by: {t.supporting_persona_ids.join(", ")}</p>
            )}
          </div>
        ))}
      </div>
      <div className="two-col">
        <div className="card">
          <h3>Weak areas / risks</h3>
          <ul>
            {data.weak_areas_or_risks.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3>Recommendations</h3>
          <ul>
            {data.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      </div>
      {data.notable_quotes.length > 0 && (
        <div className="card">
          <h3>Notable quotes</h3>
          <ul>
            {data.notable_quotes.map((q, i) => (
              <li key={i} className="quote">
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function DownloadReport({ id }: { id: string }) {
  const { toast } = useToast();
  const [busy, setBusy] = useState(false);
  const download = async () => {
    setBusy(true);
    try {
      const blob = await researchApi.reportBlob(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `research_report_${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Download failed.", "error");
    } finally {
      setBusy(false);
    }
  };
  return (
    <button className="btn btn-primary btn-sm" onClick={download} disabled={busy}>
      {busy ? "Preparing…" : "Download PDF"}
    </button>
  );
}
