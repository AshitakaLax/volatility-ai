import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // Ignore built output and generated files
  { ignores: ["dist", "node_modules"] },

  // Base JS recommended rules
  js.configs.recommended,

  // TypeScript-aware rules across all TS/TSX files
  ...tseslint.configs.recommended,

  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      // React Hooks: enforce rules of hooks and exhaustive deps
      ...reactHooks.configs.recommended.rules,

      // These newer react-hooks rules flag well-established patterns used
      // throughout this codebase:
      //   set-state-in-effect  — resetting state before an async fetch (e.g.
      //                          setCandles(null) before fetching) is standard
      //                          and intentional, not a cascade bug.
      //   refs                 — writing `handler.current = onMessage` on each
      //                          render is the canonical "stabilize a callback
      //                          without restarting an effect" idiom.
      //   immutability         — same ref-write pattern flagged by refs.
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/refs": "off",
      "react-hooks/immutability": "off",

      // Warn when a module only exports non-component things — helps
      // HMR stay reliable. Components-only files get the full check.
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],

      // TypeScript: keep the codebase honest about `any`
      "@typescript-eslint/no-explicit-any": "warn",

      // Allow `_`-prefixed variables to be unused (common in destructuring)
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
);
