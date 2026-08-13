"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useContextSwitcherState } from "@/lib/context-switcher-state";
import { useDataSources } from "@/lib/data-sources";
import { useProjects, usePlatforms, useVersions, useWorkingScope } from "@/lib/scope";

function ColumnHeading({ children }: { children: string }) {
  return (
    <div className="px-2 pb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
      {children}
    </div>
  );
}

function OptionRow({
  label,
  active,
  effective,
  onSelect,
}: {
  label: string;
  active: boolean;
  effective?: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex w-full items-center justify-between rounded-sm px-2 py-1.5 text-left text-sm text-foreground transition-colors hover:bg-muted",
        active && "bg-muted",
      )}
    >
      <span className="flex items-center gap-1.5">
        {label}
        {effective ? (
          <span className="rounded-sm bg-status-conforming/15 px-1 py-0.5 text-[10px] font-medium leading-none text-status-conforming">
            effective
          </span>
        ) : null}
      </span>
      {active ? <Check className="h-3.5 w-3.5" /> : null}
    </button>
  );
}

export function ContextSwitcher() {
  const { open, setOpen } = useContextSwitcherState();
  const { scope, select } = useWorkingScope();
  const { hasCmdbSource, isLoading: sourcesLoading } = useDataSources();

  // Transient picker state: what the operator is navigating to inside the
  // popover. Seeded from the committed scope when one exists (reopening the
  // switcher should show your current selection) — but never auto-picked
  // from the fetched lists when it doesn't, so nothing shows as chosen until
  // the operator actually clicks project, then platform, then version
  // themselves (SRS VAE-01.4).
  const [projectKey, setProjectKey] = useState<string | undefined>(undefined);
  const [platformKey, setPlatformKey] = useState<string | undefined>(undefined);
  const [versionKey, setVersionKey] = useState<string | undefined>(undefined);

  const { data: projectsData } = useProjects();
  const projects = useMemo(() => projectsData?.projects ?? [], [projectsData]);

  useEffect(() => {
    if (projectKey) return;
    if (scope) setProjectKey(scope.project);
  }, [scope, projectKey]);

  const { data: platformsData } = usePlatforms(projectKey);
  const platforms = useMemo(() => platformsData?.platforms ?? [], [platformsData]);

  useEffect(() => {
    if (!projectKey || platformKey) return;
    if (scope && scope.project === projectKey) setPlatformKey(scope.platform);
  }, [projectKey, scope, platformKey]);

  const { data: versionsData } = useVersions(projectKey, platformKey);
  const versions = useMemo(() => versionsData?.versions ?? [], [versionsData]);

  useEffect(() => {
    if (!platformKey || versionKey) return;
    if (scope && scope.project === projectKey && scope.platform === platformKey) {
      setVersionKey(scope.system_version);
    }
  }, [platformKey, scope, projectKey, versionKey]);

  function selectProject(key: string) {
    setProjectKey(key);
    setPlatformKey(undefined);
    setVersionKey(undefined);
  }

  function selectPlatform(key: string) {
    setPlatformKey(key);
    setVersionKey(undefined);
  }

  function selectVersion(key: string) {
    setVersionKey(key);
    setOpen(false);
    if (projectKey && platformKey) {
      select({ project: projectKey, platform: platformKey, system_version: key });
    }
  }

  // Deliberately not projectKey/platformKey/versionKey here even when set:
  // those are the popover's pre-seeded picker state (first project, first
  // platform, effective version) shown before the operator has confirmed
  // anything — not a real selection. Showing them as the trigger label would
  // claim a scope is active when select() hasn't been called yet.
  const triggerLabel = scope
    ? { project: scope.project, platform: scope.platform, version: scope.system_version }
    : { project: "Select project", platform: "—", version: "—" };

  // Project/platform/version is populated by querying the configured CMDB
  // sources (SRS MSD.9-13) — without one, there's nothing to select yet.
  if (!sourcesLoading && !hasCmdbSource) {
    return (
      <Link
        href="/setup"
        className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-muted-foreground outline-none transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-1 focus-visible:ring-ring"
      >
        Configure a source to begin
      </Link>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-foreground outline-none transition-colors hover:bg-muted focus-visible:ring-1 focus-visible:ring-ring">
        <span>{triggerLabel.project}</span>
        <span className="text-muted-foreground">/</span>
        <span>{triggerLabel.platform}</span>
        <span className="text-muted-foreground">/</span>
        <span>{triggerLabel.version}</span>
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
      </PopoverTrigger>
      <PopoverContent className="w-[28rem]">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <ColumnHeading>Project</ColumnHeading>
            <div className="flex flex-col gap-0.5">
              {projects.map((project) => (
                <OptionRow
                  key={project}
                  label={project}
                  active={project === projectKey}
                  onSelect={() => selectProject(project)}
                />
              ))}
              {projects.length === 0 ? (
                <div className="px-2 py-1.5 text-xs text-muted-foreground">No projects</div>
              ) : null}
            </div>
          </div>
          <div>
            <ColumnHeading>Platform</ColumnHeading>
            <div className="flex flex-col gap-0.5">
              {platforms.map((platform) => (
                <OptionRow
                  key={platform}
                  label={platform}
                  active={platform === platformKey}
                  onSelect={() => selectPlatform(platform)}
                />
              ))}
            </div>
          </div>
          <div>
            <ColumnHeading>Version</ColumnHeading>
            <div className="flex flex-col gap-0.5">
              {versions.map((version) => (
                <OptionRow
                  key={version.version}
                  label={version.version}
                  active={version.version === versionKey}
                  effective={version.is_effective}
                  onSelect={() => selectVersion(version.version)}
                />
              ))}
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
