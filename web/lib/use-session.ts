"use client";

import { useGetIdentity } from "@refinedev/core";

import type { StoredSession } from "./session-storage";

/** The signed-in operator's session, including the bearer token API calls need. */
export function useSession() {
  const { data, isLoading } = useGetIdentity<StoredSession>();
  return { session: data ?? null, isLoading };
}
