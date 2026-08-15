import { Header } from "./components/Header";
import { Reminders } from "./components/Reminders";
import { useToast } from "./components/Toast";
import { WorkLog } from "./components/WorkLog";
import { useReminders } from "./hooks/queries";
import { useMidnightRefresh } from "./hooks/useMidnightRefresh";
import { useReminderScheduler } from "./hooks/useReminderScheduler";

export function App() {
  const toast = useToast();
  const reminders = useReminders();
  useReminderScheduler(reminders.data ?? [], toast);
  useMidnightRefresh();

  return (
    <>
      <Header />
      <div className="wrap">
        <main>
          <WorkLog />
          <Reminders />
        </main>
      </div>
    </>
  );
}
