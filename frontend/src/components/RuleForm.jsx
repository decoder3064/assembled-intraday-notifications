import { useState } from "react";
import { RULE_TYPES } from "../ruleTypes";
import { KNOWN_AGENTS, KNOWN_QUEUES, formatAgentName } from "../knownEntities";
import { createRule, updateRule } from "../api";
import { tierFor, SEVERITY_LEVELS } from "./SeverityBadge";

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
  // numbers (80), so convert back on the way in, mirroring the /100 on
  // submit. Rounded — fraction * 100 can land on 7.000000000000001 due to
  // floating-point, and percent fields are only ever whole numbers anyway.
  return Object.fromEntries(
    config.paramsFields.map((f) => [f.name, f.isPercent ? Math.round(rule.params[f.name] * 100) : rule.params[f.name]])
  );
}

export default function RuleForm({ onCreated, onCancel, initialRule }) {
  const isEditing = Boolean(initialRule);
  const [ruleType, setRuleType] = useState(initialRule?.rule_type ?? "queue_backlog");
  const [scope, setScope] = useState(() => initialScopeFor(initialRule));
  const [params, setParams] = useState(() => initialParamsFor(initialRule));
  const [severity, setSeverity] = useState(initialRule?.severity ?? RULE_TYPES.queue_backlog.defaultSeverity);
  const [showTypeHint, setShowTypeHint] = useState(false);
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

  const toggleWholeTeam = (fieldName) => (e) => {
    setScope((prev) => ({ ...prev, [fieldName]: e.target.checked ? [...KNOWN_AGENTS] : [] }));
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
        <div className="form-label-row">
          <label htmlFor="rule-type">Rule type</label>
          <button type="button" className="hint-toggle" onClick={() => setShowTypeHint((v) => !v)} aria-expanded={showTypeHint}>
            ⓘ what's this?
          </button>
        </div>
        <select id="rule-type" value={ruleType} onChange={handleRuleTypeChange} disabled={isEditing}>
          {Object.entries(RULE_TYPES).map(([key, cfg]) => (
            <option key={key} value={key}>
              {cfg.label}
            </option>
          ))}
        </select>
        {showTypeHint && <p className="rule-type-hint">{config.hint}</p>}
      </div>

      <p className="rule-preview">{config.describe(normalizedScope, normalizedParams)}</p>

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

          {f.kind === "agents" && (
            <div id={`scope-${f.name}`} className="checkbox-group">
              <label className="checkbox-option checkbox-option--all">
                <input
                  type="checkbox"
                  checked={(scope[f.name] || []).length === KNOWN_AGENTS.length}
                  onChange={toggleWholeTeam(f.name)}
                />
                Whole team
              </label>
              {KNOWN_AGENTS.map((a) => (
                <label key={a} className="checkbox-option">
                  <input
                    type="checkbox"
                    checked={(scope[f.name] || []).includes(a)}
                    onChange={toggleAgent(f.name, a)}
                  />
                  {formatAgentName(a)}
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
        <label id="severity-label">Severity (more urgent shows first)</label>
        <div className="severity-picker" role="radiogroup" aria-labelledby="severity-label">
          {SEVERITY_LEVELS.map((level) => (
            <label key={level.tier} className={`severity-option severity-option--${level.tier}`}>
              <input
                type="radio"
                name="severity"
                value={level.value}
                checked={tierFor(Number(severity) || 0) === level.tier}
                onChange={() => setSeverity(level.value)}
              />
              {level.label}
            </label>
          ))}
        </div>
      </div>

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
