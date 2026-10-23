import { FileCode } from "lucide-react";
import { useState } from "react";

import { Button, Dialog } from "@/components/ui/primitives";
import { profileId, profileYaml } from "@/lib/profileYaml";
import type { Cell, Report } from "@/types/backtest";

/**
 * "Copy as live profile": the selected configuration as a
 * config/live_profiles/ file, for the operator to review and commit -- the
 * Live page can switch a deployment to it once it is in git.
 *
 * Shown in a text box rather than only put on the clipboard: the page is
 * served over plain HTTP on the LAN, where browsers withhold the clipboard
 * API, and the text is worth reading before it is committed anyway.
 */
export function ProfileProposal({
  report,
  ticker,
  cell,
}: {
  report: Report;
  ticker: string;
  cell: Cell;
}) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const text = profileYaml(report, ticker, cell);
  const id = profileId(report.model ?? "unknown", ticker);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied("Copied.");
    } catch {
      setCopied(
        "This page cannot reach the clipboard over plain HTTP: select the text and copy it.",
      );
    }
  };

  return (
    <>
      <Button variant="outline" onClick={() => setOpen(true)}>
        <FileCode className="size-3.5" />
        Copy as live profile
      </Button>
      {open ? (
        <Dialog title="Live profile" onClose={() => setOpen(false)} className="max-w-2xl">
          <div className="space-y-2 text-xs">
            <p className="text-muted-foreground">
              Save as <code>config/live_profiles/{id}.yaml</code> and commit it. Paper
              deployments trading {ticker} can then switch to it from the Live page.
            </p>
            <textarea
              readOnly
              className="h-72 w-full rounded border border-border bg-background p-2 font-mono text-[11px]"
              value={text}
              onFocus={(event) => event.currentTarget.select()}
            />
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => void copy()}>
                Copy
              </Button>
              {copied ? <span className="text-muted-foreground">{copied}</span> : null}
            </div>
          </div>
        </Dialog>
      ) : null}
    </>
  );
}
