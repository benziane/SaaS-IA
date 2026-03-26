'use client'

// React Imports
import { useEffect, useRef } from 'react'

// Next Imports
import Link from 'next/link'

// MUI Imports — required by Sneat navigationCustomStyles which uses theme.spacing/transitions
import { useColorScheme, useTheme } from '@mui/material/styles'

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
  <div className='icon-wrapper'>
    <i className='bx-bxs-chevron-left' />
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
    // eslint-disable-next-line lines-around-comment
    // Sidebar Vertical Menu
    <VerticalNav
      customStyles={navigationCustomStyles(verticalNavOptions, theme, settings)}
      collapsedWidth={85}
      backgroundColor='var(--mui-palette-background-paper)'
      // eslint-disable-next-line lines-around-comment
      // The following condition adds the data-dark attribute to the VerticalNav component
      // when semiDark is enabled and the mode or systemMode is light
      {...(isSemiDark &&
        !isDark && {
          'data-dark': ''
        })}
    >
      {/* Nav Header including Logo & nav toggle icons  */}
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
      <div
        ref={shadowRef}
        className='absolute top-[72px] z-[2] opacity-0 pointer-events-none w-full transition-opacity duration-150 ease-in-out [&.scrolled]:opacity-100'
        style={{
          height: theme.mixins.toolbar.minHeight,
          background: `linear-gradient(var(--mui-palette-background-paper) ${
            theme.direction === 'rtl' ? '95%' : '5%'
          }, rgb(var(--mui-palette-background-paperChannel) / 0.85) 30%, rgb(var(--mui-palette-background-paperChannel) / 0.5) 65%, rgb(var(--mui-palette-background-paperChannel) / 0.3) 75%, transparent)`,
        }}
      />
      <VerticalMenu scrollMenu={scrollMenu} />
    </VerticalNav>
  )
}

export default Navigation
