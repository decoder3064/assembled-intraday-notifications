import { useState } from "react";
import { RULE_TYPES } from "../ruleTypes";
import { createRule, updateRule } from "../api";
import { tierFor } from "./SeverityBadge";

function initialScopeFor(rule) {
  if (!rule) return {};
  if (rule.rule_type === "long_call") {
    return { agent_ids: (rule.scope.agent_ids || []).join(", ") };
  }
  return rule.scope;
}

export default function RuleForm({ onCreated, onCancel, initialRule }) {
  const isEditing = Boolean(initialRule);
  const [ruleType, setRuleType] = useState(initialRule?.rule_type ?? "queue_backlog");
  const [scope, setScope] = useState(() => initialScopeFor(initialRule));
  const [params, setParams] = useState(() => initialRule?.params ?? {});
  const [recipientId, setRecipientId] = useState(initialRule?.recipient_id ?? "");
  const [severity, setSeverity] = useState(initialRule?.severity ?? RULE_TYPES.queue_backlog.defaultSeverity);
  const config = RULE_TYPES[ruleType];

  const handleField = (setter) => (e) => {
    const { name, value } = e.target;
    setter((prev) => ({ ...prev, [name]: value }));
  };

  const handleRuleTypeChange = (e) => {
    const nextType = e.target.value;
    setRuleType(nextType);
    setScope({});
    setParams({});
    setSeverity(RULE_TYPES[nextType].defaultSeverity);
  };

  // Normalized once, used for both the live preview and the submit payload —
  // scope.agent_ids is a raw string while the user is typing (comma and/or
  // whitespace separated — "a_31, a_11" and "a_31 a_11" both work), and
  // describe() needs a real array either way.
  const normalizedScope =
    ruleType === "long_call"
      ? { agent_ids: (scope.agent_ids || "").split(/[,\s]+/).map((s) => s.trim()).filter(Boolean) }
      : { queue_id: (scope.queue_id || "").trim() };
  const normalizedParams = Object.fromEntries(Object.entries(params).map(([k, v]) => [k, Number(v) || 0]));

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      rule_type: ruleType,
      scope: normalizedScope,
      params: normalizedParams,
      recipient_id: recipientId,
      severity: Number(severity),
      description: config.describe(normalizedScope, normalizedParams),
    };

    if (isEditing) {
      await updateRule(initialRule.id, payload);
    } else {
      await createRule(payload);
      setScope({});
      setParams({});
    }

    onCreated();
  };

  return (
    <form className="rule-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Rule type</label>
        <select value={ruleType} onChange={handleRuleTypeChange} disabled={isEditing}>
          {Object.entries(RULE_TYPES).map(([key, cfg]) => (
            <option key={key} value={key}>
              {cfg.label}
            </option>
          ))}
        </select>
      </div>

      {config.scopeFields.map((f) => (
        <div className="form-group" key={f.name}>
          <label>{f.label}</label>
          <input
            name={f.name}
            type={f.type}
            placeholder={f.placeholder}
            value={scope[f.name] || ""}
            onChange={handleField(setScope)}
            required
          />
        </div>
      ))}

      {config.paramsFields.map((f) => (
        <div className="form-group" key={f.name}>
          <label>{f.label}</label>
          <input
            name={f.name}
            type={f.type}
            min={f.type === "number" ? 1 : undefined}
            value={params[f.name] || ""}
            onChange={handleField(setParams)}
            required
          />
        </div>
      ))}

      <div className="form-group">
        <label>Notify (recipient id)</label>
        <input value={recipientId} onChange={(e) => setRecipientId(e.target.value)} placeholder="lead_maria" required />
      </div>

      <div className="form-group">
        <label>Severity, 1–10 (higher = more urgent, shown first)</label>
        <input
          type="number"
          min={1}
          max={10}
          className={`severity-input severity-input--${tierFor(Number(severity) || 0)}`}
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          required
        />
      </div>

      <p className="rule-preview">{config.describe(normalizedScope, normalizedParams)}</p>

      <div className="form-actions">
        <button type="button" className="btn btn-outline" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          {isEditing ? "Save changes" : "Create rule"}
        </button>
      </div>
    </form>
  );
}
