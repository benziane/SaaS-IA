'use client'

// React Imports
import { useEffect, useRef } from 'react'

// Next Imports
import Link from 'next/link'

// MUI Imports — required by Sneat navigationCustomStyles which uses theme.spacing/transitions
import { useColorScheme, useTheme } from '@mui/material/styles'

// Lucide Imports
import { ChevronLeft } from 'lucide-react'

// Type Imports
import type { Mode } from '@core/types'

// Component Imports
import VerticalNav, { NavHeader, NavCollapseIcons } from '@menu/vertical-menu'
import VerticalMenu from './VerticalMenu'
import Logo from '@components/layout/shared/Logo'

// Hook Imports
import useVerticalNav from '@menu/hooks/useVerticalNav'
import { useSettings } from '@core/hooks/useSettings'

// Style Imports
import navigationCustomStyles from '@core/styles/vertical/navigationCustomStyles'

type Props = {
  mode?: Mode
}

const MenuToggle = (
  <div className='icon-wrapper flex items-center justify-center'>
    <ChevronLeft className='h-4 w-4 text-[var(--text-mid)]' />
  </div>
)

const Navigation = (props: Props) => {
  // Props
  const { mode } = props

  // Hooks — useTheme/useColorScheme required by Sneat style functions
  const verticalNavOptions = useVerticalNav()
  const { updateSettings, settings } = useSettings()
  const { mode: muiMode, systemMode: muiSystemMode } = useColorScheme()
  const theme = useTheme()

  // Refs
  const shadowRef = useRef<HTMLDivElement>(null)

  // Vars
  const { isCollapsed, isHovered, collapseVerticalNav, isBreakpointReached } = verticalNavOptions
  const isSemiDark = settings.semiDark

  const currentMode = muiMode === 'system' ? muiSystemMode : muiMode || mode

  const isDark = currentMode === 'dark'

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

  useEffect(() => {
    if (settings.layout === 'collapsed') {
      collapseVerticalNav(true)
    } else {
      collapseVerticalNav(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.layout])

  return (
    <VerticalNav
      customStyles={navigationCustomStyles(verticalNavOptions, theme, settings)}
      collapsedWidth={72}
      backgroundColor='var(--bg-surface)'
      {...(isSemiDark &&
        !isDark && {
          'data-dark': ''
        })}
    >
      {/* Nav Header — Logo & collapse toggle */}
      <NavHeader>
        <Link href='/'>
          <Logo />
        </Link>
        {!(isCollapsed && !isHovered) && (
          <NavCollapseIcons
            lockedIcon={MenuToggle}
            unlockedIcon={MenuToggle}
            closeIcon={MenuToggle}
            onClick={() => updateSettings({ layout: !isCollapsed ? 'collapsed' : 'vertical' })}
          />
        )}
      </NavHeader>
      {/* Scroll shadow indicator */}
      <div
        ref={shadowRef}
        className='absolute top-[72px] z-[2] opacity-0 pointer-events-none w-full transition-opacity duration-150 ease-in-out [&.scrolled]:opacity-100'
        style={{
          height: theme.mixins.toolbar.minHeight,
          background: 'linear-gradient(var(--bg-surface) 5%, rgba(15,22,41,0.85) 30%, rgba(15,22,41,0.5) 65%, rgba(15,22,41,0.3) 75%, transparent)',
        }}
      />
      <VerticalMenu scrollMenu={scrollMenu} />
    </VerticalNav>
  )
}

export default Navigation
