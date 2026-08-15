import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { iso } from "../lib/date";

/** Refresh time-sensitive data (scoreboard, task lists) when the local day rolls over. */
export function useMidnightRefresh() {
  const qc = useQueryClient();
  const day = useRef(iso(new Date()));

  useEffect(() => {
    const id = setInterval(() => {
      const now = iso(new Date());
      if (now !== day.current) {
        day.current = now;
        qc.invalidateQueries({ queryKey: ["stats"] });
        qc.invalidateQueries({ queryKey: ["tasks"] });
      }
    }, 60000);
    return () => clearInterval(id);
  }, [qc]);
}
