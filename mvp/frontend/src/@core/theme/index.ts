// MUI Imports
import type { Theme } from '@mui/material/styles'

// Type Imports
import type { Settings } from '@core/contexts/settingsContext'
import type { Skin, SystemMode } from '@core/types'

// Theme Options Imports
import overrides from './overrides'
import colorSchemes from './colorSchemes'
import spacing from './spacing'
import shadows from './shadows'
import customShadows from './customShadows'
import typography from './typography'

// Inter is loaded via next/font/google in app/layout.tsx as --font-inter CSS var
// globals.css maps: --font-sans → var(--font-inter, "Inter")
const FONT_SANS = '"Inter Variable", "Inter", system-ui, -apple-system, sans-serif'

const theme = (settings: Settings, mode: SystemMode, direction: Theme['direction']): Theme => {
  return {
    direction,
    components: overrides(settings.skin as Skin),
    colorSchemes: colorSchemes(settings.skin as Skin),
    ...spacing,
    shape: {
      borderRadius: 6,
      customBorderRadius: {
        xs: 2,
        sm: 4,
        md: 6,
        lg: 8,
        xl: 10
      }
    },
    shadows: shadows(mode),
    typography: typography(FONT_SANS),
    customShadows: customShadows(mode),
    mainColorChannels: {
      light: '34 48 62',
      dark: '200 220 240',
      lightShadow: '34 48 62',
      darkShadow: '4 7 19'
    }
  } as Theme
}

export default theme
