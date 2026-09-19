import { useState } from "react";

import { Button, Checkbox, Dialog, Field, Input } from "@/components/ui/primitives";
import { ApiError, api } from "@/lib/api";
import type { Shard } from "@/types/backtest";

/**
 * Set (or clear) one shard's daily lockout window: server-local
 * wall-clock hours during which it takes no new sweep and hands back
 * whatever it is running, the same as clicking Pause -- just on a
 * schedule instead of by hand. Opened by clicking the shard itself in
 * ShardPanel.
 *
 * Two default times (07:00/19:00) rather than empty fields: a native
 * `<input type="time">` starting empty makes turning the checkbox on
 * immediately invalid (the server refuses `enabled` without both
 * times), which is a confusing first thing to hit in a dialog someone
 * just opened. Existing values always win over these once the shard
 * already has a schedule.
 */
const DEFAULT_START = "07:00";
const DEFAULT_END = "19:00";

export function ShardScheduleDialog({
  shard,
  onClose,
  onSaved,
}: {
  shard: Shard;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [enabled, setEnabled] = useState(shard.schedule?.enabled ?? false);
  const [start, setStart] = useState(shard.schedule?.start ?? DEFAULT_START);
  const [end, setEnd] = useState(shard.schedule?.end ?? DEFAULT_END);
  const [busy, setBusy] = useState<"save" | "clear" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    setBusy("save");
    setError(null);
    try {
      await api.setShardSchedule(shard.name, { enabled, start, end });
      onSaved();
      onClose();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(null);
    }
  };

  const clear = async () => {
    setBusy("clear");
    setError(null);
    try {
      await api.setShardSchedule(shard.name, { enabled: false, start: null, end: null });
      onSaved();
      onClose();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(null);
    }
  };

  return (
    <Dialog title={`Lockout window -- ${shard.name}`} onClose={onClose}>
      <div className="flex flex-col gap-4">
        <p className="text-xs text-muted-foreground">
          Outside this window {shard.name} works the queue as usual. Inside it, it takes no new
          sweep and hands back one already running after its in-flight configurations -- the same
          as pausing it by hand, just on a schedule.
        </p>

        <label className="flex items-center gap-2 text-sm">
          <Checkbox checked={enabled} onChange={(event) => setEnabled(event.target.checked)} />
          Enable this window
        </label>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Start">
            <Input
              type="time"
              value={start}
              onChange={(event) => setStart(event.target.value)}
              disabled={busy !== null}
            />
          </Field>
          <Field label="End">
            <Input
              type="time"
              value={end}
              onChange={(event) => setEnd(event.target.value)}
              disabled={busy !== null}
            />
          </Field>
        </div>
        <p className="text-[11px] text-muted-foreground">
          An end time before the start means the window wraps past midnight (e.g. 22:00 to 06:00
          locks out overnight).
        </p>

        {error ? (
          <p className="rounded-md bg-loss/10 px-2 py-1 text-xs text-loss" role="alert">
            {error}
          </p>
        ) : null}

        <div className="flex items-center justify-between gap-2 pt-1">
          <Button
            type="button"
            variant="ghost"
            className="text-loss hover:text-loss"
            disabled={busy !== null || !shard.schedule}
            onClick={() => void clear()}
          >
            {busy === "clear" ? "Clearing..." : "Clear window"}
          </Button>
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" disabled={busy !== null} onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="button"
              disabled={busy !== null || (enabled && (!start || !end))}
              onClick={() => void save()}
            >
              {busy === "save" ? "Saving..." : "Save"}
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
