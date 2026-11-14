import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "@/App";
import "@/index.css";
import { applyTheme } from "@/lib/theme";

// Before the first paint: index.html ships dark, the reader's or the
// system's choice may be light.
applyTheme();

const root = document.getElementById("root");
if (!root) throw new Error("index.html is missing #root");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
