// The signature visual motif of Mrs Airma: a thin-stroked circle surrounded
// by radiating capsule "rays", each capsule outlined in ink with a small filled
// dot near its inner tip. Inspired by sundials and old astrological diagrams.
//
// Layout: the wrapper is a centered block element with explicit max-width so
// it scales gracefully. Capsules are SVG <rect rx={h/2}> rotated around the
// circle's center — this gives a proper pill outline with a clean fill.
//
// Variants:
//   "open"   → empty central disc (form / loading)
//   "broken" → dashed cracks across the disc (error)
//   "result" → solid disc with hand-drawn X + tier label inside

import type { ReactNode } from "react";

interface SunRaysProps {
  variant?: "open" | "broken" | "result";
  /** Diameter of the inner circle in viewBox units (default 360). */
  size?: number;
  /** Number of capsules per side (default 8). Total rays = 2 × this. */
  raysPerSide?: number;
  className?: string;
  /** Content rendered inside the central disc (open/broken only). */
  children?: ReactNode;
  /** Tier name printed inside the disc for the "result" variant. */
  tierLabel?: string;
}

// Fixed viewBox keeps all proportions stable regardless of rendered size.
const VB = 600;
const CX = VB / 2;
const CY = VB / 2;

export function SunRays({
  variant = "open",
  size = 360,
  raysPerSide = 8,
  className = "",
  children,
  tierLabel,
}: SunRaysProps) {
  const r = size / 2;
  const gap = 16; // space between circle edge and inner end of capsule
  const capsuleLength = r * 0.45;
  const capsuleHeight = 14;
  const dotInset = 7; // distance from capsule inner edge to dot center

  // Angular spread per side, from -spreadDeg/2 to +spreadDeg/2 around horizontal.
  const spreadDeg = 150;
  const step = spreadDeg / (raysPerSide - 1);

  const capsules: JSX.Element[] = [];
  for (let i = 0; i < raysPerSide; i++) {
    const angleFromHoriz = -spreadDeg / 2 + step * i;
    // Right side: rotate by angle. Left side: rotate by 180 - angle.
    for (const side of ["right", "left"] as const) {
      const rotation = side === "right" ? angleFromHoriz : 180 - angleFromHoriz;
      capsules.push(
        <g
          key={`${side}-${i}`}
          transform={`rotate(${rotation} ${CX} ${CY})`}
        >
          <rect
            x={CX + r + gap}
            y={CY - capsuleHeight / 2}
            width={capsuleLength}
            height={capsuleHeight}
            rx={capsuleHeight / 2}
            ry={capsuleHeight / 2}
            fill="#f5f0e8"
            stroke="currentColor"
            strokeWidth={1.4}
          />
          <circle
            cx={CX + r + gap + dotInset}
            cy={CY}
            r={3.2}
            fill="currentColor"
          />
        </g>,
      );
    }
  }

  return (
    <div
      className={`relative mx-auto ${className}`}
      style={{ width: "100%", maxWidth: 520 }}
    >
      <svg
        viewBox={`0 0 ${VB} ${VB}`}
        width="100%"
        height="auto"
        className="block text-ink"
        aria-hidden="true"
      >
        {/* Capsules */}
        <g className={variant === "broken" ? "opacity-50" : ""}>{capsules}</g>

        {/* Central disc */}
        {variant !== "result" ? (
          <circle
            cx={CX}
            cy={CY}
            r={r}
            fill="#f5f0e8"
            stroke="currentColor"
            strokeWidth={1.5}
            strokeDasharray={variant === "broken" ? "10 8" : "0"}
          />
        ) : (
          <>
            <circle
              cx={CX}
              cy={CY}
              r={r}
              fill="#f5f0e8"
              stroke="currentColor"
              strokeWidth={1.5}
            />
            {/* Hand-drawn X — two slightly wavy strokes */}
            <path
              d={`M ${CX - r * 0.55} ${CY - r * 0.55} Q ${CX} ${CY - r * 0.05} ${CX + r * 0.55} ${CY + r * 0.55}`}
              stroke="currentColor"
              strokeWidth={2}
              fill="none"
              strokeLinecap="round"
            />
            <path
              d={`M ${CX + r * 0.55} ${CY - r * 0.55} Q ${CX} ${CY + r * 0.05} ${CX - r * 0.55} ${CY + r * 0.55}`}
              stroke="currentColor"
              strokeWidth={2}
              fill="none"
              strokeLinecap="round"
            />
            {/* "Mrs Airma" stamp at the top */}
            <text
              x={CX}
              y={CY - r * 0.65}
              textAnchor="middle"
              fontFamily="Cormorant Garamond, serif"
              fontStyle="italic"
              fontSize="18"
              fill="currentColor"
            >
              Mrs Airma
            </text>
            {/* Tier label at the bottom of the disc */}
            {tierLabel && (
              <text
                x={CX}
                y={CY + r * 0.7}
                textAnchor="middle"
                fontFamily="Cormorant Garamond, serif"
                fontWeight={500}
                fontSize="26"
                letterSpacing={3}
                fill="currentColor"
              >
                {tierLabel}
              </text>
            )}
          </>
        )}

        {/* Crack lines for the broken variant */}
        {variant === "broken" && (
          <g stroke="currentColor" strokeWidth={1} fill="none" strokeDasharray="6 6">
            <line x1={CX - r * 0.95} y1={CY - r * 0.55} x2={CX + r * 0.95} y2={CY + r * 0.55} />
            <line x1={CX + r * 0.45} y1={CY - r * 0.95} x2={CX - r * 0.45} y2={CY + r * 0.95} />
          </g>
        )}
      </svg>

      {/* Overlay content positioned over the central disc.
          Constrained to the inscribed square inside the circle. */}
      {variant !== "result" && children && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-auto">
          <div
            className="w-full"
            style={{
              // Inscribed square of the circle = diameter × cos(45°) ≈ 0.707 × diameter
              // Express as % of the SVG viewBox width (VB = 600).
              maxWidth: `${(size * 0.7 * 100) / VB}%`,
            }}
          >
            {children}
          </div>
        </div>
      )}
    </div>
  );
}
