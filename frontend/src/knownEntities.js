// Matches the real sample data (data/events.txt) — one team's roster, not
// an org-wide directory. Used for dropdowns/checkboxes so a rule can't
// reference a queue or agent that doesn't exist.
export const KNOWN_QUEUES = ["billing", "tier_2", "vip"];
export const KNOWN_AGENTS = ["a_05", "a_07", "a_11", "a_19", "a_23", "a_31", "a_42", "a_88"];

// Raw id stays the matched value everywhere; this is only the display label.
export function formatAgentName(id) {
  const number = id.replace(/^a_0?/, "");
  return `Agent ${number}`;
}

// Collapses to "your whole team" once a selection covers the full roster —
// naming all 8 gets unreadable fast.
export function formatAgentList(ids) {
  if (!ids || ids.length === 0) return "my agents";
  if (ids.length === KNOWN_AGENTS.length) return "your whole team";

  const names = ids.map(formatAgentName);
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;
}

// "any of Agent 11 has been" reads wrong for a single person — drop "any of"
// and use singular agreement when there's only one.
export function agentsSubject(ids) {
  if (ids && ids.length === 1) {
    return { subject: formatAgentName(ids[0]), has: "has", hasnt: "hasn't" };
  }
  return { subject: `any of ${formatAgentList(ids)}`, has: "have", hasnt: "haven't" };
}
