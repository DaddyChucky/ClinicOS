import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#11223B",
        slate: "#2F4059",
        muted: "#64748B",
        surface: "#FFFFFF",
        cloud: "#EFF3F8",
        accent: "#0F766E",
        "accent-strong": "#0B5E59",
        info: "#1D4ED8",
        warn: "#B45309",
        danger: "#B42318",
        success: "#0F766E"
      },
      boxShadow: {
        panel: "0 10px 25px rgba(15, 23, 42, 0.08)",
        soft: "0 8px 18px rgba(15, 23, 42, 0.05)",
        elevated: "0 16px 40px rgba(15, 23, 42, 0.14)"
      }
    }
  },
  plugins: []
};

export default config;
