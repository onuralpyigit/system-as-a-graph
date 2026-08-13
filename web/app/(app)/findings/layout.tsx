import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Findings",
};

export default function FindingsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
