import type { Config } from "tailwindcss";

// Maps UXD (docs/design/UXD.md) §2.1/§2.2 CSS custom properties into Tailwind
// utilities, shadcn/ui-style (`hsl(var(--x))`) — see app/globals.css for the
// token values themselves.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        border: "hsl(var(--border))",
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        destructive: "hsl(var(--destructive))",
        ring: "hsl(var(--ring))",
        status: {
          critical: "hsl(var(--status-critical))",
          high: "hsl(var(--status-high))",
          medium: "hsl(var(--status-medium))",
          low: "hsl(var(--status-low))",
          info: "hsl(var(--status-info))",
          conforming: "hsl(var(--status-conforming))",
          "non-conforming": "hsl(var(--status-non-conforming))",
        },
      },
      borderRadius: {
        DEFAULT: "var(--radius)",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)"],
        mono: ["var(--font-geist-mono)"],
      },
    },
  },
  plugins: [],
};

export default config;
