import { useEffect, useState } from "react";

import type { Settings } from "../api/types";
import { useUpdateSettings } from "../hooks/queries";
import { useToast } from "./Toast";

interface Props {
  settings: Settings | undefined;
  onClose: () => void;
}

export function SettingsPanel({ settings, onClose }: Props) {
  const toast = useToast();
  const update = useUpdateSettings();
  const [github, setGithub] = useState("");
  const [leetcode, setLeetcode] = useState("");

  useEffect(() => {
    setGithub(settings?.github_username ?? "");
    setLeetcode(settings?.leetcode_username ?? "");
  }, [settings]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await update.mutateAsync({
        github_username: github.trim(),
        leetcode_username: leetcode.trim(),
      });
      toast("Settings saved");
      onClose();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to save settings");
    }
  }

  return (
    <form className="settings-panel" onSubmit={submit}>
      <div className="f-group">
        <label className="f" htmlFor="ghUser">
          GitHub username
        </label>
        <input id="ghUser" placeholder="octocat" value={github} onChange={(e) => setGithub(e.target.value)} />
      </div>
      <div className="f-group">
        <label className="f" htmlFor="lcUser">
          LeetCode username
        </label>
        <input id="lcUser" placeholder="leetcoder" value={leetcode} onChange={(e) => setLeetcode(e.target.value)} />
      </div>
      <button className="btn" type="submit">
        Save
      </button>
    </form>
  );
}
