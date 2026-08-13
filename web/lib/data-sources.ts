"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { setupApi } from "./api-client";
import type { DataSourceConfigureRequest } from "./api-types";
import { useSession } from "./use-session";

const DATA_SOURCES_KEY = ["data-sources"];

/** Configured external data sources (SRS MSD.2-5, 8). */
export function useDataSources() {
  const { session } = useSession();
  const token = session?.token;
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: DATA_SOURCES_KEY,
    queryFn: () => setupApi.listDataSources(token!),
    enabled: Boolean(token),
  });

  const configure = useMutation({
    mutationFn: (payload: DataSourceConfigureRequest) =>
      setupApi.configureDataSource(token!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DATA_SOURCES_KEY });
    },
  });

  const remove = useMutation({
    mutationFn: ({ sourceType, name }: { sourceType: string; name: string }) =>
      setupApi.deleteDataSource(token!, sourceType, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DATA_SOURCES_KEY });
    },
  });

  const sources = query.data ?? [];

  return {
    sources,
    // Whether any usable Configuration Management Database source is
    // configured — the real prerequisite for project/platform/version
    // selection, since that's queried through CMDB (SRS MSD.9-13).
    hasCmdbSource: sources.some(
      (source) => source.source_type === "configuration_management_database",
    ),
    isLoading: query.isLoading,
    configure: configure.mutate,
    isConfiguring: configure.isPending,
    remove: remove.mutate,
    isRemoving: remove.isPending,
  };
}
