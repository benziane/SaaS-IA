'use client'

import { useState } from 'react'

// Third-party Imports
import classnames from 'classnames'

// Lucide Imports
import { Search, Bell } from 'lucide-react'

// Component Imports
import NavToggle from './NavToggle'
import ModeDropdown from '@components/layout/shared/ModeDropdown'
import UserDropdown from '@components/layout/shared/UserDropdown'
import NotificationsDrawer from '@/components/notifications/NotificationsDrawer'

// Hook Imports
import { useUnreadCount } from '@/hooks/useNotifications'

// Util Imports
import { verticalLayoutClasses } from '@layouts/utils/layoutClasses'

const NavbarContent = () => {
  const [notifOpen, setNotifOpen] = useState(false)
  const { data: unreadCount = 0 } = useUnreadCount()

  const openCommandPalette = () => {
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))
  }

  return (
    <div className={classnames(verticalLayoutClasses.navbarContent, 'flex items-center justify-between gap-3 is-full')}>

      {/* Left — toggle */}
      <div className='flex items-center gap-2'>
        <NavToggle />
      </div>

      {/* Center — command palette trigger */}
      <div
        role='button'
        tabIndex={0}
        onClick={openCommandPalette}
        onKeyDown={(e) => e.key === 'Enter' && openCommandPalette()}
        aria-label='Open command palette'
        className='hidden md:flex items-center gap-2.5 px-4 py-2 rounded-lg
                   border border-[var(--border)] cursor-pointer
                   text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]
                   hover:border-[color-mix(in_srgb,var(--accent)_30%,transparent)]
                   backdrop-blur-sm transition-all duration-150
                   min-w-[280px] max-w-[440px] w-full'
      >
        <Search className='h-4 w-4 shrink-0' />
        <span className='flex-1 text-sm'>Search or run a command…</span>
        <kbd className='inline-flex items-center gap-0.5 rounded border border-[var(--border)]
                        px-1.5 py-0.5 text-[0.6rem] font-mono text-[var(--text-low)]'>
          Ctrl+K
        </kbd>
      </div>

      {/* Right — actions */}
      <div className='flex items-center gap-1'>
        <ModeDropdown />

        {/* Notification bell */}
        <button
          onClick={() => setNotifOpen(true)}
          className='relative inline-flex items-center justify-center rounded-full p-2
                     text-[var(--text-high)] hover:bg-[var(--bg-elevated)] transition-colors'
          aria-label='Notifications'
        >
          <Bell className='h-5 w-5' />
          {unreadCount > 0 && (
            <span className='absolute top-1 right-1 w-2 h-2 rounded-full bg-[var(--error)]' />
          )}
        </button>

        <UserDropdown />
      </div>

      <NotificationsDrawer open={notifOpen} onClose={() => setNotifOpen(false)} />

    </div>
  )
}

export default NavbarContent
