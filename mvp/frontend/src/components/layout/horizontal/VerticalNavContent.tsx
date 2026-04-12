// React Imports
import { useRef } from 'react'

// Next Imports
import Link from 'next/link'

// MUI Imports — required for shadow gradient that uses theme.direction and theme.mixins
import { useTheme } from '@mui/material/styles'

// Third-party Imports
import PerfectScrollbar from 'react-perfect-scrollbar'

// Type Imports
import type { ChildrenType } from '@core/types'

// Component Imports
import NavHeader from '@menu/components/vertical-menu/NavHeader'
import Logo from '@components/layout/shared/Logo'
import NavCollapseIcons from '@menu/components/vertical-menu/NavCollapseIcons'

// Hook Imports
import useHorizontalNav from '@menu/hooks/useHorizontalNav'

// Util Imports
import { mapHorizontalToVerticalMenu } from '@menu/utils/menuUtils'

const MenuToggle = (
  <div className='icon-wrapper'>
    <i className='bx-bxs-chevron-left' />
  </div>
)

const VerticalNavContent = ({ children }: ChildrenType) => {
  // Hooks
  const { isBreakpointReached } = useHorizontalNav()
  const theme = useTheme()

  // Refs
  const shadowRef = useRef<HTMLDivElement>(null)

  // Vars
  const ScrollWrapper = isBreakpointReached ? 'div' : PerfectScrollbar

  const scrollMenu = (container: any, isPerfectScrollbar: boolean) => {
    container = isBreakpointReached || !isPerfectScrollbar ? container.target : container

    if (shadowRef && container.scrollTop > 0) {
      // @ts-ignore
      if (!shadowRef.current.classList.contains('scrolled')) {
        // @ts-ignore
        shadowRef.current.classList.add('scrolled')
      }
    } else {
      // @ts-ignore
      shadowRef.current.classList.remove('scrolled')
    }
  }

  return (
    <>
      <NavHeader>
        <Link href='/'>
          <Logo />
        </Link>
        <NavCollapseIcons lockedIcon={MenuToggle} unlockedIcon={MenuToggle} closeIcon={MenuToggle} />
      </NavHeader>
      <div
        ref={shadowRef}
        className='absolute top-[72px] z-[2] opacity-0 pointer-events-none w-full transition-opacity duration-150 ease-in-out [&.scrolled]:opacity-100'
        style={{
          height: theme.mixins.toolbar.minHeight,
          background: `linear-gradient(var(--bg-surface) ${
            theme.direction === 'rtl' ? '95%' : '5%'
          }, color-mix(in srgb, var(--bg-app) 85%, transparent) 30%, color-mix(in srgb, var(--bg-app) 50%, transparent) 65%, color-mix(in srgb, var(--bg-app) 30%, transparent) 75%, transparent)`,
        }}
      />
      <ScrollWrapper
        {...(isBreakpointReached
          ? {
              className: 'bs-full overflow-y-auto overflow-x-hidden',
              onScroll: container => scrollMenu(container, false)
            }
          : {
              options: { wheelPropagation: false, suppressScrollX: true },
              onScrollY: container => scrollMenu(container, true)
            })}
      >
        {mapHorizontalToVerticalMenu(children)}
      </ScrollWrapper>
    </>
  )
}

export default VerticalNavContent
