export function tierFor(severity) {
  if (severity >= 6) return "high";
  if (severity >= 3) return "mid";
  return "low";
}

export default function SeverityBadge({ severity }) {
  return <span className={`severity-badge severity-badge--${tierFor(severity)}`}>severity {severity}</span>;
}
