'use client'

// React Imports
import { useState } from 'react'

// Lucide Imports
import { Sun, Moon, Monitor } from 'lucide-react'

// Type Imports
import type { Mode } from '@core/types'

// Design Hub Imports
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/lib/design-hub/components/DropdownMenu'

// Hook Imports
import { useSettings } from '@core/hooks/useSettings'

const ModeDropdown = () => {
  // States
  const [tooltipOpen, setTooltipOpen] = useState(false)

  // Hooks
  const { settings, updateSettings } = useSettings()

  const handleModeSwitch = (mode: Mode) => {
    if (settings.mode !== mode) {
      updateSettings({ mode: mode })
    }
  }

  const getModeIcon = () => {
    if (settings.mode === 'system') {
      return <Monitor className='h-5 w-5' />
    } else if (settings.mode === 'dark') {
      return <Moon className='h-5 w-5' />
    } else {
      return <Sun className='h-5 w-5' />
    }
  }

  return (
    <DropdownMenu onOpenChange={(open) => { if (open) setTooltipOpen(false) }}>
      <TooltipProvider>
        <Tooltip open={tooltipOpen} onOpenChange={setTooltipOpen}>
          <TooltipTrigger asChild>
            <DropdownMenuTrigger asChild>
              <button className='inline-flex items-center justify-center rounded-full p-2 text-[var(--text-high)] hover:bg-[var(--bg-elevated)] transition-colors capitalize'>
                {getModeIcon()}
              </button>
            </DropdownMenuTrigger>
          </TooltipTrigger>
          <TooltipContent>
            <span className='capitalize'>{settings.mode} Mode</span>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <DropdownMenuContent align='start' className='min-w-[160px]'>
        <DropdownMenuItem
          className='gap-3'
          onClick={() => handleModeSwitch('light')}
        >
          <Sun className='h-4 w-4' />
          Light
        </DropdownMenuItem>
        <DropdownMenuItem
          className='gap-3'
          onClick={() => handleModeSwitch('dark')}
        >
          <Moon className='h-4 w-4' />
          Dark
        </DropdownMenuItem>
        <DropdownMenuItem
          className='gap-3'
          onClick={() => handleModeSwitch('system')}
        >
          <Monitor className='h-4 w-4' />
          System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default ModeDropdown
