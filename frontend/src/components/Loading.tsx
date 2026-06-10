// Loading screen — shown while the backend is running the 3-pass judge.
// Cycles through three labels to communicate progress to the user.

import { useEffect, useState } from "react";
import { SunRays } from "./SunRays";

const PROGRESS_STAGES = [
  "Analysing the board",
  "Reading the Lions",
  "Verdict of the stars",
];

export function Loading() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setStage((s) => Math.min(s + 1, PROGRESS_STAGES.length - 1));
    }, 15000); // ~45s total = 15s per stage
    return () => window.clearInterval(id);
  }, []);

  return (
    <div className="w-full max-w-3xl mx-auto px-4 animate-fade-in">
      <div className="animate-rays-pulse">
        <SunRays variant="open" size={420}>
          <div className="text-center px-6">
            <div className="editorial italic text-2xl md:text-3xl leading-relaxed">
              Mrs Airma consults
              <br />
              the stars…
            </div>
          </div>
        </SunRays>
      </div>

      <div className="flex items-center justify-center gap-6 mt-10 text-sm">
        {PROGRESS_STAGES.map((label, i) => (
          <div key={i} className="flex items-center gap-2">
            <span
              className={`block w-2.5 h-2.5 rounded-full border border-ink ${
                i <= stage ? "bg-ink" : "bg-transparent"
              }`}
            />
            <span className={i <= stage ? "text-ink" : "text-ink-faint"}>{label}</span>
          </div>
        ))}
      </div>

      <p className="text-center label-caps mt-6">
        Evaluation typically takes about 45 seconds.
      </p>
    </div>
  );
}
