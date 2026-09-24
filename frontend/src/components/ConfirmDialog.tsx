import type { ReactNode } from "react";

interface Props {
  open: boolean;
  title: string;
  body: ReactNode;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ open, title, body, confirmLabel = "Confirm", onConfirm, onCancel }: Props) {
  if (!open) return null;
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label={title}>
      <div className="modal">
        <h3>{title}</h3>
        <div className="modal-body">{body}</div>
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn-danger" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
