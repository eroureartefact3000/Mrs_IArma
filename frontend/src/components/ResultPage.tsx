import type { EvaluateResponse } from "../types";
import { SunRays } from "./SunRays";
import { AxesTable } from "./AxesTable";
import { PresagesList } from "./PresagesList";

interface Props {
  result: EvaluateResponse;
  onRetry: () => void;
}

export function ResultPage({ result, onRetry }: Props) {
  const tp = result.tier_prediction;

  return (
    <div className="w-full max-w-2xl mx-auto px-4 pb-16 animate-fade-in">
      {/* Hero: stamped circle + score + verdict */}
      <div className="flex flex-col items-center text-center gap-6">
        <SunRays variant="result" size={300} tierLabel={tp.tier_label} />

        <div className="editorial text-5xl md:text-6xl mt-2">
          {tp.score_percent}
          <span className="text-xl align-top ml-0.5">%</span>
        </div>

        <blockquote className="editorial italic text-xl text-ink-soft max-w-md">
          «&nbsp;{tp.mystic_verdict}&nbsp;»
        </blockquote>

        <ConfidenceBadge confidence={tp.confidence} />
      </div>

      {/* Detail panels */}
      <div className="mt-12 space-y-6">
        <AxesTable axes={tp.axes} />
        <PresagesList presages={tp.presages} />

        {/* Post-mortem synthesis */}
        <div className="pt-2">
          <div className="label-caps mb-3">Synthesis</div>
          <p className="text-base text-ink-soft leading-relaxed">{tp.synthesis}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-center gap-4 mt-12">
        <button
          className="cta-primary"
          onClick={() => {
            navigator.clipboard
              ?.writeText(window.location.href)
              .catch(() => null);
          }}
        >
          Share
        </button>
        <button className="cta-secondary" onClick={onRetry}>
          Consult again
        </button>
      </div>

      {/* Debug strip — useful for handoff, can be removed in prod */}
      <div className="mt-10 text-center label-caps">
        Evaluation #{result.evaluation_id.slice(0, 8)} · {result.elapsed_seconds}s
      </div>
    </div>
  );
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  return (
    <div className="inline-flex items-center gap-2 border border-ink/40 px-3 py-1 text-xs">
      <span className="label-caps">Confidence</span>
      <span className="text-ink font-medium uppercase tracking-widest">{confidence}</span>
    </div>
  );
}
