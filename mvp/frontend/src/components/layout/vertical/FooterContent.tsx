'use client'

// Next Imports
import Link from 'next/link'

// Third-party Imports
import classnames from 'classnames'

// Hook Imports
import useVerticalNav from '@menu/hooks/useVerticalNav'

// Util Imports
import { verticalLayoutClasses } from '@layouts/utils/layoutClasses'

const FooterContent = () => {
  // Hooks
  const { isBreakpointReached } = useVerticalNav()

  return (
    <div
      className={classnames(verticalLayoutClasses.footerContent, 'flex items-center justify-between flex-wrap gap-4')}
    >
      <p className='text-xs text-[var(--text-low)]'>© 2025 SaaS-IA</p>
      {!isBreakpointReached && (
        <div className='flex items-center gap-4'>
          <Link href='#' className='text-xs text-[var(--text-low)] hover:text-[var(--accent)] transition-colors'>
            Documentation
          </Link>
          <Link href='/api-docs' className='text-xs text-[var(--text-low)] hover:text-[var(--accent)] transition-colors'>
            API Reference
          </Link>
          <Link href='#' className='text-xs text-[var(--text-low)] hover:text-[var(--accent)] transition-colors'>
            Support
          </Link>
        </div>
      )}
    </div>
  )
}

export default FooterContent
