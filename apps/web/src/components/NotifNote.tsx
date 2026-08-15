import { useState } from "react";

export function NotifNote() {
  const supported = typeof window !== "undefined" && "Notification" in window;
  const [permission, setPermission] = useState<NotificationPermission | null>(
    supported ? Notification.permission : null,
  );

  if (!supported) {
    return (
      <p className="notif-note">
        This browser doesn't support desktop notifications — reminders will show in-page.
      </p>
    );
  }
  if (permission === "granted") {
    return <p className="notif-note">Desktop notifications are on. Reminders fire while this page is open.</p>;
  }
  if (permission === "denied") {
    return (
      <p className="notif-note">
        Desktop notifications are blocked in browser settings — reminders will show in-page.
      </p>
    );
  }
  return (
    <p className="notif-note">
      Reminders show in-page.{" "}
      <button
        onClick={async () => {
          const result = await Notification.requestPermission();
          setPermission(result);
        }}
      >
        Turn on desktop notifications
      </button>
    </p>
  );
}
