"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, DatabaseZap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDataSources } from "@/lib/data-sources";
import type { DataSourceResponse } from "@/lib/api-types";
import { useSourceStatusStream } from "@/lib/source-status";
import { cn } from "@/lib/utils";

import { SourceEditDialog } from "./source-edit-dialog";
import { SOURCE_TYPES } from "./source-types";

type TypeStatus = "not-configured" | "pending" | "reachable" | "unreachable";

function StatusDot({ status }: { status: TypeStatus }) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-block h-1.5 w-1.5 rounded-full",
        status === "not-configured"
          ? "border border-dashed border-muted-foreground/50"
          : status === "pending"
            ? "bg-muted-foreground/40"
            : status === "reachable"
              ? "bg-status-conforming"
              : "bg-status-critical",
      )}
    />
  );
}

export function SourceConfiguration() {
  const { sources, configure, isConfiguring, remove, isRemoving } = useDataSources();
  const { snapshot } = useSourceStatusStream();
  const [editing, setEditing] = useState<DataSourceResponse | null>(null);
  const [addType, setAddType] = useState<string | undefined>(undefined);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);

  function statusFor(sourceType: string): TypeStatus {
    const configured = sources.filter((source) => source.source_type === sourceType);
    if (configured.length === 0) return "not-configured";
    if (!snapshot) return "pending";

    const statuses = configured.map((source) =>
      snapshot.statuses.find(
        (item) => item.source_type === sourceType && item.source_name === source.name,
      ),
    );
    if (statuses.some((status) => !status)) return "pending";
    return statuses.every((status) => status!.accessibility === "reachable")
      ? "reachable"
      : "unreachable";
  }

  function reachabilityFor(source: DataSourceResponse): boolean | undefined {
    const status = snapshot?.statuses.find(
      (item) => item.source_type === source.source_type && item.source_name === source.name,
    );
    return status ? status.accessibility === "reachable" : undefined;
  }

  function openEdit(source: DataSourceResponse) {
    setEditing(source);
    setAddType(undefined);
    setDialogOpen(true);
  }

  function openAdd(sourceType?: string) {
    setEditing(null);
    setAddType(sourceType);
    setDialogOpen(true);
  }

  function removeSource(source: DataSourceResponse) {
    if (!window.confirm(`Delete data source "${source.name}"?`)) return;
    remove({ sourceType: source.source_type, name: source.name });
  }

  const overallStatus = SOURCE_TYPES.map((type) => statusFor(type.value));
  const anyConfigured = sources.length > 0;

  // "attention needed" is reserved for an actual reachability failure — a
  // type nobody's configured yet (some are legitimately optional, e.g.
  // network topology can use manual entry instead) isn't broken, so it gets
  // its own neutral wording rather than reading as the same problem.
  const unreachableCount = overallStatus.filter((status) => status === "unreachable").length;
  const notConfiguredCount = overallStatus.filter((status) => status === "not-configured").length;
  const pendingCount = overallStatus.filter((status) => status === "pending").length;

  let sourcesBadgeVariant: "conforming" | "critical" | "info" | "default" = "conforming";
  let sourcesBadgeLabel = "all reachable";
  if (unreachableCount > 0) {
    sourcesBadgeVariant = "critical";
    sourcesBadgeLabel = "attention needed";
  } else if (pendingCount > 0) {
    sourcesBadgeVariant = "info";
    sourcesBadgeLabel = "checking…";
  } else if (notConfiguredCount > 0) {
    sourcesBadgeVariant = "default";
    sourcesBadgeLabel = `${notConfiguredCount} not configured`;
  }

  if (!anyConfigured) {
    return (
      <>
        <div className="mx-6 flex flex-col items-center gap-3 rounded-lg border border-dashed border-border px-6 py-10 text-center">
          <DatabaseZap className="h-6 w-6 text-muted-foreground" aria-hidden />
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-foreground">No data sources configured</p>
            <p className="text-sm text-muted-foreground">
              Add a Configuration Management Database to discover projects, platforms, and
              versions (SRS MSD.9-13).
            </p>
          </div>
          <Button
            size="sm"
            onClick={() => openAdd("configuration_management_database")}
          >
            Add Configuration Management Database
          </Button>
        </div>

        <SourceEditDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          source={editing}
          defaultSourceType={addType}
          isSubmitting={isConfiguring}
          onSubmit={(payload) => {
            configure(payload);
            setDialogOpen(false);
          }}
        />
      </>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between px-6">
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          <span>Sources</span>
          <Badge variant={sourcesBadgeVariant}>{sourcesBadgeLabel}</Badge>
        </button>
        <Button size="sm" variant="outline" onClick={() => openAdd()}>
          Add source
        </Button>
      </div>

      {!expanded ? (
        <div className="flex flex-wrap gap-x-6 gap-y-2 px-6 text-sm">
          {SOURCE_TYPES.map((type) => {
            const status = statusFor(type.value);
            const configured = sources.filter((source) => source.source_type === type.value);
            return (
              <div key={type.value} className="flex items-center gap-1.5">
                <StatusDot status={status} />
                <span className={status === "not-configured" ? "text-muted-foreground" : ""}>
                  {type.label}
                </span>
                {status === "not-configured" ? (
                  <Button
                    size="sm"
                    variant="link"
                    className="h-auto p-0 text-xs"
                    onClick={() => openAdd(type.value)}
                  >
                    Add
                  </Button>
                ) : configured.length === 1 ? (
                  <Button
                    size="sm"
                    variant="link"
                    className="h-auto p-0 text-xs"
                    onClick={() => openEdit(configured[0])}
                  >
                    Edit
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="link"
                    className="h-auto p-0 text-xs"
                    onClick={() => setExpanded(true)}
                  >
                    {configured.length} sources
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="px-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-6" />
                <TableHead>Type</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Address</TableHead>
                <TableHead>Credential</TableHead>
                <TableHead className="w-32" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {sources.map((source) => (
                <TableRow key={`${source.source_type}/${source.name}`}>
                  <TableCell>
                    <StatusDot
                      status={
                        reachabilityFor(source) === undefined
                          ? "pending"
                          : reachabilityFor(source)
                            ? "reachable"
                            : "unreachable"
                      }
                    />
                  </TableCell>
                  <TableCell className="text-muted-foreground">{source.source_type}</TableCell>
                  <TableCell className="font-mono text-xs">{source.name}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {source.connection_address}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {source.username || "—"}
                    {source.secret_set ? " · secret set" : ""}
                  </TableCell>
                  <TableCell className="flex items-center gap-1">
                    <Button size="sm" variant="ghost" onClick={() => openEdit(source)}>
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={isRemoving}
                      onClick={() => removeSource(source)}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <SourceEditDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        source={editing}
        defaultSourceType={addType}
        isSubmitting={isConfiguring}
        onSubmit={(payload) => {
          configure(payload);
          setDialogOpen(false);
        }}
      />
    </div>
  );
}
