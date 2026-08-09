// Fixed lists matching the real sample data (data/events.txt) — verified with
// a script, not guessed. Used to render dropdowns/checkboxes instead of free
// text, so a rule can't reference a queue or agent that doesn't exist.
// This is one team's data, not an org-wide feed — see decisions.md.
export const KNOWN_QUEUES = ["billing", "tier_2", "vip"];
export const KNOWN_AGENTS = ["a_05", "a_07", "a_11", "a_19", "a_23", "a_31", "a_42", "a_88"];

// "a_19" is an internal ID, not something a person reads comfortably in a
// sentence. Keep the raw ID as the value everywhere it's matched against
// data; only swap in this label where it's displayed to a human.
export function formatAgentName(id) {
  const number = id.replace(/^a_0?/, "");
  return `Agent ${number}`;
}

// Turns an id list into a readable phrase. Once a rule covers the whole
// known roster, naming every agent gets unreadable fast (and since this
// data is one team's roster, "the whole team" says the same thing better
// than a wall of IDs would).
export function formatAgentList(ids) {
  if (!ids || ids.length === 0) return "my agents";
  if (ids.length === KNOWN_AGENTS.length) return "your whole team";

  const names = ids.map(formatAgentName);
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;
}

// For a sentence like "X has/have been off-schedule..." — "any of Agent 11
// has been" doesn't read right for a single named person ("any of" implies
// picking from a group), so a lone agent drops "any of" and takes singular
// agreement; a real group keeps "any of" with plural agreement.
export function agentsSubject(ids) {
  if (ids && ids.length === 1) {
    return { subject: formatAgentName(ids[0]), has: "has", hasnt: "hasn't" };
  }
  return { subject: `any of ${formatAgentList(ids)}`, has: "have", hasnt: "haven't" };
}
