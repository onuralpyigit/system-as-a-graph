"use client";

import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

const SEEN_KEY = ["jobs", "seen"];
const STORAGE_KEY = "saag.jobs.seen";

function readStored(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(STORAGE_KEY) ?? "";
}

/**
 * Which finished job the operator has already viewed, persisted across
 * sessions. Drives the nav-item dot: a job the operator hasn't looked at
 * yet stays marked, one they've visited the page for doesn't.
 */
export function useSeenJob() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: SEEN_KEY,
    queryFn: readStored,
    initialData: readStored,
    staleTime: Infinity,
  });

  const markSeen = useCallback(
    (jobId: string) => {
      window.localStorage.setItem(STORAGE_KEY, jobId);
      queryClient.setQueryData(SEEN_KEY, jobId);
    },
    [queryClient],
  );

  return { seenJobId: query.data ?? "", markSeen };
}
