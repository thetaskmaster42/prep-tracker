import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Reminder } from "../api/types";
import { useReminderScheduler } from "./useReminderScheduler";

function reminder(overrides: Partial<Reminder> = {}): Reminder {
  return {
    id: 1,
    title: "LeetCode hour",
    remind_time: "19:00",
    days: "",
    enabled: 1,
    created_at: "",
    ...overrides,
  };
}

describe("useReminderScheduler", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Thursday 2026-08-13 at 19:00 local time.
    vi.setSystemTime(new Date(2026, 7, 13, 19, 0, 0));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("fires a due reminder exactly once and dedupes on the next tick", () => {
    const toast = vi.fn();
    renderHook(() => useReminderScheduler([reminder()], toast));

    expect(toast).toHaveBeenCalledTimes(1);
    expect(toast).toHaveBeenCalledWith("⏰ LeetCode hour");

    vi.advanceTimersByTime(20000);
    expect(toast).toHaveBeenCalledTimes(1); // deduped within the same minute
  });

  it("skips disabled reminders and non-matching times", () => {
    const toast = vi.fn();
    renderHook(() =>
      useReminderScheduler(
        [reminder({ id: 2, enabled: 0 }), reminder({ id: 3, remind_time: "08:00" })],
        toast,
      ),
    );
    expect(toast).not.toHaveBeenCalled();
  });

  it("respects the weekday filter (Mon=0)", () => {
    const toast = vi.fn();
    // 2026-08-13 is a Thursday -> weekday index 3.
    renderHook(() => useReminderScheduler([reminder({ days: "0,1" })], toast));
    expect(toast).not.toHaveBeenCalled();
  });
});
