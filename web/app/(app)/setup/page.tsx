"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Compass } from "lucide-react";
import {
  type ColumnDef,
  getCoreRowModel,
  getPaginationRowModel,
  useReactTable,
} from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PageHeader } from "@/components/app-shell/page-header";
import { ProductionRunRow } from "@/components/setup/production-run-row";
import { SourceConfiguration } from "@/components/setup/source-configuration";
import { SOURCE_TYPES } from "@/components/setup/source-types";
import type { ProductionJobResponse } from "@/lib/api-types";
import { useContextSwitcherState } from "@/lib/context-switcher-state";
import { useDataSources } from "@/lib/data-sources";
import { useSeenJob } from "@/lib/job-acknowledgement";
import { useProductionHistory, useSelectFile, useStartProduction } from "@/lib/production";
import { useWorkingScope } from "@/lib/scope";

// One column per run, identified only — ProductionRunRow renders the actual
// cells, so TanStack Table is used here purely for its pagination row model
// (UXD §5/§6: TanStack Table owns sort/filter/pagination for every data
// table; the production run history didn't follow that convention yet).
const RUN_COLUMNS: ColumnDef<ProductionJobResponse>[] = [{ accessorKey: "job_id" }];
const PAGE_SIZE = 10;

export default function SetupPage() {
  const { scope } = useWorkingScope();
  const { setOpen: setContextSwitcherOpen } = useContextSwitcherState();
  const { jobs, hasActiveJob } = useProductionHistory();
  const { selectFile } = useSelectFile();
  const { sources, hasCmdbSource } = useDataSources();
  const { mutate: startProduction, isPending: isStarting } = useStartProduction();
  const { markSeen } = useSeenJob();

  const table = useReactTable({
    data: jobs,
    columns: RUN_COLUMNS,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: PAGE_SIZE } },
  });

  // Visiting the page while the latest run is finished is what clears its
  // nav-item dot — a run still in progress isn't "seen" until it resolves.
  const latestJob = jobs[0];
  const selectedJob = jobs.find(
    (job) => job.run_id === scope?.selected_model_setup_data_run_id,
  );
  useEffect(() => {
    if (latestJob && latestJob.status !== "in_progress") {
      markSeen(latestJob.job_id);
    }
  }, [latestJob, markSeen]);

  // Production tolerates gaps (a source's data is just excluded, not a hard
  // failure), so this warns rather than blocks — the operator decides.
  const unconfiguredCount = SOURCE_TYPES.filter(
    (type) =>
      type.value !== "configuration_management_database" &&
      !sources.some((source) => source.source_type === type.value),
  ).length;

  return (
    <div className="flex flex-col gap-6 pb-10">
      <PageHeader
        title="Setup"
        action={
          <div className="flex flex-col items-end gap-1">
            <Button
              onClick={() => startProduction()}
              disabled={!scope || !hasCmdbSource || hasActiveJob || isStarting}
            >
              {hasActiveJob ? "Production running…" : "Produce Model Setup Data"}
            </Button>
            {scope && !hasCmdbSource ? (
              <span className="text-xs text-status-critical">
                No Configuration Management Database configured — production will fail
              </span>
            ) : scope && unconfiguredCount > 0 ? (
              <span className="text-xs text-status-medium">
                {unconfiguredCount} source{unconfiguredCount === 1 ? "" : "s"} not configured —
                production may exclude data
              </span>
            ) : null}
          </div>
        }
      />

      <SourceConfiguration />

      {!scope ? (
        <div className="mx-6 flex flex-col items-center gap-3 rounded-lg border border-dashed border-border px-6 py-10 text-center">
          <Compass className="h-6 w-6 text-muted-foreground" aria-hidden />
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-foreground">No scope selected</p>
            <p className="text-sm text-muted-foreground">
              {hasCmdbSource
                ? "Choose a project, platform, and version to see or produce Model Setup Data."
                : "Configure a Configuration Management Database above, then choose a project, platform, and version — there's nothing to select until one exists."}
            </p>
          </div>
          {hasCmdbSource ? (
            <Button size="sm" onClick={() => setContextSwitcherOpen(true)}>
              Select project, platform, and version
            </Button>
          ) : null}
        </div>
      ) : (
        <>
          <div className="px-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>File</TableHead>
                  <TableHead>Started at</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Finished at</TableHead>
                  <TableHead>Entities</TableHead>
                  <TableHead>Relations</TableHead>
                  <TableHead className="w-20" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <ProductionRunRow
                    key={row.original.job_id}
                    job={row.original}
                    isSelected={scope.selected_model_setup_data_run_id === row.original.run_id}
                    onSelect={selectFile}
                  />
                ))}
                {jobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-muted-foreground">
                      No production runs yet for this scope.
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </div>

          {jobs.length > PAGE_SIZE ? (
            <div className="flex items-center justify-between px-6 text-sm text-muted-foreground">
              <span>
                Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()} (
                {jobs.length} runs)
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!table.getCanPreviousPage()}
                  onClick={() => table.previousPage()}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!table.getCanNextPage()}
                  onClick={() => table.nextPage()}
                >
                  Next
                </Button>
              </div>
            </div>
          ) : null}

          {jobs.length > 0 ? (
            <div className="flex items-center justify-between px-6">
              <span className="text-sm text-muted-foreground">
                {scope.selected_model_setup_data_run_id ? (
                  <>
                    Selected MSD file:{" "}
                    <span className="font-mono text-xs text-foreground">
                      {selectedJob?.file_path ?? scope.selected_model_setup_data_run_id}
                    </span>
                  </>
                ) : (
                  <span className="text-status-medium">
                    No file selected — choose one above.
                  </span>
                )}
              </span>
              {scope.selected_model_setup_data_run_id ? (
                <Button asChild size="sm" variant="outline">
                  <Link href="/model">Continue to Model →</Link>
                </Button>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
