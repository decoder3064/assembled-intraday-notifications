import { deleteNotification, resolveNotification, unresolveNotification } from "../api";
import SeverityBadge, { tierFor } from "./SeverityBadge";

export default function NotificationFeed({ notifications, resolved, onChanged }) {
  const resolve = async (n) => {
    await resolveNotification(n.id);
    onChanged();
  };

  const undo = async (n) => {
    await unresolveNotification(n.id);
    onChanged();
  };

  const remove = async (n) => {
    if (!window.confirm("Delete this notification permanently? This can't be undone.")) return;
    await deleteNotification(n.id);
    onChanged();
  };

  if (notifications.length === 0) {
    return (
      <p className="empty-state">
        {resolved ? "Nothing resolved yet." : "Nothing's fired yet. This updates automatically."}
      </p>
    );
  }

  return (
    <ul className="card-list">
      {notifications.map((n) => (
        <li
          className={`notification-card notification-card--${tierFor(n.severity)}${resolved ? " notification-card--resolved" : ""}`}
          key={n.id}
        >
          <div className="rule-card-top">
            <SeverityBadge severity={n.severity} />
            <span className="notification-time">{new Date(n.sent_at).toLocaleTimeString()}</span>
          </div>
          <p className="notification-message">{n.message}</p>
          <div className="rule-card-bottom">
            <span className="rule-recipient">to {n.recipient_id}</span>
            <div className="rule-card-actions">
              {resolved ? (
                <button className="btn btn-small btn-outline" onClick={() => undo(n)}>
                  Undo
                </button>
              ) : (
                <button className="btn btn-small btn-outline" onClick={() => resolve(n)}>
                  Resolve
                </button>
              )}
              <button className="btn btn-small btn-outline btn-danger" onClick={() => remove(n)}>
                Delete
              </button>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
