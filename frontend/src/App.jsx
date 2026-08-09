import { useEffect, useState, useCallback } from "react";
import RuleForm from "./components/RuleForm";
import RuleList from "./components/RuleList";
import NotificationFeed from "./components/NotificationFeed";
import Modal from "./components/Modal";
import { listRules, listNotifications } from "./api";

export default function App() {
  const [rules, setRules] = useState([]);
  const [activeNotifications, setActiveNotifications] = useState([]);
  const [resolvedNotifications, setResolvedNotifications] = useState([]);
  // null = closed, "new" = create form, a rule object = editing that rule
  const [formTarget, setFormTarget] = useState(null);
  const [showResolved, setShowResolved] = useState(false);

  const refresh = useCallback(async () => {
    setRules(await listRules());
    setActiveNotifications(await listNotifications(false));
    setResolvedNotifications(await listNotifications(true));
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const closeForm = () => setFormTarget(null);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-mark">Intraday Notifications</div>
        <p className="brand-subtitle">Know when something needs your attention — before it becomes a fire.</p>
      </header>

      <main className="app-grid">
        <section className="panel">
          <div className="panel-header">
            <h2>Active rules</h2>
            <button className="btn btn-add" onClick={() => setFormTarget("new")} aria-label="Add rule">
              +
            </button>
          </div>
          <RuleList rules={rules} onChanged={refresh} onEdit={(rule) => setFormTarget(rule)} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Notifications</h2>
          </div>
          <NotificationFeed notifications={activeNotifications} resolved={false} onChanged={refresh} />
        </section>
      </main>

      <section className="panel panel-resolved">
        <button className="resolved-toggle" onClick={() => setShowResolved((v) => !v)} aria-expanded={showResolved}>
          <span>
            {showResolved ? "▾" : "▸"} Resolved ({resolvedNotifications.length})
          </span>
        </button>
        {showResolved && <NotificationFeed notifications={resolvedNotifications} resolved={true} onChanged={refresh} />}
      </section>

      {formTarget && (
        <Modal title={formTarget === "new" ? "Create a rule" : "Edit rule"} onClose={closeForm}>
          <RuleForm
            initialRule={formTarget === "new" ? null : formTarget}
            onCreated={() => {
              closeForm();
              refresh();
            }}
            onCancel={closeForm}
          />
        </Modal>
      )}
    </div>
  );
}
