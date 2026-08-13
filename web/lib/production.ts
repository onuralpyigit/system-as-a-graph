"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, setupApi } from "./api-client";
import type { ModelSetupDataFileResponse, ProductionJobResponse } from "./api-types";
import { useWorkingScope } from "./scope";
import { useSession } from "./use-session";

const HISTORY_KEY = ["production", "history"];
const FILES_KEY = ["model-setup-data", "files"];

function hasActiveJob(jobs: ProductionJobResponse[] | undefined): boolean {
  return (jobs ?? []).some((job) => job.status === "in_progress");
}

/** Production processes started for the current selection (SRS VAE-01.6). */
export function useProductionHistory() {
  const { session } = useSession();
  const { scope } = useWorkingScope();
  const token = session?.token;

  const query = useQuery({
    queryKey: [...HISTORY_KEY, scope?.project, scope?.platform, scope?.system_version],
    queryFn: async () => {
      try {
        return await setupApi.productionHistory(token!);
      } catch (error) {
        if (error instanceof ApiError && error.status === 409) return [];
        throw error;
      }
    },
    enabled: Boolean(token && scope),
    refetchInterval: (latest) => (hasActiveJob(latest.state.data) ? 2000 : false),
  });

  return {
    jobs: query.data ?? [],
    isLoading: query.isLoading,
    hasActiveJob: hasActiveJob(query.data),
  };
}

export function useStartProduction() {
  const { session } = useSession();
  const token = session?.token;
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => setupApi.startProduction(token!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HISTORY_KEY });
    },
  });
}

/** Failures recorded during one production run (SRS VAE-01.8), fetched on demand. */
export function useRunErrors(runId: string, enabled: boolean, poll = false) {
  const { session } = useSession();
  const token = session?.token;

  const query = useQuery({
    queryKey: ["production", "errors", runId],
    queryFn: () => setupApi.productionErrorsForRun(token!, runId),
    enabled: Boolean(token && runId && enabled),
    refetchInterval: poll ? 3000 : false,
  });

  return { errors: query.data ?? [], isLoading: query.isLoading };
}

/** Selects which produced Model Setup Data file the working scope uses. */
export function useSelectFile() {
  const { session } = useSession();
  const token = session?.token;
  const queryClient = useQueryClient();

  const select = useMutation({
    mutationFn: (runId: string) => setupApi.selectFile(token!, runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scope", "current"] });
    },
  });

  return { selectFile: select.mutate };
}

/** Produced Model Setup Data files for the current selection (SRS VAE-01.5). */
export function useModelSetupDataFiles(pollWhileActive: boolean) {
  const { session } = useSession();
  const { scope } = useWorkingScope();
  const token = session?.token;

  const query = useQuery({
    queryKey: [...FILES_KEY, scope?.project, scope?.platform, scope?.system_version],
    queryFn: () => setupApi.listFiles(token!),
    enabled: Boolean(token && scope),
    refetchInterval: pollWhileActive ? 3000 : false,
  });

  const { selectFile } = useSelectFile();

  return {
    files: query.data ?? ([] as ModelSetupDataFileResponse[]),
    isLoading: query.isLoading,
    selectFile,
  };
}
