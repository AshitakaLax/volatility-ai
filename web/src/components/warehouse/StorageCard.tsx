import { HardDrive } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { ago, bytes, whole } from "@/lib/warehouse";
import type { Storage } from "@/types/warehouse";

const LAKES: { key: "ohlcv" | "executions" | "external"; label: string }[] = [
  { key: "ohlcv", label: "Bars (ohlcv)" },
  { key: "executions", label: "Trade logs (executions)" },
  { key: "external", label: "Macro series (external)" },
];

/**
 * What the warehouse takes on disk and what its reference tables hold.
 *
 * Sizes come from the filesystem, so they show even while DuckDB cannot
 * open the files. The two .duckdb files are catalogs; the data is the
 * Parquet lakes beside them.
 */
export function StorageCard({ storage, now }: { storage: Storage; now: Date }) {
  const tables = storage.tables;
  const events = Object.entries(tables?.market_events ?? {});

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <HardDrive className="size-4" />
          Storage
        </CardTitle>
        <span className="truncate text-xs text-muted-foreground" title={storage.root ?? undefined}>
          {storage.duckdb ? `DuckDB ${storage.duckdb} · ` : ""}
          {storage.root ?? ""}
        </span>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="pb-2 font-medium">File or lake</th>
              <th className="pb-2 text-right font-medium">Files</th>
              <th className="pb-2 text-right font-medium">Size</th>
              <th className="pb-2 text-right font-medium">Changed</th>
            </tr>
          </thead>
          <tbody>
            {(storage.catalogs ?? []).map((catalog) => (
              <tr key={catalog.name} className="border-b border-border/50">
                <td className="py-1.5">{catalog.name}</td>
                <td className="py-1.5 text-right">1</td>
                <td className="py-1.5 text-right tabular-nums">{bytes(catalog.bytes)}</td>
                <td className="py-1.5 text-right text-xs text-muted-foreground">
                  {ago(catalog.modified, now)}
                </td>
              </tr>
            ))}
            {LAKES.map(({ key, label }) => {
              const lake = storage.lakes?.[key];
              return (
                <tr key={key} className="border-b border-border/50">
                  <td className="py-1.5">{label}</td>
                  <td className="py-1.5 text-right tabular-nums">{whole(lake?.files)}</td>
                  <td className="py-1.5 text-right tabular-nums">{bytes(lake?.bytes)}</td>
                  <td />
                </tr>
              );
            })}
            <tr>
              <td className="py-1.5">Spill space (tmp)</td>
              <td />
              <td className="py-1.5 text-right tabular-nums">{bytes(storage.tmp_bytes)}</td>
              <td />
            </tr>
          </tbody>
        </table>

        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <div className="text-xs font-medium text-muted-foreground">Reference tables</div>
            <div>{whole(tables?.assets)} assets described</div>
            <div>{whole(tables?.broker_environments)} cost models</div>
            {events.length ? (
              events.map(([kind, n]) => (
                <div key={kind}>
                  {whole(n)} {kind.replaceAll("_", " ")} events
                </div>
              ))
            ) : (
              <div className="text-muted-foreground">no market events</div>
            )}
          </div>
          <div>
            <div className="text-xs font-medium text-muted-foreground">Macro series</div>
            {tables?.external_series.length ? (
              tables.external_series.map((provider) => (
                <div key={provider.provider}>
                  {provider.provider}: {whole(provider.series)} series, newest{" "}
                  {provider.newest?.slice(0, 10) ?? "--"}
                </div>
              ))
            ) : (
              <div className="text-muted-foreground">none ingested</div>
            )}
          </div>
        </div>

        {storage.disk ? (
          <div className="text-xs text-muted-foreground">
            {bytes(storage.disk.free)} free of {bytes(storage.disk.total)} on the warehouse&apos;s
            disk.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
