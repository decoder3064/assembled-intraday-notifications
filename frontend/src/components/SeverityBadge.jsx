export function tierFor(severity) {
  if (severity >= 6) return "high";
  if (severity >= 3) return "mid";
  return "low";
}

// Representative values landing in each tierFor() bucket — storage stays
// a 1-10 int, the UI only ever shows Low/Medium/High.
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
