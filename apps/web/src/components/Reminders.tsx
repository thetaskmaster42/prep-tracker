import { useState } from "react";

import { useReminderMutations, useReminders } from "../hooks/queries";
import { DAY_NAMES, daysLabel } from "../lib/date";
import { NotifNote } from "./NotifNote";
import { useToast } from "./Toast";

export function Reminders() {
  const toast = useToast();
  const reminders = useReminders();
  const { create, toggle, remove } = useReminderMutations();

  const [title, setTitle] = useState("");
  const [time, setTime] = useState("19:00");
  const [days, setDays] = useState<Set<number>>(new Set());

  function toggleDay(i: number) {
    setDays((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const daysStr = [...days].sort((a, b) => a - b).join(",");
      await create.mutateAsync({ title, remind_time: time, days: daysStr });
      setTitle("");
      setDays(new Set());
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to add reminder");
    }
  }

  const list = reminders.data ?? [];

  return (
    <section>
      <h2>Reminders</h2>
      {list.length === 0 ? (
        <p className="empty">
          No reminders yet. Schedule your daily blocks — they fire as notifications while this page is open.
        </p>
      ) : (
        <ul className="rems">
          {list.map((r) => (
            <li key={r.id} className={`rem ${r.enabled ? "" : "off"}`.trim()}>
              <span className="r-time">{r.remind_time}</span>
              <div className="r-body">
                <div className="r-title">{r.title}</div>
                <div className="r-days">{daysLabel(r.days)}</div>
              </div>
              <button className="r-toggle" aria-label="Toggle reminder" onClick={() => toggle.mutate(r.id)}>
                {r.enabled ? "⏸" : "▶"}
              </button>
              <button className="r-del" aria-label="Delete reminder" onClick={() => remove.mutate(r.id)}>
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="card">
        <form className="stack" onSubmit={submit}>
          <div>
            <label className="f" htmlFor="rTitle">
              Remind me to
            </label>
            <input
              id="rTitle"
              placeholder="e.g. LeetCode hour"
              required
              maxLength={200}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="f" htmlFor="rTime">
              At
            </label>
            <input id="rTime" type="time" required value={time} onChange={(e) => setTime(e.target.value)} />
          </div>
          <div>
            <label className="f">On days (none selected = every day)</label>
            <div className="daypick">
              {DAY_NAMES.map((d, i) => (
                <label key={d}>
                  <input type="checkbox" value={i} checked={days.has(i)} onChange={() => toggleDay(i)} />
                  <span>{d}</span>
                </label>
              ))}
            </div>
          </div>
          <button className="btn" type="submit">
            Add reminder
          </button>
        </form>
        <NotifNote />
      </div>
    </section>
  );
}
