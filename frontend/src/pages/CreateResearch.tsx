import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { researchApi } from "../api/endpoints";
import { useToast } from "../context/ToastContext";
import type { CreateResearchInput } from "../types";

const initial: CreateResearchInput = {
  title: "",
  product_description: "",
  target_audience: "",
  research_goal: "",
  num_personas: 5,
  num_questions: 6,
};

export function CreateResearch() {
  const [form, setForm] = useState<CreateResearchInput>(initial);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const set = <K extends keyof CreateResearchInput>(k: K, v: CreateResearchInput[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (form.title.trim().length < 1) e.title = "Title is required.";
    if (form.product_description.trim().length < 10)
      e.product_description = "Describe the product in at least 10 characters.";
    if (form.target_audience.trim().length < 5) e.target_audience = "Describe the target audience.";
    if (form.research_goal.trim().length < 5) e.research_goal = "State a research goal.";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setBusy(true);
    try {
      const project = await researchApi.create(form);
      toast("Research started — generating personas…", "success");
      navigate(`/research/${project.id}`);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Could not start research.", "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page page-narrow">
      <div className="page-head">
        <div>
          <h1>Create research</h1>
          <p className="muted">
            Describe your product and audience. The AI pipeline will generate synthetic personas, a
            survey, in-character responses and an insight report.
          </p>
        </div>
      </div>

      <form className="card form" onSubmit={onSubmit}>
        <label>
          Project title
          <input value={form.title} onChange={(e) => set("title", e.target.value)} />
          {errors.title && <span className="field-error">{errors.title}</span>}
        </label>

        <label>
          Product description
          <textarea
            rows={4}
            value={form.product_description}
            placeholder="What is the product and what does it do?"
            onChange={(e) => set("product_description", e.target.value)}
          />
          {errors.product_description && (
            <span className="field-error">{errors.product_description}</span>
          )}
        </label>

        <label>
          Target audience
          <textarea
            rows={3}
            value={form.target_audience}
            placeholder="Who is it for?"
            onChange={(e) => set("target_audience", e.target.value)}
          />
          {errors.target_audience && <span className="field-error">{errors.target_audience}</span>}
        </label>

        <label>
          Research goal
          <textarea
            rows={3}
            value={form.research_goal}
            placeholder="What decision should this research inform?"
            onChange={(e) => set("research_goal", e.target.value)}
          />
          {errors.research_goal && <span className="field-error">{errors.research_goal}</span>}
        </label>

        <div className="form-row">
          <label>
            Personas: <strong>{form.num_personas}</strong>
            <input
              type="range"
              min={2}
              max={10}
              value={form.num_personas}
              onChange={(e) => set("num_personas", Number(e.target.value))}
            />
          </label>
          <label>
            Survey questions: <strong>{form.num_questions}</strong>
            <input
              type="range"
              min={3}
              max={15}
              value={form.num_questions}
              onChange={(e) => set("num_questions", Number(e.target.value))}
            />
          </label>
        </div>

        <div className="form-actions">
          <button className="btn btn-secondary" type="button" onClick={() => navigate("/")}>
            Cancel
          </button>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Starting…" : "Run research"}
          </button>
        </div>
      </form>
    </div>
  );
}
