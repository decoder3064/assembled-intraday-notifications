import { formatAgentList, agentsSubject } from "./knownEntities";

export const RULE_TYPES = {
  queue_backlog: {
    label: "Queue backlog",
    hint: "Tells you when too many people are waiting in this queue.",
    defaultSeverity: 5,
    scopeFields: [{ name: "queue_id", label: "Queue", kind: "queue" }],
    paramsFields: [{ name: "threshold", label: "Ticket threshold", type: "number" }],
    describe: (scope, params) =>
      `Notify me when ${scope.queue_id || "this queue"} has more than ${params.threshold ?? "?"} tickets waiting`,
  },
  sla_risk: {
    label: "SLA at risk",
    hint: "Tells you when someone's wait is getting close to how long you promised customers they'd wait.",
    defaultSeverity: 5,
    scopeFields: [{ name: "queue_id", label: "Queue", kind: "queue" }],
    paramsFields: [{ name: "pct_of_sla", label: "Warn at this % of the SLA deadline", type: "number", isPercent: true }],
    describe: (scope, params) =>
      `Warn me when ${scope.queue_id || "this queue"}'s longest wait reaches ${(params.pct_of_sla ?? 0) * 100}% of its SLA deadline`,
  },
  sla_breach: {
    label: "SLA breached",
    hint: "Tells you when someone already waited longer than you promised.",
    defaultSeverity: 9,
    scopeFields: [{ name: "queue_id", label: "Queue", kind: "queue" }],
    paramsFields: [],
    describe: (scope) => `Notify me when ${scope.queue_id || "this queue"} has already missed its SLA`,
  },
  volume_surge: {
    label: "Volume surge",
    hint: "Tells you when way more calls are coming in than you expected.",
    defaultSeverity: 9,
    scopeFields: [{ name: "queue_id", label: "Queue", kind: "queue" }],
    paramsFields: [{ name: "pct_over_forecast", label: "Surge threshold, % over forecast", type: "number", isPercent: true }],
    describe: (scope, params) =>
      `Notify me when ${scope.queue_id || "this queue"}'s call volume runs more than ${(params.pct_over_forecast ?? 0) * 100}% above what was forecasted`,
  },
  zero_coverage: {
    label: "Zero coverage",
    hint: "Tells you when nobody is free to help, and someone needs it.",
    defaultSeverity: 9,
    scopeFields: [{ name: "queue_id", label: "Queue", kind: "queue" }],
    paramsFields: [],
    describe: (scope) => `Notify me when nobody's free in ${scope.queue_id || "this queue"} and tickets are waiting`,
  },
  long_call: {
    label: "Long call",
    hint: "Tells you when one agent has been on the same call for too long.",
    defaultSeverity: 9,
    scopeFields: [{ name: "agent_ids", label: "Agents", kind: "agents" }],
    paramsFields: [{ name: "duration_min", label: "Minutes threshold", type: "number" }],
    describe: (scope, params) => {
      const { subject, has } = agentsSubject(scope.agent_ids);
      return `Notify me if ${subject} ${has} been on one call for over ${params.duration_min ?? "?"} minutes`;
    },
  },
  adherence_escalated: {
    label: "Escalated adherence",
    hint: "Tells you when an agent has been off schedule too long.",
    defaultSeverity: 9,
    scopeFields: [{ name: "agent_ids", label: "Agents", kind: "agents" }],
    paramsFields: [{ name: "duration_min", label: "Minutes threshold", type: "number" }],
    describe: (scope, params) => {
      const { subject, has, hasnt } = agentsSubject(scope.agent_ids);
      return `Notify me if ${subject} ${has} been off-schedule for over ${params.duration_min ?? "?"} minutes and ${hasnt} corrected it`;
    },
  },
  team_adherence_capacity: {
    label: "Team adherence capacity",
    hint: "Tells you when too many agents are off schedule at once.",
    defaultSeverity: 9,
    scopeFields: [{ name: "agent_ids", label: "Agents", kind: "agents" }],
    paramsFields: [{ name: "count_threshold", label: "Alert if more than this many are off-schedule at once", type: "number" }],
    describe: (scope, params) =>
      `Notify me when more than ${params.count_threshold ?? "?"} of ${formatAgentList(scope.agent_ids)} are off-schedule at the same time`,
  },
  occupancy: {
    label: "Occupancy",
    hint: "Tells you when most of your agents are busy, even before anyone starts waiting.",
    defaultSeverity: 5,
    scopeFields: [{ name: "queue_id", label: "Queue", kind: "queue" }],
    paramsFields: [{ name: "occupancy_threshold", label: "Occupancy threshold %", type: "number", isPercent: true }],
    describe: (scope, params) =>
      `Notify me when ${(params.occupancy_threshold ?? 0) * 100}% of ${scope.queue_id || "this queue"}'s agents are busy on calls`,
  },
};
