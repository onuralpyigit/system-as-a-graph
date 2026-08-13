"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLogout } from "@refinedev/core";
import { LogOut } from "lucide-react";

import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSession } from "@/lib/use-session";
import { ContextSwitcher } from "./context-switcher";
import { useNavGroups } from "./nav-groups";
import { ThemeToggle } from "./theme-toggle";

function NavDot({ state }: { state: "running" | "succeeded" | "failed" }) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-block h-1.5 w-1.5 rounded-full",
        state === "running"
          ? "animate-pulse bg-status-info"
          : state === "failed"
            ? "bg-status-critical"
            : "bg-status-conforming",
      )}
    />
  );
}

function GroupNav() {
  const pathname = usePathname();
  const navGroups = useNavGroups();

  return (
    <nav className="flex items-center gap-5">
      {navGroups.map((group) => {
        const active = pathname === group.href || pathname.startsWith(`${group.href}/`);
        return (
          <Link
            key={group.key}
            href={group.href}
            className={cn(
              "flex items-center gap-1.5 text-sm transition-colors",
              active ? "font-semibold text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {group.dot ? <NavDot state={group.dot} /> : null}
            {group.label}
          </Link>
        );
      })}
    </nav>
  );
}

function SessionMenu() {
  const { session } = useSession();
  const { mutate: logout } = useLogout();
  const initials = (session?.display_name ?? session?.username ?? "?")
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="rounded-full outline-none focus-visible:ring-1 focus-visible:ring-ring">
        <Avatar>
          <AvatarFallback>{initials}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>{session?.username ?? "—"}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => logout()}>
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center gap-6">
        <ContextSwitcher />
        <GroupNav />
      </div>
      <div className="flex items-center gap-4">
        <ThemeToggle />
        <SessionMenu />
      </div>
    </header>
  );
}
