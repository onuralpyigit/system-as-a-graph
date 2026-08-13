import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  action?: ReactNode;
  className?: string;
}

export function PageHeader({ title, action, className }: PageHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between gap-4 px-6 pt-6", className)}>
      <h1 className="text-[30px] font-bold leading-tight tracking-tight text-foreground">
        {title}
      </h1>
      {action}
    </div>
  );
}
