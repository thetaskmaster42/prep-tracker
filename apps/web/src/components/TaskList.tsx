import type { Task } from "../api/types";

interface Props {
  tasks: Task[];
  onToggle: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export function TaskList({ tasks, onToggle, onDelete }: Props) {
  if (tasks.length === 0) {
    return (
      <p className="empty">
        Nothing logged for this day. Add the first task below — done tasks feed the streak.
      </p>
    );
  }
  return (
    <ul className="tasks">
      {tasks.map((t) => (
        <li key={t.id} className={`task ${t.done ? "done" : ""}`.trim()}>
          <button className="t-check" aria-label="Toggle done" onClick={() => onToggle(t)}>
            ✓
          </button>
          <div className="t-body">
            <div className="t-title">{t.title}</div>
            <div className="t-meta">
              <span className={`chip ${t.category}`}>{t.category}</span>
              <span>{t.planned_min}m</span>
              {t.notes && <span className="t-notes">{t.notes}</span>}
            </div>
          </div>
          <button className="t-del" aria-label="Delete task" onClick={() => onDelete(t)}>
            ✕
          </button>
        </li>
      ))}
    </ul>
  );
}
