import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../cn'

const buttonVariants = cva(
  // Base styles — consume recipe tokens via CSS vars
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium',
    'transition-all duration-[var(--duration-base,200ms)]',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]',
    'disabled:pointer-events-none disabled:opacity-50',
    'border border-transparent',
  ].join(' '),
  {
    variants: {
      variant: {
        default: [
          'bg-[var(--accent)] text-[var(--bg-app,#09090d)]',
          'hover:bg-[var(--accent-dim,var(--accent))]',
          'shadow-[var(--shadow-sm,none)]',
        ].join(' '),
        outline: [
          'border-[var(--border)] bg-transparent text-[var(--text-high)]',
          'hover:bg-[var(--bg-elevated)] hover:border-[var(--accent)]',
        ].join(' '),
        ghost: [
          'bg-transparent text-[var(--text-mid)]',
          'hover:bg-[var(--bg-elevated)] hover:text-[var(--text-high)]',
        ].join(' '),
        destructive: [
          'bg-red-600 text-white',
          'hover:bg-red-700',
        ].join(' '),
        secondary: [
          'bg-[var(--bg-elevated)] text-[var(--text-high)]',
          'hover:bg-[var(--bg-surface)]',
        ].join(' '),
      },
      size: {
        sm:   'h-8  px-3 text-xs rounded-[var(--radius-sm,4px)]',
        md:   'h-10 px-4 text-sm rounded-[var(--radius-md,6px)]',
        lg:   'h-12 px-6 text-base rounded-[var(--radius-lg,8px)]',
        icon: 'h-9  w-9      rounded-[var(--radius-md,6px)]',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
