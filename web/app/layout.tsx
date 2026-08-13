import type { Metadata } from "next";
import { Suspense } from "react";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: {
    default: "SaaG",
    template: "%s - SaaG",
  },
  description: "System as a Graph (SaaG) Operations Panel",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="flex min-h-screen flex-col font-sans">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <Suspense fallback={null}>
            <Providers>
              <main className="flex flex-1 flex-col">{children}</main>
            </Providers>
          </Suspense>
        </ThemeProvider>
      </body>
    </html>
  );
}
