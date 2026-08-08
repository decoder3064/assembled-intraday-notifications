export const RULE_TYPES = {
  queue_backlog: {
    label: "Queue backlog",
    defaultSeverity: 4,
    scopeFields: [{ name: "queue_id", label: "Queue", type: "text", placeholder: "billing" }],
    paramsFields: [{ name: "threshold", label: "Ticket threshold", type: "number" }],
    describe: (scope, params) =>
      `Notify me when ${scope.queue_id || "this queue"} has more than ${params.threshold ?? "?"} tickets waiting`,
  },
  sla_risk: {
    label: "SLA at risk",
    defaultSeverity: 3,
    scopeFields: [{ name: "queue_id", label: "Queue", type: "text", placeholder: "billing" }],
    paramsFields: [{ name: "pct_of_sla", label: "Warn at this % of the SLA deadline", type: "number", isPercent: true }],
    describe: (scope, params) =>
      `Warn me when ${scope.queue_id || "this queue"} is close to missing its SLA (${(params.pct_of_sla ?? 0) * 100 || "?"}%)`,
  },
  sla_breach: {
    label: "SLA breached",
    defaultSeverity: 9,
    scopeFields: [{ name: "queue_id", label: "Queue", type: "text", placeholder: "billing" }],
    paramsFields: [],
    describe: (scope) => `Notify me when ${scope.queue_id || "this queue"} has already missed its SLA`,
  },
  volume_surge: {
    label: "Volume surge",
    defaultSeverity: 6,
    scopeFields: [{ name: "queue_id", label: "Queue", type: "text", placeholder: "billing" }],
    paramsFields: [{ name: "pct_over_forecast", label: "Surge threshold, % over forecast", type: "number", isPercent: true }],
    describe: (scope, params) =>
      `Notify me when ${scope.queue_id || "this queue"}'s volume is running well above what was forecasted (>${(params.pct_over_forecast ?? 0) * 100 || "?"}%)`,
  },
  zero_coverage: {
    label: "Zero coverage",
    defaultSeverity: 10,
    scopeFields: [{ name: "queue_id", label: "Queue", type: "text", placeholder: "billing" }],
    paramsFields: [],
    describe: (scope) => `Notify me when nobody's free in ${scope.queue_id || "this queue"} and tickets are waiting`,
  },
  long_call: {
    label: "Long call",
    defaultSeverity: 6,
    scopeFields: [{ name: "agent_ids", label: "Agent IDs (comma separated)", type: "text", placeholder: "a_31, a_11" }],
    paramsFields: [{ name: "duration_min", label: "Minutes threshold", type: "number" }],
    describe: (scope, params) =>
      `Notify me if any of ${(scope.agent_ids || []).join(", ") || "my agents"} has been on one call for over ${params.duration_min ?? "?"} minutes`,
  },
  adherence_self: {
    label: "Off-schedule nudge (self)",
    defaultSeverity: 2,
    scopeFields: [{ name: "agent_id", label: "Your agent ID", type: "text", placeholder: "a_19" }],
    paramsFields: [{ name: "duration_min", label: "Minutes threshold", type: "number" }],
    describe: (scope, params) =>
      `Privately let ${scope.agent_id || "me"} know if they've been off-schedule for over ${params.duration_min ?? "?"} minutes`,
  },
  adherence_escalated: {
    label: "Escalated adherence",
    defaultSeverity: 9,
    scopeFields: [{ name: "agent_ids", label: "Agent IDs (comma separated)", type: "text", placeholder: "a_31, a_11" }],
    paramsFields: [{ name: "duration_min", label: "Minutes threshold", type: "number" }],
    describe: (scope, params) =>
      `Notify me if any of ${(scope.agent_ids || []).join(", ") || "my agents"} has been off-schedule for over ${params.duration_min ?? "?"} minutes and hasn't fixed it`,
  },
  team_adherence_capacity: {
    label: "Team adherence capacity",
    defaultSeverity: 8,
    scopeFields: [{ name: "agent_ids", label: "Agent IDs (comma separated)", type: "text", placeholder: "a_31, a_11" }],
    paramsFields: [{ name: "count_threshold", label: "Alert if more than this many are off-schedule at once", type: "number" }],
    describe: (scope, params) =>
      `Notify me when more than ${params.count_threshold ?? "?"} of ${(scope.agent_ids || []).join(", ") || "my agents"} are off-schedule at the same time`,
  },
  occupancy: {
    label: "Occupancy",
    defaultSeverity: 5,
    scopeFields: [{ name: "queue_id", label: "Queue", type: "text", placeholder: "billing" }],
    paramsFields: [{ name: "occupancy_threshold", label: "Occupancy threshold %", type: "number", isPercent: true }],
    describe: (scope, params) =>
      `Notify me when ${scope.queue_id || "this queue"}'s occupancy crosses ${(params.occupancy_threshold ?? 0) * 100 || "?"}%`,
  },
};
