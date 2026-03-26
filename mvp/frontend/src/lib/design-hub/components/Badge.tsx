import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../cn'

const badgeVariants = cva(
  'inline-flex items-center rounded-[var(--radius-sm,4px)] px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default:     'bg-[var(--accent)] text-[var(--bg-app,#09090d)]',
        outline:     'border border-[var(--border)] text-[var(--text-mid)] bg-transparent',
        secondary:   'bg-[var(--bg-elevated)] text-[var(--text-high)]',
        destructive: 'bg-red-600/20 text-red-400 border border-red-600/30',
        success:     'bg-green-600/20 text-green-400 border border-green-600/30',
        warning:     'bg-amber-600/20 text-amber-400 border border-amber-600/30',
      },
    },
    defaultVariants: { variant: 'default' },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
