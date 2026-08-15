export const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/** Local-date ISO string (YYYY-MM-DD) — matches how the backend keys days. */
export function iso(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function formatMinutes(m: number): string {
  if (m >= 60) {
    const h = Math.floor(m / 60);
    const rem = m % 60;
    return `${h}h${rem ? `${rem}m` : ""}`;
  }
  return `${m}m`;
}

export function daysLabel(days: string): string {
  if (!days) return "every day";
  return days
    .split(",")
    .map((n) => DAY_NAMES[+n])
    .join(" ");
}

export function formatActivityDate(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function activityLabel(count: number, isoDate: string, noun: string): string {
  const plural = count === 1 ? "" : "s";
  return count === 0
    ? `No ${noun}s on ${formatActivityDate(isoDate)}`
    : `${count} ${noun}${plural} on ${formatActivityDate(isoDate)}`;
}
