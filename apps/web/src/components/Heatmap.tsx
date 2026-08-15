import { iso } from "../lib/date";

interface Props {
  cells: { date: string; count: number }[];
}

function levelClass(count: number): string {
  if (count >= 4) return "c3";
  if (count >= 2) return "c2";
  if (count >= 1) return "c1";
  return "";
}

/** Local 12-week completion heatmap (84 cells, oldest first). */
export function Heatmap({ cells }: Props) {
  const today = iso(new Date());
  return (
    <div className="heat" title="Last 12 weeks — days with completed work">
      {cells.map((d) => (
        <div
          key={d.date}
          className={`cell ${levelClass(d.count)} ${d.date === today ? "today" : ""}`.trim()}
          title={`${d.date}: ${d.count} completed`}
        />
      ))}
    </div>
  );
}
