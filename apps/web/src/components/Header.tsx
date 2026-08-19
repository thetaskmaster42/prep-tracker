import { useState } from "react";

import {
  useGithubActivity,
  useGithubStreak,
  useLeetcodeActivity,
  useLeetcodeStreak,
  useSettings,
  useStats,
} from "../hooks/queries";
import { formatMinutes } from "../lib/date";
import { ActivityStrip } from "./ActivityStrip";
import { Heatmap } from "./Heatmap";
import { SettingsPanel } from "./SettingsPanel";
import type { UseQueryResult } from "@tanstack/react-query";
import type { StreakResult } from "../api/types";

function ExternalStreakTile({
  query,
  label,
  source,
}: {
  query: UseQueryResult<StreakResult>;
  label: string;
  source: string;
}) {
  let value = "–";
  let unset = false;
  let title: string | undefined;
  if (query.isLoading) {
    value = "…";
  } else if (query.isError) {
    value = "!";
    title = query.error instanceof Error ? query.error.message : undefined;
  } else if (query.data?.configured) {
    value = String(query.data.streak);
    title = `${query.data.username} on ${source}`;
  } else {
    value = "set up";
    unset = true;
    title = `Click ⚙ to add your ${source} username`;
  }
  return (
    <div className="stat">
      <div className={`v ${unset ? "unset" : ""}`.trim()} title={title}>
        {value}
      </div>
      <div className="k">{label}</div>
    </div>
  );
}

export function Header() {
  const [panelOpen, setPanelOpen] = useState(false);
  const stats = useStats();
  const settings = useSettings();
  const ghStreak = useGithubStreak();
  const lcStreak = useLeetcodeStreak();
  const ghActivity = useGithubActivity();
  const lcActivity = useLeetcodeActivity();

  const streak = stats.data?.streak ?? 0;
  const today = stats.data?.today ?? { total: 0, done: 0, minutes_done: 0 };

  const ghConfigured = ghActivity.data?.configured && ghActivity.data.days;
  const lcConfigured = lcActivity.data?.configured && lcActivity.data.days;
  const sideVisible = ghConfigured || lcConfigured;

  return (
    <header>
      <div className="wrap header-grid">
        <div className="header-main">
          <div className="board">
            <div className="brand">
              Prep Tracker · daily training log
              <button
                className="settings-btn"
                aria-label="Streak source settings"
                title="GitHub / LeetCode usernames"
                onClick={() => setPanelOpen((v) => !v)}
              >
                ⚙
              </button>
            </div>
            <div>
              <div className={`streak-num ${streak === 0 ? "zero" : ""}`.trim()}>{streak}</div>
              <div className="streak-label">day streak</div>
            </div>
            <div className="board-stats">
              <div className="stat">
                <div className="v">{stats.data?.best_streak ?? 0}</div>
                <div className="k">best streak</div>
              </div>
              <div className="stat">
                <div className="v">
                  {today.done}/{today.total}
                </div>
                <div className="k">today done</div>
              </div>
              <div className="stat">
                <div className="v">{formatMinutes(today.minutes_done)}</div>
                <div className="k">time logged</div>
              </div>
              <ExternalStreakTile query={ghStreak} label="github streak" source="GitHub" />
              <ExternalStreakTile query={lcStreak} label="leetcode streak" source="LeetCode" />
            </div>
            {panelOpen && <SettingsPanel settings={settings.data} onClose={() => setPanelOpen(false)} />}
          </div>
          <Heatmap cells={stats.data?.heatmap ?? []} />
        </div>

        {sideVisible && (
          <div className="header-side">
            {ghConfigured && (
              <section className="card gh-activity">
                <h2>GitHub · last 30 days</h2>
                <ActivityStrip variant="ghheat" days={ghActivity.data!.days!} noun="contribution" />
                <p className="gh-activity-meta">
                  {ghActivity.data!.total} contribution{ghActivity.data!.total === 1 ? "" : "s"} in the last 30 days ·{" "}
                  {ghActivity.data!.username} on GitHub
                </p>
              </section>
            )}
            {lcConfigured && (
              <section className="card lc-activity">
                <h2>LeetCode · last 30 days</h2>
                <ActivityStrip variant="lcheat" days={lcActivity.data!.days!} noun="submission" />
                <p className="lc-activity-meta">
                  {lcActivity.data!.total} submission{lcActivity.data!.total === 1 ? "" : "s"} in the last 30 days ·{" "}
                  {lcActivity.data!.username} on LeetCode
                </p>
              </section>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
