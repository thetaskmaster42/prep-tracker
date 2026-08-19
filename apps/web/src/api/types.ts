export interface Task {
  id: number;
  title: string;
  category: string;
  task_date: string;
  planned_min: number;
  done: boolean;
  notes: string;
  created_at: string;
}

export interface TaskList {
  date: string;
  tasks: Task[];
}

export interface TaskInput {
  title: string;
  category: string;
  task_date: string;
  planned_min: number;
  notes: string;
}

export interface TaskPatch {
  title?: string;
  category?: string;
  task_date?: string;
  planned_min?: number;
  done?: boolean;
  notes?: string;
}

export interface Stats {
  streak: number;
  best_streak: number;
  today: { total: number; done: number; minutes_done: number };
  heatmap: { date: string; count: number }[];
}

export interface Reminder {
  id: number;
  title: string;
  remind_time: string;
  days: string;
  enabled: number;
  created_at: string;
}

export interface ReminderInput {
  title: string;
  remind_time: string;
  days: string;
}

export interface Settings {
  github_username: string | null;
  leetcode_username: string | null;
}

export interface StreakResult {
  configured: boolean;
  username?: string;
  streak?: number;
  total_active_days?: number;
}

export interface ActivityDay {
  date: string;
  count: number;
  level: number;
}

export interface ActivityResult {
  configured: boolean;
  username?: string;
  days?: ActivityDay[];
  total?: number;
}
