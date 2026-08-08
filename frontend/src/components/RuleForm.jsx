import { useState } from "react";
import { RULE_TYPES } from "../ruleTypes";
import { createRule, updateRule } from "../api";
import { tierFor } from "./SeverityBadge";

function initialScopeFor(rule) {
  if (!rule) return {};
  // Any stored "agent_ids" array needs to become the comma-separated
  // string the text field expects; everything else passes through as-is.
  if (Array.isArray(rule.scope.agent_ids)) {
    return { ...rule.scope, agent_ids: rule.scope.agent_ids.join(", ") };
  }
  return rule.scope;
}

function initialParamsFor(rule) {
  if (!rule) return {};
  const config = RULE_TYPES[rule.rule_type];
  // Stored percent fields are fractions (0.8); the input shows whole
  // numbers (80), so convert back on the way in, mirroring the /100 on submit.
  return Object.fromEntries(
    config.paramsFields.map((f) => [f.name, f.isPercent ? rule.params[f.name] * 100 : rule.params[f.name]])
  );
}

export default function RuleForm({ onCreated, onCancel, initialRule }) {
  const isEditing = Boolean(initialRule);
  const [ruleType, setRuleType] = useState(initialRule?.rule_type ?? "queue_backlog");
  const [scope, setScope] = useState(() => initialScopeFor(initialRule));
  const [params, setParams] = useState(() => initialParamsFor(initialRule));
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

  // Normalized once, used for both the live preview and the submit payload.
  // Any "agent_ids" field is a raw string while the user is typing (comma
  // and/or whitespace separated — "a_31, a_11" and "a_31 a_11" both work)
  // and needs to become a real array; every other field is just trimmed.
  const normalizedScope = Object.fromEntries(
    config.scopeFields.map((f) => {
      const raw = scope[f.name] || "";
      if (f.name === "agent_ids") {
        return [f.name, raw.split(/[,\s]+/).map((s) => s.trim()).filter(Boolean)];
      }
      return [f.name, raw.trim()];
    })
  );
  const normalizedParams = Object.fromEntries(
    config.paramsFields.map((f) => {
      const raw = Number(params[f.name]) || 0;
      return [f.name, f.isPercent ? raw / 100 : raw];
    })
  );

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
        <label htmlFor="rule-type">Rule type</label>
        <select id="rule-type" value={ruleType} onChange={handleRuleTypeChange} disabled={isEditing}>
          {Object.entries(RULE_TYPES).map(([key, cfg]) => (
            <option key={key} value={key}>
              {cfg.label}
            </option>
          ))}
        </select>
      </div>

      {config.scopeFields.map((f) => (
        <div className="form-group" key={f.name}>
          <label htmlFor={`scope-${f.name}`}>{f.label}</label>
          <input
            id={`scope-${f.name}`}
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
          <label htmlFor={`params-${f.name}`}>{f.label}</label>
          <input
            id={`params-${f.name}`}
            name={f.name}
            type={f.type}
            min={f.isPercent ? 1 : f.type === "number" ? 1 : undefined}
            max={f.isPercent ? 100 : undefined}
            value={params[f.name] || ""}
            onChange={handleField(setParams)}
            required
          />
        </div>
      ))}

      <div className="form-group">
        <label htmlFor="recipient-id">Notify (recipient id)</label>
        <input
          id="recipient-id"
          value={recipientId}
          onChange={(e) => setRecipientId(e.target.value)}
          placeholder="lead_maria"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="severity">Severity, 1–10 (higher = more urgent, shown first)</label>
        <input
          id="severity"
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
