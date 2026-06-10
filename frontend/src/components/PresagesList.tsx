import type { Presage } from "../types";

interface Props {
  presages: Presage[];
}

export function PresagesList({ presages }: Props) {
  const allFavorable = presages.every((p) => p.kind === "favorable");
  const heading = allFavorable
    ? "Favorable presages detected"
    : "Presages detected";

  return (
    <div className="border border-dashed border-ink p-6">
      <div className="label-caps mb-5">{heading}</div>
      <ul className="space-y-3">
        {presages.map((p, i) => (
          <li key={i} className="flex items-start gap-3">
            <span
              className={`flex-none mt-0.5 text-lg font-medium ${
                p.kind === "favorable" ? "text-ink" : "text-ink"
              }`}
              aria-hidden
            >
              {p.kind === "favorable" ? "✓" : "✗"}
            </span>
            <div className="flex flex-col">
              <span className="font-medium">{p.title}</span>
              <span className="text-sm text-ink-soft">
                {p.detail}
                {p.malus_pct > 0 && (
                  <span className="text-ink-faint"> — −{p.malus_pct}%</span>
                )}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
