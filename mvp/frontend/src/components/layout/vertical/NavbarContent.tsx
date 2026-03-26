'use client'

// Third-party Imports
import classnames from 'classnames'

// Lucide Imports
import { Search } from 'lucide-react'

// Component Imports
import NavToggle from './NavToggle'
import ModeDropdown from '@components/layout/shared/ModeDropdown'
import UserDropdown from '@components/layout/shared/UserDropdown'

// Design Hub Imports
import { Badge } from '@/components/ui/badge'

// Util Imports
import { verticalLayoutClasses } from '@layouts/utils/layoutClasses'

const NavbarContent = () => {
  return (
    <div className={classnames(verticalLayoutClasses.navbarContent, 'flex items-center justify-between gap-4 is-full')}>
      <div className='flex items-center gap-4'>
        <NavToggle />
        <ModeDropdown />
      </div>
      <div
        onClick={() => {
          const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true });
          window.dispatchEvent(event);
        }}
        className='hidden md:flex items-center gap-2 px-4 py-1.5 rounded-lg border border-[var(--border)] cursor-pointer text-[var(--text-mid)] hover:bg-[var(--bg-elevated)] min-w-[200px]'
      >
        <Search className='h-[18px] w-[18px]' />
        <span className='flex-1 text-sm text-[var(--text-mid)]'>
          Search...
        </span>
        <Badge variant='outline' className='h-5 text-[0.65rem] px-1.5 py-0'>Ctrl+K</Badge>
      </div>
      <div className='flex items-center'>
        <UserDropdown />
      </div>
    </div>
  )
}

export default NavbarContent
