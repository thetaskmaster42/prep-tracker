import type {
  ActivityResult,
  Reminder,
  ReminderInput,
  Settings,
  Stats,
  StreakResult,
  Task,
  TaskInput,
  TaskList,
  TaskPatch,
} from "./types";

const BASE = "/api/v1";
const JSON_HEADERS = { "Content-Type": "application/json" };

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(detail, res.status);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  categories: () => request<string[]>("/categories"),

  listTasks: (day: string) => request<TaskList>(`/tasks?day=${day}`),
  createTask: (body: TaskInput) =>
    request<Task>("/tasks", { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(body) }),
  patchTask: (id: number, body: TaskPatch) =>
    request<Task>(`/tasks/${id}`, { method: "PATCH", headers: JSON_HEADERS, body: JSON.stringify(body) }),
  deleteTask: (id: number) => request<void>(`/tasks/${id}`, { method: "DELETE" }),

  listReminders: () => request<Reminder[]>("/reminders"),
  createReminder: (body: ReminderInput) =>
    request<Reminder>("/reminders", { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(body) }),
  toggleReminder: (id: number) => request<Reminder>(`/reminders/${id}/toggle`, { method: "PATCH" }),
  deleteReminder: (id: number) => request<void>(`/reminders/${id}`, { method: "DELETE" }),

  stats: () => request<Stats>("/stats"),

  getSettings: () => request<Settings>("/settings"),
  updateSettings: (body: Partial<Settings>) =>
    request<Settings>("/settings", { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(body) }),

  githubStreak: () => request<StreakResult>("/github-streak"),
  leetcodeStreak: () => request<StreakResult>("/leetcode-streak"),
  githubActivity: () => request<ActivityResult>("/github-activity"),
  leetcodeActivity: () => request<ActivityResult>("/leetcode-activity"),
};
