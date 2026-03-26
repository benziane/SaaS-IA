import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-[var(--radius-md,6px)] border p-4 text-sm [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4",
  {
    variants: {
      variant: {
        default: "border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-high)] [&>svg]:text-[var(--text-high)]",
        info: "border-[var(--accent)]/30 bg-[var(--accent)]/10 text-[var(--text-high)] [&>svg]:text-[var(--accent)]",
        success: "border-[var(--status-success-500,#22c55e)]/30 bg-[var(--status-success-500,#22c55e)]/10 text-green-400 [&>svg]:text-green-400",
        warning: "border-[var(--status-warning-500,#f59e0b)]/30 bg-[var(--status-warning-500,#f59e0b)]/10 text-amber-400 [&>svg]:text-amber-400",
        destructive: "border-[var(--status-error-500,#ef4444)]/30 bg-[var(--status-error-500,#ef4444)]/10 text-red-400 [&>svg]:text-red-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
))
Alert.displayName = "Alert"

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
))
AlertTitle.displayName = "AlertTitle"

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
))
AlertDescription.displayName = "AlertDescription"

export { Alert, AlertTitle, AlertDescription }

