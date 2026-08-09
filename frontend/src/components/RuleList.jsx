import { RULE_TYPES } from "../ruleTypes";
import { deleteRule, updateRule } from "../api";
import SeverityBadge from "./SeverityBadge";

export default function RuleList({ rules, onChanged, onEdit }) {
  const toggle = async (rule) => {
    await updateRule(rule.id, { enabled: !rule.enabled });
    onChanged();
  };

  const remove = async (rule) => {
    if (!window.confirm(`Delete "${rule.description}"? Its notification history is kept, just no longer linked to a rule.`)) {
      return;
    }
    await deleteRule(rule.id);
    onChanged();
  };

  if (rules.length === 0) {
    return <p className="empty-state">No rules yet — add one to get started.</p>;
  }

  return (
    <ul className="card-list">
      {rules.map((rule) => (
        <li className={`rule-card${rule.enabled ? "" : " rule-card--disabled"}`} key={rule.id}>
          <div className="rule-card-top">
            <div className="rule-card-top-left">
              <button className="btn-icon" onClick={() => onEdit(rule)} aria-label="Edit rule" title="Edit">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 20h9" strokeLinecap="round" />
                  <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" strokeLinejoin="round" />
                </svg>
              </button>
              <span className="rule-type-tag">{RULE_TYPES[rule.rule_type]?.label ?? rule.rule_type}</span>
            </div>
            <SeverityBadge severity={rule.severity} />
          </div>
          <p className="rule-description">{rule.description}</p>
          <div className="rule-card-bottom">
            <span className="rule-recipient">notifies {rule.recipient_id}</span>
            <div className="rule-card-actions">
              <button className="btn btn-small btn-outline" onClick={() => toggle(rule)}>
                {rule.enabled ? "Disable" : "Enable"}
              </button>
              <button className="btn btn-small btn-outline btn-danger" onClick={() => remove(rule)}>
                Delete
              </button>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
