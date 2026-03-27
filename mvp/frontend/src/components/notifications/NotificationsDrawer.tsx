'use client'

import { useRouter } from 'next/navigation'
import {
  AlertTriangle,
  AtSign,
  Bell,
  CheckCircle2,
  Settings,
  Sparkles,
  X,
  XCircle,
} from 'lucide-react'

import {
  Sheet,
  SheetContent,
} from '@/components/ui/sheet'
import {
  useMarkAllRead,
  useMarkRead,
  useNotifications,
} from '@/hooks/useNotifications'
import type { Notification, NotificationType } from '@/features/notifications/types'

/* ========================================================================
   HELPERS
   ======================================================================== */

const TYPE_META: Record<
  NotificationType,
  { Icon: React.ElementType; color: string }
> = {
  info:        { Icon: Bell,         color: 'var(--accent)' },
  success:     { Icon: CheckCircle2, color: 'var(--success)' },
  warning:     { Icon: AlertTriangle,color: 'var(--warning)' },
  error:       { Icon: XCircle,      color: 'var(--error)' },
  ai_complete: { Icon: Sparkles,     color: 'var(--accent)' },
  mention:     { Icon: AtSign,       color: 'var(--accent)' },
  system:      { Icon: Settings,     color: 'var(--text-mid)' },
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1)  return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

/* ========================================================================
   SUB-COMPONENTS
   ======================================================================== */

function SkeletonRow() {
  return (
    <div className='flex gap-3 px-4 py-3 animate-pulse'>
      <div className='w-8 h-8 rounded-full bg-[var(--bg-elevated)] shrink-0' />
      <div className='flex-1 space-y-2 pt-0.5'>
        <div className='h-3 w-2/3 rounded bg-[var(--bg-elevated)]' />
        <div className='h-2.5 w-full rounded bg-[var(--bg-elevated)]' />
        <div className='h-2 w-1/4 rounded bg-[var(--bg-elevated)]' />
      </div>
    </div>
  )
}

function NotificationRow({
  notification,
  onRead,
}: {
  notification: Notification
  onRead: (id: string, link: string | null) => void
}) {
  const { Icon, color } = TYPE_META[notification.type] ?? TYPE_META.info

  return (
    <button
      type='button'
      onClick={() => onRead(notification.id, notification.link)}
      className={[
        'w-full flex items-start gap-3 px-4 py-3 text-left transition-colors',
        'hover:bg-[var(--bg-elevated)]',
        notification.is_read
          ? 'bg-transparent'
          : 'bg-[color-mix(in_srgb,var(--accent)_5%,transparent)] border-l-2 border-l-[var(--accent)]',
      ].join(' ')}
    >
      {/* Icon circle */}
      <span
        className='flex items-center justify-center w-8 h-8 rounded-full shrink-0'
        style={{ backgroundColor: `color-mix(in srgb,${color} 12%,transparent)` }}
      >
        <Icon className='w-4 h-4' style={{ color }} />
      </span>

      {/* Text */}
      <div className='flex-1 min-w-0'>
        <p className='text-sm font-medium text-[var(--text-high)] leading-snug'>
          {notification.title}
        </p>
        <p className='text-xs text-[var(--text-mid)] line-clamp-2 mt-0.5 leading-relaxed'>
          {notification.body}
        </p>
        <p className='text-[10px] text-[var(--text-low)] mt-1'>
          {relativeTime(notification.created_at)}
        </p>
      </div>
    </button>
  )
}

/* ========================================================================
   MAIN COMPONENT
   ======================================================================== */

interface NotificationsDrawerProps {
  open: boolean
  onClose: () => void
}

export default function NotificationsDrawer({ open, onClose }: NotificationsDrawerProps) {
  const router = useRouter()
  const { data, isLoading } = useNotifications()
  const markRead    = useMarkRead()
  const markAllRead = useMarkAllRead()

  const notifications = data?.items ?? []
  const unreadCount   = notifications.filter((n) => !n.is_read).length

  function handleRead(id: string, link: string | null) {
    markRead.mutate(id)
    if (link) {
      router.push(link)
      onClose()
    }
  }

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        side='right'
        className='w-[380px] sm:max-w-[380px] p-0 flex flex-col gap-0'
      >
        {/* Header */}
        <div className='flex items-center justify-between px-4 py-3.5 border-b border-[var(--border)]'>
          <div className='flex items-center gap-2'>
            <h2 className='text-base font-semibold text-[var(--text-high)]'>
              Notifications
            </h2>
            {unreadCount > 0 && (
              <span className='inline-flex items-center justify-center h-5 min-w-[1.25rem] px-1.5 rounded-full
                               bg-[var(--accent)] text-white text-[10px] font-semibold leading-none'>
                {unreadCount}
              </span>
            )}
          </div>

          <div className='flex items-center gap-1'>
            {unreadCount > 0 && (
              <button
                type='button'
                onClick={() => markAllRead.mutate()}
                disabled={markAllRead.isPending}
                className='text-xs text-[var(--accent)] hover:underline disabled:opacity-50 px-1'
              >
                Mark all as read
              </button>
            )}
            <button
              type='button'
              onClick={onClose}
              aria-label='Close notifications'
              className='p-1.5 rounded-md text-[var(--text-mid)] hover:bg-[var(--bg-elevated)] transition-colors'
            >
              <X className='w-4 h-4' />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className='flex-1 overflow-y-auto'>
          {isLoading ? (
            <>
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
            </>
          ) : notifications.length === 0 ? (
            <div className='flex flex-col items-center justify-center gap-3 h-full py-20 text-[var(--text-low)]'>
              <Bell className='w-10 h-10 opacity-30' />
              <p className='text-sm'>No notifications yet</p>
            </div>
          ) : (
            <div className='divide-y divide-[var(--border)]'>
              {notifications.map((n) => (
                <NotificationRow key={n.id} notification={n} onRead={handleRead} />
              ))}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
