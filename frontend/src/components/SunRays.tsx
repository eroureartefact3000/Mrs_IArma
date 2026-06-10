// The signature visual motif of Mrs Airma: a circle surrounded by radiating
// "capsule" rays, each with a small filled dot at the inner tip.
//
// Used as a frame on the form, loading, and error screens. The center can be
// left open (form input lives inside) or filled (loading text inside).
//
// Variants:
//   "open"      → circle outline only, capsules around (form, loading)
//   "broken"    → cracked/dashed lines through the circle (error)
//   "result"    → solid circle with hand-drawn X inside (result page)

import type { ReactNode } from "react";

interface SunRaysProps {
  variant?: "open" | "broken" | "result";
  size?: number; // px diameter of the inner circle
  rays?: number; // total number of capsules (split across left + right halves)
  className?: string;
  children?: ReactNode; // content drawn inside the central circle
  tierLabel?: string; // for "result" variant, the tier name to print under the X
}

export function SunRays({
  variant = "open",
  size = 360,
  rays = 12,
  className = "",
  children,
  tierLabel,
}: SunRaysProps) {
  const cx = 250;
  const cy = 250;
  const r = size / 2;

  // Build the capsule rays: half on each side, with vertical staggered offsets.
  // Each ray is a thin rounded rectangle with a small filled dot at the inner tip.
  const rayCount = rays;
  const half = rayCount / 2;
  // Stagger lengths slightly so it looks hand-drawn, not machine-perfect.
  const baseLength = r * 0.55;
  const lengthJitter = (i: number) => baseLength + ((i % 3) - 1) * 8;

  // Capsule angular spread on each side: from -45deg above horizontal
  // to +45deg below. Distributed evenly.
  const spreadDeg = 90;
  const angleStep = spreadDeg / (half - 1);

  function rayPath(side: "left" | "right", i: number): JSX.Element {
    const angleFromHoriz = -spreadDeg / 2 + angleStep * i;
    const angleDeg = side === "left" ? 180 - angleFromHoriz : angleFromHoriz;
    const rad = (angleDeg * Math.PI) / 180;
    const length = lengthJitter(i);
    const innerR = r + 10;
    const x1 = cx + innerR * Math.cos(rad);
    const y1 = cy + innerR * Math.sin(rad);
    const x2 = cx + (innerR + length) * Math.cos(rad);
    const y2 = cy + (innerR + length) * Math.sin(rad);
    const capsuleWidth = 16;
    return (
      <g key={`${side}-${i}`} className="ray">
        {/* The capsule body */}
        <line
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="currentColor"
          strokeWidth={capsuleWidth}
          strokeLinecap="round"
          fill="none"
          opacity={0.9}
        />
        {/* Inner stroke to give the capsule a hollow look */}
        <line
          x1={x1 + Math.cos(rad) * 4}
          y1={y1 + Math.sin(rad) * 4}
          x2={x2 - Math.cos(rad) * 4}
          y2={y2 - Math.sin(rad) * 4}
          stroke="currentColor"
          strokeOpacity={0}
          strokeWidth={capsuleWidth - 4}
          strokeLinecap="round"
          fill="currentColor"
          fillOpacity={0}
        />
        {/* Filled dot at the inner tip */}
        <circle cx={x1} cy={y1} r={4.5} fill="currentColor" />
      </g>
    );
  }

  // Use stroke-only for capsules: they look like outlined pills.
  // We render them as a rect-style capsule via two lines... actually simpler:
  // a stroked line acts as a capsule when strokeLinecap="round" and width > 1.
  // The "hollow" look is achieved by drawing a thinner background line on top.

  const rayElements: JSX.Element[] = [];
  for (let i = 0; i < half; i++) {
    rayElements.push(rayPath("left", i));
    rayElements.push(rayPath("right", i));
  }

  // Re-render capsules as outlined pills (stroke outer, fill cream inner)
  // by drawing a thinner cream line over each rendered black one.
  function rayHollow(side: "left" | "right", i: number): JSX.Element {
    const angleFromHoriz = -spreadDeg / 2 + angleStep * i;
    const angleDeg = side === "left" ? 180 - angleFromHoriz : angleFromHoriz;
    const rad = (angleDeg * Math.PI) / 180;
    const length = lengthJitter(i);
    const innerR = r + 10;
    const x1 = cx + innerR * Math.cos(rad);
    const y1 = cy + innerR * Math.sin(rad);
    const x2 = cx + (innerR + length) * Math.cos(rad);
    const y2 = cy + (innerR + length) * Math.sin(rad);
    return (
      <line
        key={`${side}-${i}-hollow`}
        x1={x1 + Math.cos(rad) * 2}
        y1={y1 + Math.sin(rad) * 2}
        x2={x2 - Math.cos(rad) * 2}
        y2={y2 - Math.sin(rad) * 2}
        stroke="#f5f0e8"
        strokeWidth={12}
        strokeLinecap="round"
      />
    );
  }
  const rayHollows: JSX.Element[] = [];
  for (let i = 0; i < half; i++) {
    rayHollows.push(rayHollow("left", i));
    rayHollows.push(rayHollow("right", i));
  }

  return (
    <div className={`relative inline-block ${className}`}>
      <svg
        viewBox="0 0 500 500"
        width="100%"
        height="auto"
        className="text-ink"
        aria-hidden="true"
      >
        {/* Rays first (behind the circle) */}
        <g className={variant === "broken" ? "opacity-50" : ""}>
          {rayElements}
          {rayHollows}
        </g>

        {/* Center circle */}
        {variant !== "result" ? (
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="#f5f0e8"
            stroke="currentColor"
            strokeWidth={1.5}
            strokeDasharray={variant === "broken" ? "8 6" : "0"}
          />
        ) : (
          <>
            <circle cx={cx} cy={cy} r={r} fill="#f5f0e8" stroke="currentColor" strokeWidth={1.5} />
            {/* Hand-drawn X — two slightly wavy strokes crossing */}
            <path
              d="M 150 150 Q 250 240 350 350"
              stroke="currentColor"
              strokeWidth={2}
              fill="none"
              strokeLinecap="round"
            />
            <path
              d="M 350 150 Q 250 240 150 350"
              stroke="currentColor"
              strokeWidth={2}
              fill="none"
              strokeLinecap="round"
            />
            {/* "Mrs Airma" stamp at the top */}
            <text
              x={cx}
              y={cy - r * 0.6}
              textAnchor="middle"
              className="editorial"
              fontSize="14"
              fontStyle="italic"
              fill="currentColor"
            >
              Mrs Airma
            </text>
            {/* Tier label at the bottom of the circle */}
            {tierLabel && (
              <text
                x={cx}
                y={cy + r * 0.65}
                textAnchor="middle"
                fontSize="22"
                fontFamily="Cormorant Garamond, serif"
                fontWeight="500"
                letterSpacing="2"
                fill="currentColor"
              >
                {tierLabel}
              </text>
            )}
          </>
        )}

        {/* Crack lines through the circle for the broken variant */}
        {variant === "broken" && (
          <g stroke="currentColor" strokeWidth={1} fill="none" strokeDasharray="4 4">
            <line x1={cx - r} y1={cy - r * 0.6} x2={cx + r} y2={cy + r * 0.6} />
            <line x1={cx + r * 0.5} y1={cy - r} x2={cx - r * 0.5} y2={cy + r} />
          </g>
        )}
      </svg>

      {/* Overlay content positioned over the central circle */}
      {variant !== "result" && children && (
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-auto"
          style={{
            // Constrain the content to the inner circle area
            padding: `${(500 - size) / 5}% ${(500 - size) / 5}%`,
          }}
        >
          <div className="w-full max-w-md">{children}</div>
        </div>
      )}
    </div>
  );
}
