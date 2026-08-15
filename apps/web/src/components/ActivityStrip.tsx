import { useState } from "react";

import type { ActivityDay } from "../api/types";
import { activityLabel } from "../lib/date";

interface Props {
  variant: "ghheat" | "lcheat";
  days: ActivityDay[];
  noun: string;
}

interface Tip {
  text: string;
  left: number;
  top: number;
}

/** GitHub/LeetCode 30-day activity strip with a calendar-style hover/focus tooltip. */
export function ActivityStrip({ variant, days, noun }: Props) {
  const [tip, setTip] = useState<Tip | null>(null);

  function showTip(el: HTMLElement, text: string) {
    const rect = el.getBoundingClientRect();
    setTip({ text, left: rect.left + rect.width / 2, top: rect.top });
  }

  return (
    <>
      <div className={variant}>
        {days.map((d) => {
          const label = activityLabel(d.count, d.date, noun);
          return (
            <div
              key={d.date}
              className={`cell l${d.level}`}
              tabIndex={0}
              aria-label={label}
              onMouseEnter={(e) => showTip(e.currentTarget, label)}
              onMouseLeave={() => setTip(null)}
              onFocus={(e) => showTip(e.currentTarget, label)}
              onBlur={() => setTip(null)}
            />
          );
        })}
      </div>
      <div
        className={`gh-tooltip ${tip ? "show" : ""}`}
        role="tooltip"
        style={tip ? { left: tip.left, top: tip.top } : undefined}
      >
        {tip?.text}
      </div>
    </>
  );
}
