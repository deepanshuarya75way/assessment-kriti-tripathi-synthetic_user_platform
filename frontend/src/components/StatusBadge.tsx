import type { ResearchStatus } from "../types";

const LABEL: Record<ResearchStatus, string> = {
  PENDING: "Pending",
  RUNNING: "Running",
  COMPLETED: "Completed",
  FAILED: "Failed",
};

export function StatusBadge({ status }: { status: ResearchStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{LABEL[status]}</span>;
}
