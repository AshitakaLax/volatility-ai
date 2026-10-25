import { ChevronRight, CircleCheck, CircleDashed, CircleX, TriangleAlert } from "lucide-react";

import type { Step, StepState } from "@/lib/fidelity";
import { cn } from "@/lib/utils";

/**
 * The links from this server to the Fidelity account, left to right:
 * Bridge -> Extension -> Fidelity tab -> Allow trading -> Trader -> Account
 * check. Each says how it is and why; the first broken one is outlined and
 * its fix written out underneath -- the one thing to do.
 */
const STYLE: Record<StepState, string> = {
  ok: "border-profit/40 bg-profit/10",
  warn: "border-stuck/40 bg-stuck/10",
  fail: "border-loss/50 bg-loss/10",
  unknown: "border-border bg-secondary/30",
};

const TEXT: Record<StepState, string> = {
  ok: "text-profit",
  warn: "text-stuck",
  fail: "text-loss",
  unknown: "text-muted-foreground",
};

const WORD: Record<StepState, string> = {
  ok: "working",
  warn: "working, with a warning",
  fail: "broken",
  unknown: "not reported",
};

function Icon({ state }: { state: StepState }) {
  const className = cn("size-3.5 shrink-0", TEXT[state]);
  if (state === "ok") return <CircleCheck className={className} aria-hidden />;
  if (state === "warn") return <TriangleAlert className={className} aria-hidden />;
  if (state === "fail") return <CircleX className={className} aria-hidden />;
  return <CircleDashed className={className} aria-hidden />;
}

export function ConnectionChain({ steps }: { steps: Step[] }) {
  const broken = steps.find((step) => step.state === "fail");
  return (
    <div className="space-y-2">
      <ol className="flex flex-wrap items-stretch gap-1.5" aria-label="The connection, link by link">
        {steps.map((step, index) => (
          <li key={step.id} className="flex items-center gap-1.5">
            {index > 0 ? (
              <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
            ) : null}
            <div
              className={cn(
                "rounded-md border px-2 py-1",
                STYLE[step.state],
                step === broken && "ring-1 ring-loss/60",
              )}
              title={step.fix ? `${step.detail} -- ${step.fix}` : step.detail}
            >
              <div className={cn("flex items-center gap-1 text-xs font-medium", TEXT[step.state])}>
                <Icon state={step.state} />
                {step.label}
                <span className="sr-only">: {WORD[step.state]}</span>
              </div>
              <div className="max-w-[17rem] text-[11px] leading-snug text-muted-foreground">
                {step.detail}
              </div>
            </div>
          </li>
        ))}
      </ol>
      {broken?.fix ? (
        <p className="text-xs">
          <span className="font-medium text-loss">To fix the {broken.label.toLowerCase()}:</span>{" "}
          {broken.fix}.
        </p>
      ) : null}
    </div>
  );
}
