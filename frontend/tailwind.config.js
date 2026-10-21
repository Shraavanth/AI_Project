/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        page: "#F5F4ED",
        background: "#F5F4ED",
        surface: "#FFFFFF",
        "surface-muted": "#FAF9F4",
        "forest-green": {
          DEFAULT: "#193B32",
          dark: "#122B24",
          light: "#234F43",
        },
        "secondary-green": {
          DEFAULT: "#456B57",
          hover: "#395847",
        },
        botanical: {
          DEFAULT: "#C7F36B",
          dark: "#A3D446",
        },
        "muted-sage": {
          DEFAULT: "#DCE5D8",
          dark: "#C6D3C1",
          light: "#F0F4ED",
        },
        "secondary-text": "#69786D",
        "primary-text": "#193B32",
        border: {
          DEFAULT: "#DFE4D9",
          dark: "#CAD3C2",
          light: "#EBEFE6",
        },
        "warning-amber": {
          DEFAULT: "#D9A441",
          light: "#FCF6E8",
        },
        "critical-incident": {
          DEFAULT: "#C95B48",
          light: "#FCEEEB",
        },
        status: {
          normal: "#193B32",
          active: "#456B57",
          botanical: "#C7F36B",
          warning: "#D9A441",
          critical: "#C95B48",
          offline: "#8A978E",
        },
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Lora", "Georgia", "serif"],
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
      boxShadow: {
        editorial: "0 1px 3px rgba(25, 59, 50, 0.05), 0 1px 2px rgba(25, 59, 50, 0.03)",
        elevated: "0 10px 25px -5px rgba(25, 59, 50, 0.08), 0 8px 10px -6px rgba(25, 59, 50, 0.04)",
      },
    },
  },
  plugins: [],
};
