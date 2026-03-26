import * as React from 'react'
import { cn } from '../cn'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-[var(--radius-md,6px)] border border-[var(--border)]',
          'bg-[var(--bg-elevated)] px-3 py-1 text-sm text-[var(--text-high)]',
          'placeholder:text-[var(--text-low)]',
          'focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-[var(--accent)]',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'transition-colors duration-[var(--duration-base,150ms)]',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = 'Input'

export { Input }
