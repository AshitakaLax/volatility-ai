import { History } from "lucide-react";
import { useState } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { commandLabel, rememberedOperator, statusTone } from "@/lib/control";
import type { CommandRow } from "@/types/control";

/**
 * Every command asked of this deployment, newest first, with what came of
 * it in the trader's own words -- applied, rejected and why, superseded,
 * expired, withdrawn. The control directory these come from is the audit
 * trail: who asked, from where, why, and when it took effect.
 *
 * A queued command can be withdrawn until its trader takes it; after that
 * the withdrawal is refused rather than pretending to undo something
 * already applied.
 */
interface Props {
  deploymentId: string;
  commands: CommandRow[];
  onChange: () => void;
}

const SHOWN = 20;

function when(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString() : "--";
}

export function CommandLog({ deploymentId, commands, onChange }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cancel = async (row: CommandRow) => {
    setBusy(row.id);
    setError(null);
    try {
      await api.cancelCommand(deploymentId, row.id, rememberedOperator() || "unknown");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(null);
      onChange();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="size-4" />
          Commands
        </CardTitle>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {commands.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nothing has been asked of it yet.</p>
        ) : (
          <table className="w-full min-w-[860px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Asked</th>
                <th className="pb-2 font-medium">Command</th>
                <th className="pb-2 font-medium">By</th>
                <th className="pb-2 font-medium">Reason</th>
                <th className="pb-2 font-medium">Outcome</th>
                <th className="pb-2 font-medium">Applied</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody>
              {commands.slice(0, SHOWN).map((row) => (
                <tr key={row.id} className="border-b border-border/50 align-top last:border-0">
                  <td className="py-2 text-xs text-muted-foreground">{when(row.created_at)}</td>
                  <td className="py-2">
                    {commandLabel(row)}
                    {row.timing !== "now" ? (
                      <span className="text-xs text-muted-foreground">
                        {" "}
                        ({row.timing.replace("_", " ")})
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2 text-xs" title={row.client ?? undefined}>
                    {row.operator}
                  </td>
                  <td className="max-w-[240px] py-2 text-xs text-muted-foreground">{row.reason}</td>
                  <td className="max-w-[300px] py-2">
                    <Badge tone={statusTone(row.status)}>{row.status}</Badge>
                    {row.detail ? <div className="mt-1 text-xs">{row.detail}</div> : null}
                  </td>
                  <td className="py-2 text-xs text-muted-foreground">{when(row.finished_at)}</td>
                  <td className="py-2 text-right">
                    {row.status === "queued" ? (
                      <Button
                        variant="ghost"
                        disabled={busy !== null}
                        onClick={() => void cancel(row)}
                      >
                        {busy === row.id ? "Withdrawing…" : "Withdraw"}
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {error ? <p className="mt-2 text-xs text-loss">{error}</p> : null}
      </CardContent>
    </Card>
  );
}
