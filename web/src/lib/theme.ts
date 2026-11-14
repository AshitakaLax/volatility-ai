/**
 * Light or dark: the system's choice unless the reader picked one here.
 * index.css carries both palettes; the `dark` class on <html> selects one.
 * The choice is kept in this browser only.
 */
export type ThemeChoice = "system" | "light" | "dark";

const KEY = "vai-theme";
const ORDER: ThemeChoice[] = ["system", "light", "dark"];

export function themeChoice(): ThemeChoice {
  try {
    const stored = window.localStorage.getItem(KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system"; // storage refused (private mode): follow the system
  }
}

export function isDark(choice: ThemeChoice, systemDark: boolean): boolean {
  return choice === "dark" || (choice === "system" && systemDark);
}

export function nextTheme(choice: ThemeChoice): ThemeChoice {
  return ORDER[(ORDER.indexOf(choice) + 1) % ORDER.length] ?? "system";
}

function systemDark(): boolean {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? true;
}

export function applyTheme(choice: ThemeChoice = themeChoice()): void {
  document.documentElement.classList.toggle("dark", isDark(choice, systemDark()));
}

export function setTheme(choice: ThemeChoice): void {
  try {
    if (choice === "system") window.localStorage.removeItem(KEY);
    else window.localStorage.setItem(KEY, choice);
  } catch {
    // Not kept; it still applies to this page.
  }
  applyTheme(choice);
}

/** Follow the system as it changes, while the reader has not chosen. */
export function watchSystemTheme(): () => void {
  const query = window.matchMedia?.("(prefers-color-scheme: dark)");
  if (!query) return () => {};
  const onChange = () => applyTheme();
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}
