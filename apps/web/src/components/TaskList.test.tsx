import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Task } from "../api/types";
import { TaskList } from "./TaskList";

function task(overrides: Partial<Task> = {}): Task {
  return {
    id: 1,
    title: "2 mediums",
    category: "LeetCode",
    task_date: "2026-08-13",
    planned_min: 45,
    done: false,
    notes: "",
    created_at: "",
    ...overrides,
  };
}

describe("TaskList", () => {
  it("shows the empty state when there are no tasks", () => {
    render(<TaskList tasks={[]} onToggle={() => {}} onDelete={() => {}} />);
    expect(screen.getByText(/Nothing logged for this day/i)).toBeInTheDocument();
  });

  it("renders tasks and wires toggle/delete", () => {
    const onToggle = vi.fn();
    const onDelete = vi.fn();
    render(<TaskList tasks={[task()]} onToggle={onToggle} onDelete={onDelete} />);

    expect(screen.getByText("2 mediums")).toBeInTheDocument();
    expect(screen.getByText("LeetCode")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Toggle done"));
    expect(onToggle).toHaveBeenCalledOnce();

    fireEvent.click(screen.getByLabelText("Delete task"));
    expect(onDelete).toHaveBeenCalledOnce();
  });

  it("marks done tasks with the done class", () => {
    const { container } = render(<TaskList tasks={[task({ done: true })]} onToggle={() => {}} onDelete={() => {}} />);
    expect(container.querySelector("li.task.done")).not.toBeNull();
  });
});
