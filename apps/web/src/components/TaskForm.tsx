import { useState } from "react";

import { useCategories } from "../hooks/queries";

interface Props {
  onSubmit: (values: { title: string; category: string; planned_min: number; notes: string }) => void;
}

export function TaskForm({ onSubmit }: Props) {
  const categories = useCategories();
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [minutes, setMinutes] = useState("60");
  const [notes, setNotes] = useState("");

  const effectiveCategory = category || categories.data?.[0] || "Other";

  function submit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      title,
      category: effectiveCategory,
      planned_min: parseInt(minutes || "0", 10),
      notes,
    });
    setTitle("");
    setNotes("");
  }

  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <form className="stack" onSubmit={submit}>
        <div>
          <label className="f" htmlFor="tTitle">
            Task
          </label>
          <input
            id="tTitle"
            placeholder="e.g. 2 LeetCode mediums — sliding window"
            required
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div className="row2">
          <div>
            <label className="f" htmlFor="tCat">
              Category
            </label>
            <select id="tCat" value={effectiveCategory} onChange={(e) => setCategory(e.target.value)}>
              {(categories.data ?? []).map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="f" htmlFor="tMin">
              Planned minutes
            </label>
            <input
              id="tMin"
              type="number"
              min={0}
              max={1440}
              step={5}
              value={minutes}
              onChange={(e) => setMinutes(e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="f" htmlFor="tNotes">
            Notes (optional)
          </label>
          <textarea
            id="tNotes"
            placeholder="What to cover, links, problem numbers…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <button className="btn" type="submit">
          Add to log
        </button>
      </form>
    </div>
  );
}
