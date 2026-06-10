import type { AxisDisplay } from "../types";

interface Props {
  axes: AxisDisplay[];
}

export function AxesTable({ axes }: Props) {
  return (
    <div className="border border-ink p-6">
      <div className="label-caps mb-5">Detailed reading of the stars</div>
      <ul className="space-y-4">
        {axes.map((a) => (
          <li key={a.key} className="flex flex-col gap-1.5">
            <div className="flex items-baseline justify-between gap-4 flex-wrap">
              <div className="flex items-baseline gap-3">
                <span className="font-medium">{a.label}</span>
                <span className="label-caps">weight {Math.round(a.weight * 100)} %</span>
              </div>
              <span className="editorial text-lg">
                {a.score}<span className="text-ink-faint">/100</span>
              </span>
            </div>
            <div className="h-px bg-ink/15 relative">
              <div
                className="absolute inset-y-0 left-0 bg-ink transition-all duration-700"
                style={{ width: `${a.score}%`, height: "2px", top: "-0.5px" }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
