import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../cn'

const alertVariants = cva(
  'relative w-full rounded-[var(--radius-md,6px)] border p-4 text-sm',
  {
    variants: {
      variant: {
        default:     'border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-high)]',
        info:        'border-[var(--accent)]/30 bg-[var(--accent)]/10 text-[var(--text-high)]',
        success:     'border-green-600/30 bg-green-600/10 text-green-400',
        warning:     'border-amber-500/30 bg-amber-500/10 text-amber-400',
        destructive: 'border-red-600/30 bg-red-600/10 text-red-400',
      },
    },
    defaultVariants: { variant: 'default' },
  }
)

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
))
Alert.displayName = 'Alert'

const AlertTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <h5 ref={ref} className={cn('mb-1 font-semibold leading-none tracking-tight', className)} {...props} />
  )
)
AlertTitle.displayName = 'AlertTitle'

const AlertDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('text-sm opacity-90', className)} {...props} />
  )
)
AlertDescription.displayName = 'AlertDescription'

export { Alert, AlertTitle, AlertDescription }
