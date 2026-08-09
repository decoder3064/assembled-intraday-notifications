// Fixed lists matching the real sample data (data/events.txt) — verified with
// a script, not guessed. Used to render dropdowns/checkboxes instead of free
// text, so a rule can't reference a queue or agent that doesn't exist.
export const KNOWN_QUEUES = ["billing", "tier_2", "vip"];
export const KNOWN_AGENTS = ["a_05", "a_07", "a_11", "a_19", "a_23", "a_31", "a_42", "a_88"];
