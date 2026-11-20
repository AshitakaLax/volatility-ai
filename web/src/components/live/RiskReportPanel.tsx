import { FileJson } from "lucide-react";
import { useState, type DragEvent } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Checkbox, Input } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { rememberedOperator, rememberOperator } from "@/lib/control";
import {
  checkedByDefault,
  levers,
  needsTyped,
  parsePasted,
  reportDeployments,
  sessionDay,
  tierLabel,
  tierTone,
  would,
} from "@/lib/riskReport";
import { cn } from "@/lib/utils";
import type { DeploymentSummary } from "@/types/control";
import type { RiskReportPreview } from "@/types/riskReport";

/**
 * Tonight's risk report (docs/daily_risk_report_plan.md): paste or drop the
 * JSON the evening prompt returned, CHECK it, then APPLY it to the
 * deployments ticked.
 *
 * Check asks the server what the report would do to each deployment whose
 * config takes reports -- its audit, the session it is for, and the overlay
 * that deployment's own mapping makes of it. It writes nothing. Apply queues
 * apply_risk_report for each one ticked; its trader parses and maps the
 * report again, archives it, and -- in advisory mode, every deployment's
 * until its gate passes -- shows it as a suggestion and trades as configured.
 *
 * A report can only take risk away from what a deployment's config trades.
 * Real money is listed beside paper and ticked like it, and asks for its id
 * typed back.
 */

interface Props {
  deployments: DeploymentSummary[];
  onSent: () => void;
}

interface Sent {
  id: string;
  ok: boolean;
  text: string;
}

function newKey(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function RiskReportPanel({ deployments, onSent }: Props) {
  const listed = reportDeployments(deployments);
  const [text, setText] = useState("");
  const [previews, setPreviews] = useState<RiskReportPreview[] | null>(null);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [typed, setTyped] = useState<Record<string, string>>({});
  const [reason, setReason] = useState("Tonight's risk report");
  const [operator, setOperator] = useState(rememberedOperator);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState<Sent[]>([]);
  const [key, setKey] = useState(newKey);

  if (!listed.length) return null;
  const pasted = parsePasted(text);
  const first = previews?.[0];

  const check = async () => {
    if (!pasted.report) return;
    setBusy(true);
    setError(null);
    setSent([]);
    try {
      const found = await Promise.all(listed.map((d) => api.previewRiskReport(d.id, pasted.report)));
      setPreviews(found);
      setChecked(Object.fromEntries(found.map((p) => [p.deployment, checkedByDefault(p)])));
      setTyped({});
      setKey(newKey());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const chosen = (previews ?? []).filter((p) => checked[p.deployment]);
  const ready =
    chosen.length > 0 &&
    reason.trim().length >= 3 &&
    operator.trim().length > 0 &&
    chosen.every((p) => !needsTyped(p) || (typed[p.deployment] ?? "").trim() === p.deployment);

  const apply = async () => {
    if (!pasted.report || !ready) return;
    setBusy(true);
    setError(null);
    const results: Sent[] = [];
    for (const preview of chosen) {
      try {
        const response = await api.sendCommand(preview.deployment, {
          type: "apply_risk_report",
          args: { report: pasted.report },
          reason: reason.trim(),
          operator: operator.trim(),
          idempotency_key: `${key}-${preview.deployment}`,
          ...(needsTyped(preview) ? { confirm: (typed[preview.deployment] ?? "").trim() } : {}),
        });
        results.push({
          id: preview.deployment,
          ok: true,
          text: response.warning ?? "queued: its trader archives it within seconds -- see its command log",
        });
      } catch (cause) {
        results.push({
          id: preview.deployment,
          ok: false,
          text: cause instanceof Error ? cause.message : String(cause),
        });
      }
    }
    rememberOperator(operator.trim());
    setSent(results);
    setBusy(false);
    onSent();
  };

  const onDrop = (event: DragEvent<HTMLTextAreaElement>) => {
    const file = event.dataTransfer.files[0];
    if (!file) return;
    event.preventDefault();
    void file.text().then((body) => {
      setText(body);
      setPreviews(null);
    });
  };

  return (
    <details className="group" data-testid="risk-report-panel" open={text.length > 0 || undefined}>
      <summary className="cursor-pointer list-none rounded-lg border border-border bg-card px-5 py-3 text-sm font-semibold select-none">
        <FileJson className="mr-2 inline size-4" />
        Tonight&apos;s risk report
        <span className="ml-2 font-normal text-muted-foreground group-open:hidden">
          paste the evening report to set tomorrow&apos;s risk for {listed.length} deployment
          {listed.length === 1 ? "" : "s"}
        </span>
      </summary>
      <Card className="mt-3">
        <CardHeader>
          <CardTitle className="text-base">Check, then apply</CardTitle>
          <p className="text-xs text-muted-foreground">
            A report can only take risk away from what each deployment&apos;s config trades -- fewer
            or smaller buys, a wider grid step, a lower exposure ceiling. It never sells, never changes
            the algorithm, and in advisory mode changes nothing at all: the suggestion is shown and
            logged, and you act on it with Pause buys.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            className="min-h-32 w-full rounded-md border border-input bg-background p-2 font-mono text-xs"
            placeholder='Paste or drop the report JSON here ({"schema_version": "1.1.0", "symbol": "TQQQ", ...})'
            value={text}
            onChange={(event) => {
              setText(event.currentTarget.value);
              setPreviews(null);
            }}
            onDragOver={(event) => event.preventDefault()}
            onDrop={onDrop}
            aria-label="Risk report JSON"
          />
          {pasted.error ? <p className="text-xs text-loss">{pasted.error}</p> : null}
          <Button disabled={busy || !pasted.report} onClick={() => void check()}>
            {busy && !previews ? "Checking…" : "Check"}
          </Button>

          {first ? <AuditSummary preview={first} /> : null}

          {previews && first?.audit.ok ? (
            <div className="space-y-2">
              <p className="text-sm font-medium">Apply to</p>
              {previews.map((preview) => (
                <PreviewRow
                  key={preview.deployment}
                  preview={preview}
                  checked={Boolean(checked[preview.deployment])}
                  onCheck={(on) => setChecked({ ...checked, [preview.deployment]: on })}
                  typed={typed[preview.deployment] ?? ""}
                  onType={(value) => setTyped({ ...typed, [preview.deployment]: value })}
                />
              ))}
              <div className="grid gap-2 sm:grid-cols-[1fr_12rem]">
                <Input
                  placeholder="Why -- recorded with the report"
                  value={reason}
                  onChange={(event) => setReason(event.currentTarget.value)}
                />
                <Input
                  placeholder="Your name"
                  value={operator}
                  onChange={(event) => setOperator(event.currentTarget.value)}
                />
              </div>
              <Button disabled={busy || !ready} onClick={() => void apply()}>
                {busy ? "Sending…" : `Apply to ${chosen.length} deployment${chosen.length === 1 ? "" : "s"}`}
              </Button>
            </div>
          ) : null}
          {sent.length ? (
            <ul className="space-y-1 text-xs">
              {sent.map((row) => (
                <li key={row.id} className={row.ok ? "text-muted-foreground" : "text-loss"}>
                  <span className="font-medium">{row.id}</span>: {row.text}
                </li>
              ))}
            </ul>
          ) : null}
          {error ? <p className="text-xs text-loss">{error}</p> : null}
        </CardContent>
      </Card>
    </details>
  );
}

function AuditSummary({ preview }: { preview: RiskReportPreview }) {
  const audit = preview.audit;
  return (
    <div className="space-y-1 rounded-md border border-border bg-secondary/30 p-3 text-sm">
      {audit.ok ? (
        <p>
          For <span className="font-medium">{sessionDay(preview.session)}</span>
          {preview.mapped?.provisional ? (
            <span className="text-muted-foreground"> · tier thresholds provisional until calibrated</span>
          ) : null}
        </p>
      ) : (
        <p className="font-medium text-loss">The report does not pass the audit:</p>
      )}
      {audit.errors.map((f) => (
        <p key={`${f.where}-${f.message}`} className="text-xs text-loss">
          <code>{f.where}</code>: {f.message}
        </p>
      ))}
      {audit.warnings.length ? (
        <details>
          <summary className="cursor-pointer text-xs text-muted-foreground">
            {audit.warnings.length} warning{audit.warnings.length === 1 ? "" : "s"}
          </summary>
          {audit.warnings.map((f) => (
            <p key={`${f.where}-${f.message}`} className="text-xs text-muted-foreground">
              <code>{f.where}</code>: {f.message}
            </p>
          ))}
        </details>
      ) : null}
    </div>
  );
}

function PreviewRow({
  preview,
  checked,
  onCheck,
  typed,
  onType,
}: {
  preview: RiskReportPreview;
  checked: boolean;
  onCheck: (on: boolean) => void;
  typed: string;
  onType: (value: string) => void;
}) {
  const said = would(preview);
  const mapped = preview.mapped;
  const usable = preview.takes_reports && preview.would !== "refused" && preview.would !== "unchanged";
  return (
    <div className={cn("space-y-1 rounded-md border p-3", checked ? "border-border" : "border-border/50 opacity-80")}>
      <label className="flex flex-wrap items-center gap-2 text-sm">
        <Checkbox
          checked={checked}
          disabled={!usable}
          onChange={(event) => onCheck(event.currentTarget.checked)}
        />
        <span className="font-medium">{preview.label}</span>
        <span className="text-muted-foreground">{preview.symbol}</span>
        <Badge tone={preview.paper ? "profit" : "loss"}>{preview.paper ? "paper" : "real money"}</Badge>
        {preview.mode ? <Badge>{preview.mode}</Badge> : null}
        {mapped ? <Badge tone={tierTone(mapped.tier, mapped.abstained)}>{tierLabel(mapped.tier, mapped.abstained)}</Badge> : null}
        <span className={cn("text-xs", said.tone === "loss" ? "text-loss" : "text-muted-foreground")}>{said.label}</span>
      </label>
      {preview.summary ? <p className="text-sm">{preview.summary}</p> : null}
      {preview.overlay && levers(preview.overlay).length ? (
        <div className="flex flex-wrap gap-1">
          {levers(preview.overlay).map((lever) => (
            <Badge key={lever} tone="stuck">
              {lever}
            </Badge>
          ))}
        </div>
      ) : null}
      {mapped?.reasons.length ? (
        <ul className="list-disc pl-5 text-xs text-muted-foreground">
          {mapped.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : null}
      {preview.notes?.length ? <p className="text-xs text-muted-foreground">{preview.notes.join(" · ")}</p> : null}
      {preview.detail && preview.would !== "apply" ? <p className="text-xs text-muted-foreground">{preview.detail}</p> : null}
      {checked && needsTyped(preview) ? (
        <div className="space-y-1">
          <p className="text-xs text-loss">
            Type <code className="font-mono">{preview.deployment}</code> to confirm: {preview.typed}.
          </p>
          <Input placeholder={preview.deployment} value={typed} onChange={(event) => onType(event.currentTarget.value)} />
        </div>
      ) : null}
    </div>
  );
}
