import { ScrollText } from "lucide-react";
import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Activity } from "@/types/telemetry";

/**
 * The ledger's own revision log, newest first: every mutation the trader
 * made to it -- a lot opened, one closed, an order's state, a halt. Lower
 * level than the trades above, and the record reconciliation reads; shown
 * collapsed, for the question the trades cannot answer.
 */
const POLL_MS = 30_000;

export function ActivityCard({ deploymentId }: { deploymentId: string }) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<Activity[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const load = () =>
      api
        .activity(deploymentId, 100)
        .then((next) => {
          if (!cancelled) {
            setRows(next);
            setError(null);
          }
        })
        .catch((cause: unknown) => {
          if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
        });
    void load();
    const timer = window.setInterval(() => void load(), POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [deploymentId, open]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ScrollText className="size-4" />
          <button type="button" className="text-left" onClick={() => setOpen(!open)}>
            Ledger activity {open ? "▾" : "▸"}
          </button>
        </CardTitle>
      </CardHeader>
      {open ? (
        <CardContent className="overflow-x-auto">
          {error ? (
            <p className="text-sm text-loss">{error}</p>
          ) : rows === null ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">The ledger has recorded nothing yet.</p>
          ) : (
            <table className="w-full min-w-[640px] text-xs">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 font-medium">#</th>
                  <th className="pb-2 font-medium">Operation</th>
                  <th className="pb-2 font-medium">Order</th>
                  <th className="pb-2 font-medium">Detail</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.revision} className="border-b border-border/50 last:border-0">
                    <td className="tnum py-1 text-muted-foreground">{row.revision}</td>
                    <td className="py-1">{row.operation}</td>
                    <td className="max-w-[220px] truncate py-1 font-mono" title={row.order_id ?? ""}>
                      {row.order_id ?? ""}
                    </td>
                    <td className="py-1 text-muted-foreground">{row.detail ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      ) : null}
    </Card>
  );
}
