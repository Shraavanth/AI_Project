import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ground: "#DCEAF5",          // MAIN APPLICATION BACKGROUND
        sidebar: "#C9DDED",         // SIDEBAR BACKGROUND
        surface: "#E5EFF7",         // CARDS AND CONTAINERS
        panel: "#D4E4F1",           // MAIN CONTENT PANELS
        raised: "#D4E4F1",          // MAIN CONTENT PANELS
        selected: "#B8D2E8",        // EXPANDED AND SELECTED SECTIONS
        header: "#C9DDED",          // TABLE HEADERS
        input: "#EDF4F9",           // INPUT BACKGROUNDS
        line: "#B2C9DC",            // DIVIDERS AND BORDERS
        primary: {
          DEFAULT: "#397FB8",       // PRIMARY ACCENT
          hover: "#2D6FAD",         // PRIMARY HOVER
          active: "#B8D2E8",        // ACTIVE NAVIGATION
        },
        ink: {
          DEFAULT: "#18344D",       // PRIMARY TEXT
          2: "#536F86",             // SECONDARY TEXT
          3: "#71879B",             // MUTED TEXT
        },
        ok: "#398C69",              // NORMAL AGENT / OK
        warn: "#D99A39",            // WARNING / EXTREME HEAT
        crit: "#E96C4B",            // FIRE / CRITICAL / RESPONDING
        dead: "#7F8992",            // FAILED
        move: "#397FB8",            // MOVING
        respond: "#E96C4B",         // RESPONDING
        recovering: "#866CC5",      // RECOVERING
        fire: "#E96C4B",
        pollution: "#36A6B5",
        heat: "#D99A39",
      },
      fontFamily: {
        sans: ["Barlow", "system-ui", "sans-serif"],
        cond: ["'Barlow Semi Condensed'", "Barlow", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
    },
  },
  plugins: [],
};
export default config;
