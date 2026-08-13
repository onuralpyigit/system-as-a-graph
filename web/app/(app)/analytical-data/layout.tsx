import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Analytical Data",
};

export default function AnalyticalDataLayout({ children }: { children: React.ReactNode }) {
  return children;
}
