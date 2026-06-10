import { SunRays } from "./SunRays";

interface Props {
  message: string;
  onRetry: () => void;
}

const CAUSES = [
  "Unsupported format. JPG, PNG, WEBP, AVIF or GIF only.",
  "File too large. 25 MB maximum.",
  "Out-of-range dimensions. Up to about 7000 × 5000 px recommended.",
  "Corrupt or unreadable file.",
  "Backend offline or rate-limited.",
];

export function ErrorPage({ message, onRetry }: Props) {
  return (
    <div className="w-full max-w-2xl mx-auto px-4 animate-fade-in">
      <SunRays variant="broken" size={360}>
        <div className="text-center">
          <div className="editorial italic text-2xl md:text-3xl leading-relaxed">
            The stars
            <br />
            are clouded…
          </div>
        </div>
      </SunRays>

      <div className="border border-dashed border-ink p-6 mt-8">
        <div className="label-caps mb-4">Possible causes</div>
        <ul className="space-y-2 text-sm text-ink-soft">
          {CAUSES.map((c, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-ink-faint">·</span>
              <span>{c}</span>
            </li>
          ))}
        </ul>
        {message && (
          <div className="mt-5 pt-4 border-t border-ink/15 text-sm">
            <span className="label-caps">Server response: </span>
            <span className="text-ink">{message}</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-center gap-4 mt-8">
        <button className="cta-primary" onClick={onRetry}>
          Try again
        </button>
      </div>
    </div>
  );
}
