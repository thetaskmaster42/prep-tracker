import { useState } from "react";

import type { Task } from "../api/types";
import { useTaskMutations, useTasks } from "../hooks/queries";
import { iso } from "../lib/date";
import { TaskForm } from "./TaskForm";
import { TaskList } from "./TaskList";
import { useToast } from "./Toast";

export function WorkLog() {
  const toast = useToast();
  const [viewDate, setViewDate] = useState(() => new Date());
  const day = iso(viewDate);
  const tasks = useTasks(day);
  const { create, patch, remove } = useTaskMutations(day);

  const todayStr = iso(new Date());
  const label = day === todayStr ? `${day} · today` : day;

  function shift(delta: number) {
    setViewDate((d) => {
      const next = new Date(d);
      next.setDate(next.getDate() + delta);
      return next;
    });
  }

  async function add(values: { title: string; category: string; planned_min: number; notes: string }) {
    try {
      await create.mutateAsync({ ...values, task_date: day });
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to add task");
    }
  }

  return (
    <section>
      <h2>Work log</h2>
      <div className="datebar">
        <button aria-label="Previous day" onClick={() => shift(-1)}>
          ‹
        </button>
        <span className="d">{label}</span>
        <button aria-label="Next day" onClick={() => shift(1)}>
          ›
        </button>
        <button className="todaybtn" onClick={() => setViewDate(new Date())}>
          Today
        </button>
      </div>

      <TaskList
        tasks={tasks.data?.tasks ?? []}
        onToggle={(t: Task) => patch.mutate({ id: t.id, body: { done: !t.done } })}
        onDelete={(t: Task) => remove.mutate(t.id)}
      />

      <TaskForm onSubmit={add} />
    </section>
  );
}
