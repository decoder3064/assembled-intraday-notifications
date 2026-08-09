import { useState } from "react";
import { RULE_TYPES } from "../ruleTypes";
import { KNOWN_AGENTS, KNOWN_QUEUES } from "../knownEntities";
import { createRule, updateRule } from "../api";
import { tierFor } from "./SeverityBadge";

function initialScopeFor(rule) {
  if (!rule) return {};
  // Scope values are already stored in the exact shape the controls need —
  // arrays for "agents" checkboxes, plain strings for "queue"/"agent"
  // dropdowns — so no conversion is needed on the way in.
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

  const toggleAgent = (fieldName, agentId) => (e) => {
    const current = scope[fieldName] || [];
    const next = e.target.checked ? [...current, agentId] : current.filter((a) => a !== agentId);
    setScope((prev) => ({ ...prev, [fieldName]: next }));
  };

  const handleRuleTypeChange = (e) => {
    const nextType = e.target.value;
    setRuleType(nextType);
    setScope({});
    setParams({});
    setSeverity(RULE_TYPES[nextType].defaultSeverity);
  };

  // Normalized once, used for both the live preview and the submit payload.
  // "agents" fields are already a real array (built by the checkboxes);
  // "queue"/"agent" fields are already an exact value (chosen from a
  // dropdown, so there's nothing to typo) — no string parsing needed here
  // at all, unlike the old free-text version of this form.
  const normalizedScope = Object.fromEntries(
    config.scopeFields.map((f) => [f.name, f.kind === "agents" ? scope[f.name] || [] : scope[f.name] || ""])
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

          {f.kind === "queue" && (
            <select id={`scope-${f.name}`} name={f.name} value={scope[f.name] || ""} onChange={handleField(setScope)} required>
              <option value="" disabled>
                Select a queue
              </option>
              {KNOWN_QUEUES.map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
          )}

          {f.kind === "agent" && (
            <select id={`scope-${f.name}`} name={f.name} value={scope[f.name] || ""} onChange={handleField(setScope)} required>
              <option value="" disabled>
                Select an agent
              </option>
              {KNOWN_AGENTS.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          )}

          {f.kind === "agents" && (
            <div id={`scope-${f.name}`} className="checkbox-group">
              {KNOWN_AGENTS.map((a) => (
                <label key={a} className="checkbox-option">
                  <input
                    type="checkbox"
                    checked={(scope[f.name] || []).includes(a)}
                    onChange={toggleAgent(f.name, a)}
                  />
                  {a}
                </label>
              ))}
            </div>
          )}
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
