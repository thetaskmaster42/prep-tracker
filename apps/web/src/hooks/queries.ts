import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import type { ReminderInput, Settings, TaskInput, TaskPatch } from "../api/types";

export const keys = {
  categories: ["categories"] as const,
  stats: ["stats"] as const,
  tasks: (day: string) => ["tasks", day] as const,
  reminders: ["reminders"] as const,
  settings: ["settings"] as const,
  githubStreak: ["github-streak"] as const,
  leetcodeStreak: ["leetcode-streak"] as const,
  githubActivity: ["github-activity"] as const,
  leetcodeActivity: ["leetcode-activity"] as const,
};

export function useCategories() {
  return useQuery({ queryKey: keys.categories, queryFn: api.categories, staleTime: Infinity });
}

export function useStats() {
  return useQuery({ queryKey: keys.stats, queryFn: api.stats });
}

export function useTasks(day: string) {
  return useQuery({ queryKey: keys.tasks(day), queryFn: () => api.listTasks(day) });
}

/** Task mutations invalidate the day's list and the scoreboard together. */
export function useTaskMutations(day: string) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["tasks"] });
    qc.invalidateQueries({ queryKey: keys.stats });
  };
  return {
    create: useMutation({ mutationFn: (body: TaskInput) => api.createTask(body), onSuccess: invalidate }),
    patch: useMutation({
      mutationFn: ({ id, body }: { id: number; body: TaskPatch }) => api.patchTask(id, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: (id: number) => api.deleteTask(id), onSuccess: invalidate }),
    _day: day,
  };
}

export function useReminders() {
  return useQuery({ queryKey: keys.reminders, queryFn: api.listReminders });
}

export function useReminderMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: keys.reminders });
  return {
    create: useMutation({ mutationFn: (body: ReminderInput) => api.createReminder(body), onSuccess: invalidate }),
    toggle: useMutation({ mutationFn: (id: number) => api.toggleReminder(id), onSuccess: invalidate }),
    remove: useMutation({ mutationFn: (id: number) => api.deleteReminder(id), onSuccess: invalidate }),
  };
}

export function useSettings() {
  return useQuery({ queryKey: keys.settings, queryFn: api.getSettings });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Settings>) => api.updateSettings(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.settings });
      qc.invalidateQueries({ queryKey: keys.githubStreak });
      qc.invalidateQueries({ queryKey: keys.leetcodeStreak });
      qc.invalidateQueries({ queryKey: keys.githubActivity });
      qc.invalidateQueries({ queryKey: keys.leetcodeActivity });
    },
  });
}

export function useGithubStreak() {
  return useQuery({ queryKey: keys.githubStreak, queryFn: api.githubStreak });
}
export function useLeetcodeStreak() {
  return useQuery({ queryKey: keys.leetcodeStreak, queryFn: api.leetcodeStreak });
}
export function useGithubActivity() {
  return useQuery({ queryKey: keys.githubActivity, queryFn: api.githubActivity });
}
export function useLeetcodeActivity() {
  return useQuery({ queryKey: keys.leetcodeActivity, queryFn: api.leetcodeActivity });
}
