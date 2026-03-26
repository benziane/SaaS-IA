import * as React from 'react'
import { cn } from '../cn'

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-[var(--radius-md,6px)] bg-[var(--bg-elevated)]',
        className
      )}
      {...props}
    />
  )
}
export { Skeleton }
