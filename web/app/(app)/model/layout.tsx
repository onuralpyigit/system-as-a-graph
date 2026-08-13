import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Model",
};

export default function ModelLayout({ children }: { children: React.ReactNode }) {
  return children;
}
