"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, scopeApi } from "./api-client";
import type { ScopeSelectionRequest, WorkingScopeResponse } from "./api-types";
import { useSession } from "./use-session";

const CURRENT_SCOPE_KEY = ["scope", "current"];

/** The operator's current project/platform/version selection (SRS VAE-01.4). */
export function useWorkingScope() {
  const { session } = useSession();
  const token = session?.token;
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: CURRENT_SCOPE_KEY,
    queryFn: async () => {
      try {
        return await scopeApi.current(token!);
      } catch (error) {
        // No project/platform/version selected yet is not a fetch failure.
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    enabled: Boolean(token),
  });

  const select = useMutation({
    mutationFn: (payload: ScopeSelectionRequest) => scopeApi.select(token!, payload),
    onSuccess: (scope) => {
      queryClient.setQueryData<WorkingScopeResponse | null>(CURRENT_SCOPE_KEY, scope);
    },
  });

  return {
    scope: query.data ?? null,
    isLoading: query.isLoading,
    select: select.mutate,
    isSelecting: select.isPending,
  };
}

export function useProjects() {
  const { session } = useSession();
  const token = session?.token;
  return useQuery({
    queryKey: ["scope", "projects"],
    queryFn: () => scopeApi.listProjects(token!),
    enabled: Boolean(token),
  });
}

export function usePlatforms(project: string | undefined) {
  const { session } = useSession();
  const token = session?.token;
  return useQuery({
    queryKey: ["scope", "platforms", project],
    queryFn: () => scopeApi.listPlatforms(token!, project!),
    enabled: Boolean(token && project),
  });
}

export function useVersions(project: string | undefined, platform: string | undefined) {
  const { session } = useSession();
  const token = session?.token;
  return useQuery({
    queryKey: ["scope", "versions", project, platform],
    queryFn: () => scopeApi.listVersions(token!, project!, platform!),
    enabled: Boolean(token && project && platform),
  });
}
