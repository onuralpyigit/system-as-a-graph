"use client";

import { useSeenJob } from "@/lib/job-acknowledgement";
import { useProductionHistory } from "@/lib/production";

export type NavDotState = "running" | "succeeded" | "failed" | null;

export interface NavGroup {
  key: string;
  label: string;
  href: string;
  dot: NavDotState;
}

/**
 * Per-group background-job indicator (UXD §5): running blinks, a finished
 * job the operator hasn't looked at yet shows solid, one they've visited the
 * page for goes back to no dot. Only Setup has a job source today; the rest
 * stay dot-less until their own increments land.
 */
export function useNavGroups(): NavGroup[] {
  const { jobs } = useProductionHistory();
  const { seenJobId } = useSeenJob();

  const latest = jobs[0];
  let setupDot: NavDotState = null;
  if (latest) {
    if (latest.status === "in_progress") {
      setupDot = "running";
    } else if (latest.job_id !== seenJobId) {
      setupDot = latest.status === "failed" ? "failed" : "succeeded";
    }
  }

  return [
    { key: "setup", label: "Setup", href: "/setup", dot: setupDot },
    { key: "model", label: "Model", href: "/model", dot: null },
    { key: "analytical-data", label: "Analytical Data", href: "/analytical-data", dot: null },
    { key: "findings", label: "Findings", href: "/findings", dot: null },
  ];
}
