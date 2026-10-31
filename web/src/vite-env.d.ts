/// <reference types="vite/client" />

// Required, not boilerplate: tsconfig.app.json sets
// noUncheckedSideEffectImports, so `import "@/index.css"` is an error
// without the ambient module declarations Vite ships here.

/** The web build's release version, injected by vite.config.ts from package.json. */
declare const __WEB_VERSION__: string;
