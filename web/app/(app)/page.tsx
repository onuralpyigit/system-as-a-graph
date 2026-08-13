"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useWorkingScope } from "@/lib/scope";

// UXD's post-login rule: scope selection if none active, else last-visited
// screen, else Model Visualization. There's no dedicated selection screen —
// the picker lives in the top bar — so "none active" resolves to Setup.
export default function Home() {
  const router = useRouter();
  const { scope, isLoading } = useWorkingScope();

  useEffect(() => {
    if (isLoading) return;
    router.replace(scope ? "/model" : "/setup");
  }, [isLoading, scope, router]);

  return null;
}
