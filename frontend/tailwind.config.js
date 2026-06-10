/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Mrs Airma · The Cannes Oracle palette
        // Cream paper background, India-ink black, subtle warm accents.
        cream: "#f5f0e8",
        "cream-soft": "#ebe4d6",
        ink: "#0f0e0c",
        "ink-soft": "#403d36",
        "ink-faint": "#807a6e",
        rule: "#1a1815",
        // Tier accents (used sparingly, the design is mostly monochrome)
        gold: "#b8860b",
        silver: "#9a9a9a",
        bronze: "#a05a2c",
      },
      fontFamily: {
        // Serif italic is the brand voice (titles, verdicts, scores).
        // Stack falls back gracefully if Cormorant isn't loaded yet.
        serif: ['"Cormorant Garamond"', '"Garamond"', '"Times New Roman"', "serif"],
        // Sans for body copy, form inputs, fine print.
        sans: ['"Inter"', "-apple-system", "BlinkMacSystemFont", '"Segoe UI"', "Helvetica", "sans-serif"],
      },
      letterSpacing: {
        // Used on small caps labels (DETAILED READING OF THE STARS, etc.)
        wide: "0.12em",
      },
      animation: {
        "fade-in": "fadeIn 600ms ease-out both",
        "rays-pulse": "raysPulse 2800ms ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        raysPulse: {
          "0%, 100%": { opacity: "0.7" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
