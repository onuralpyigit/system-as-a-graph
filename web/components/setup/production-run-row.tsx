"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ProductionJobResponse } from "@/lib/api-types";
import { useRunErrors } from "@/lib/production";

interface ProductionRunRowProps {
  job: ProductionJobResponse;
  isSelected: boolean;
  onSelect: (runId: string) => void;
}

function duration(startedAt: string, finishedAt: string | null): string {
  if (!finishedAt) return "—";
  const seconds = Math.round(
    (new Date(finishedAt).getTime() - new Date(startedAt).getTime()) / 1000,
  );
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}

/** One production run, expandable to the errors MSD recorded for it (SRS VAE-01.8). */
export function ProductionRunRow({ job, isSelected, onSelect }: ProductionRunRowProps) {
  const [expanded, setExpanded] = useState(false);
  const isRunning = job.status === "in_progress";
  // error_count is only set once a job resolves (succeed()/fail()), so it's
  // always 0 while running — poll the run's live error list instead, so a
  // failure that already happened isn't invisible until the run finishes.
  const { errors } = useRunErrors(job.run_id, expanded || isRunning, isRunning);
  const errorCount = isRunning ? errors.length : job.error_count;
  const hasErrors = errorCount > 0;

  return (
    <>
      <TableRow>
        <TableCell>
          <div className="flex items-center gap-1.5">
            {hasErrors ? (
              <button
                type="button"
                onClick={() => setExpanded((value) => !value)}
                className="text-muted-foreground hover:text-foreground"
                aria-label={expanded ? "Hide errors" : "Show errors"}
              >
                {expanded ? (
                  <ChevronDown className="h-3.5 w-3.5" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5" />
                )}
              </button>
            ) : null}
            <Badge
              variant={
                job.status === "succeeded"
                  ? "conforming"
                  : job.status === "failed"
                    ? "critical"
                    : "info"
              }
            >
              {job.status === "in_progress" ? "running" : job.status}
            </Badge>
            {hasErrors ? (
              <span className="text-xs text-muted-foreground">
                ({errorCount} error{errorCount === 1 ? "" : "s"})
              </span>
            ) : null}
            {/* Only shown when there's no per-error detail to expand into (e.g.
                an unhandled exception before any run/errors existed) —
                otherwise the expandable list above is the one place errors
                are presented. */}
            {job.status === "failed" && !hasErrors && job.failure_reason ? (
              <span className="text-xs text-muted-foreground">{job.failure_reason}</span>
            ) : null}
          </div>
        </TableCell>
        <TableCell className="font-mono text-xs">{job.file_path || "—"}</TableCell>
        <TableCell className="text-muted-foreground">
          {new Date(job.started_at).toLocaleString()}
        </TableCell>
        <TableCell className="tabular-nums text-muted-foreground">
          {duration(job.started_at, job.finished_at)}
        </TableCell>
        <TableCell className="text-muted-foreground">
          {job.finished_at ? new Date(job.finished_at).toLocaleString() : "—"}
        </TableCell>
        <TableCell className="tabular-nums">
          {job.status === "in_progress" ? "—" : job.entity_count}
        </TableCell>
        <TableCell className="tabular-nums">
          {job.status === "in_progress" ? "—" : job.relation_count}
        </TableCell>
        <TableCell>
          <div className="flex h-8 items-center">
            {job.status === "succeeded" ? (
              isSelected ? (
                <Badge variant="conforming">selected</Badge>
              ) : (
                <Button size="sm" variant="ghost" onClick={() => onSelect(job.run_id)}>
                  Select
                </Button>
              )
            ) : job.status === "failed" ? (
              <Button size="sm" variant="ghost" disabled>
                Select
              </Button>
            ) : null}
          </div>
        </TableCell>
      </TableRow>
      {expanded && hasErrors ? (
        <TableRow>
          <TableCell colSpan={8}>
            <div className="flex max-h-56 flex-col gap-1.5 overflow-y-auto py-1">
              {errors.map((error, index) => (
                <div key={index} className="text-xs text-status-critical">
                  <span className="font-medium">{error.status}</span> — {error.reason} (
                  {error.source_type}/{error.source_name},{" "}
                  {new Date(error.occurred_at).toLocaleString()})
                </div>
              ))}
            </div>
          </TableCell>
        </TableRow>
      ) : null}
    </>
  );
}
