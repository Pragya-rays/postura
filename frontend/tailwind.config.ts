import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: { "2xl": "1200px" },
    },
    extend: {
      colors: {
        // Postura brand palette — premium black surfaces, an off-white
        // ink, and a bright cyan accent. "cream" is a legacy token name
        // kept for compatibility with existing classNames but now points
        // at the same near-black values as "forest".
        cream: {
          DEFAULT: "#0c0c0c",
          soft: "#141414",
          card: "#1a1a1a",
        },
        ink: {
          DEFAULT: "#dfdfdf",
          secondary: "#a8a8a8",
          muted: "#646363",
        },
        line: {
          DEFAULT: "rgba(255,255,255,0.10)",
          soft: "rgba(255,255,255,0.06)",
        },
        // "lime" is a legacy token name — it now holds the neutral grey
        // accent (previously cyan) used for CTA buttons, checkmarks, and
        // icon badges.
        lime: {
          DEFAULT: "#a3a3a3",
          dark: "#737373",
          soft: "rgba(163,163,163,0.14)",
        },
        glow: {
          orange: "#f2b54a",
          purple: "#3c61a7",
          cyan: "#28dfda",
        },
        forest: {
          DEFAULT: "#0c0c0c",
          soft: "#141414",
          card: "#1a1a1a",
          line: "rgba(255,255,255,0.10)",
          ink: "#dfdfdf",
          secondary: "#a8a8a8",
          muted: "#646363",
        },
        status: {
          good: "#4fd9b4",
          warning: "#f2b54a",
          serious: "#e08a3c",
          critical: "#dd5559",
        },
      },
      fontFamily: {
        serif: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-body)", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      backgroundImage: {
        "grid-dots": "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
        "grid-dots-dark": "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.35), 0 1px 0 rgba(255,255,255,0.03)",
        pop: "0 12px 32px -12px rgba(0,0,0,0.45)",
        "pop-dark": "0 24px 60px -20px rgba(0,0,0,0.7), 0 0 40px -12px rgba(255,255,255,0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
