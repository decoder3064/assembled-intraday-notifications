export function tierFor(severity) {
  if (severity >= 6) return "high";
  if (severity >= 3) return "mid";
  return "low";
}

// A person doesn't need to think in a 1–10 scale — three levels is plenty.
// The number still exists underneath (storage/sort order, unchanged), these
// are just representative values that land in the matching tierFor() bucket.
export const SEVERITY_LEVELS = [
  { value: 2, tier: "low", label: "Low" },
  { value: 5, tier: "mid", label: "Medium" },
  { value: 9, tier: "high", label: "High" },
];

const TIER_LABEL = { low: "Low", mid: "Medium", high: "High" };

export default function SeverityBadge({ severity }) {
  const tier = tierFor(severity);
  return <span className={`severity-badge severity-badge--${tier}`}>{TIER_LABEL[tier]}</span>;
}
