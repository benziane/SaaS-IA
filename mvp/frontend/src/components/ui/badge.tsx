import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-[var(--radius-sm,4px)] px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--accent)] text-[var(--bg-app,#09090d)]",
        secondary:
          "bg-[var(--bg-elevated)] text-[var(--text-high)]",
        destructive:
          "bg-[var(--status-error-500,#ef4444)]/20 text-red-400 border border-[var(--status-error-500,#ef4444)]/30",
        success:
          "bg-[var(--status-success-500,#22c55e)]/20 text-green-400 border border-[var(--status-success-500,#22c55e)]/30",
        warning:
          "bg-[var(--status-warning-500,#f59e0b)]/20 text-amber-400 border border-[var(--status-warning-500,#f59e0b)]/30",
        outline: "border border-[var(--border)] text-[var(--text-mid)] bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }

