export const RULE_TYPES = {
  queue_backlog: {
    label: "Queue backlog",
    defaultSeverity: 4,
    scopeFields: [{ name: "queue_id", label: "Queue", type: "text", placeholder: "billing" }],
    paramsFields: [{ name: "threshold", label: "Ticket threshold", type: "number" }],
    describe: (scope, params) =>
      `Notify me when ${scope.queue_id || "this queue"} has more than ${params.threshold ?? "?"} tickets waiting`,
  },
  long_call: {
    label: "Long call",
    defaultSeverity: 6,
    scopeFields: [{ name: "agent_ids", label: "Agent IDs (comma separated)", type: "text", placeholder: "a_31, a_11" }],
    paramsFields: [{ name: "duration_min", label: "Minutes threshold", type: "number" }],
    describe: (scope, params) =>
      `Notify me if any of ${(scope.agent_ids || []).join(", ") || "my agents"} has been on one call for over ${params.duration_min ?? "?"} minutes`,
  },
};
