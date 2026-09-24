import type { Persona } from "../types";

interface Props {
  persona: Persona;
  onChat?: (persona: Persona) => void;
  expandable?: boolean;
}

export function PersonaCard({ persona, onChat }: Props) {
  return (
    <article className="card persona-card">
      <header className="persona-card-head">
        <div>
          <h3>{persona.name}</h3>
          <p className="muted">
            {persona.age} · {persona.occupation}
          </p>
        </div>
        <span className={`chip chip-${persona.tech_savviness}`}>tech: {persona.tech_savviness}</span>
      </header>

      <p className="persona-summary">{persona.persona_summary}</p>

      <details>
        <summary>Details</summary>
        <div className="persona-details">
          <Field label="Goals" items={persona.goals} />
          <Field label="Pain points" items={persona.pain_points} />
          <Field label="Personality" items={persona.personality_traits} />
          <Field label="Behavioral patterns" items={persona.behavioral_patterns} />
          <p>
            <strong>Psychological profile:</strong> {persona.psychological_profile}
          </p>
          <p>
            <strong>Communication style:</strong> {persona.communication_style}
          </p>
        </div>
      </details>

      {onChat && (
        <button className="btn btn-secondary btn-sm" onClick={() => onChat(persona)}>
          Chat with {persona.name.split(" ")[0]}
        </button>
      )}
    </article>
  );
}

function Field({ label, items }: { label: string; items: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="persona-field">
      <span className="persona-field-label">{label}</span>
      <div className="tag-row">
        {items.map((it, i) => (
          <span key={i} className="tag">
            {it}
          </span>
        ))}
      </div>
    </div>
  );
}
