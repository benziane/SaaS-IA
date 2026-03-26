'use client'

// React Imports
import { useEffect, useRef } from 'react'
import type { CSSProperties } from 'react'

// Component Imports
import SneatLogo from '@core/svg/Logo'

// Config Imports
import themeConfig from '@configs/themeConfig'

// Hook Imports
import useVerticalNav from '@menu/hooks/useVerticalNav'
import { useSettings } from '@core/hooks/useSettings'

const Logo = ({ color }: { color?: CSSProperties['color'] }) => {
  // Refs
  const logoTextRef = useRef<HTMLSpanElement>(null)

  // Hooks
  const { isHovered, transitionDuration, isBreakpointReached } = useVerticalNav()
  const { settings } = useSettings()

  // Vars
  const { layout } = settings

  const isCollapsed = layout === 'collapsed'
  const isHidden = !isBreakpointReached && isCollapsed && !isHovered

  useEffect(() => {
    if (layout !== 'collapsed') {
      return
    }

    if (logoTextRef && logoTextRef.current) {
      if (!isBreakpointReached && layout === 'collapsed' && !isHovered) {
        logoTextRef.current?.classList.add('hidden')
      } else {
        logoTextRef.current.classList.remove('hidden')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isHovered, layout, isBreakpointReached])

  return (
    <div className='flex items-center'>
      <SneatLogo className='text-2xl text-primary' />
      <span
        ref={logoTextRef}
        className='text-[1.75rem] leading-none font-bold tracking-[0.15px]'
        style={{
          color: color ?? 'var(--mui-palette-text-primary)',
          transition: `margin-inline-start ${transitionDuration}ms ease-in-out, opacity ${transitionDuration}ms ease-in-out`,
          opacity: isHidden ? 0 : 1,
          marginInlineStart: isHidden ? 0 : 8,
        }}
      >
        {themeConfig.templateName}
      </span>
    </div>
  )
}

export default Logo
