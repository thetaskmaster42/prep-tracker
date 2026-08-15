import { useEffect, useRef } from "react";

import type { Reminder } from "../api/types";
import { iso } from "../lib/date";

/**
 * Fire due reminders while the tab is open — checked every 20s. Mirrors the original
 * client-side scheduler: matches HH:MM + weekday (Mon=0), dedupes per id|date|time, and
 * raises an in-page toast plus a desktop Notification when permission is granted.
 */
export function useReminderScheduler(reminders: Reminder[], toast: (msg: string) => void) {
  const fired = useRef<Set<string>>(new Set());
  const remindersRef = useRef(reminders);
  remindersRef.current = reminders;

  useEffect(() => {
    function check() {
      const now = new Date();
      const hhmm = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
      const weekday = (now.getDay() + 6) % 7; // Mon=0
      const today = iso(now);
      for (const r of remindersRef.current) {
        if (!r.enabled || r.remind_time !== hhmm) continue;
        if (r.days && !r.days.split(",").includes(String(weekday))) continue;
        const key = `${r.id}|${today}|${hhmm}`;
        if (fired.current.has(key)) continue;
        fired.current.add(key);
        toast(`⏰ ${r.title}`);
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification("Prep Tracker", { body: r.title });
        }
      }
    }

    check();
    const id = setInterval(check, 20000);
    return () => clearInterval(id);
  }, [toast]);
}
