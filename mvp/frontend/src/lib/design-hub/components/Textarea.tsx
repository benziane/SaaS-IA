import * as React from 'react'
import { cn } from '../cn'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          'flex min-h-[80px] w-full rounded-[var(--radius-md,6px)] border border-[var(--border)]',
          'bg-[var(--bg-elevated)] px-3 py-2 text-sm text-[var(--text-high)]',
          'placeholder:text-[var(--text-low)]',
          'focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-[var(--accent)]',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'transition-colors duration-[var(--duration-base,150ms)] resize-none',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = 'Textarea'
export { Textarea }
