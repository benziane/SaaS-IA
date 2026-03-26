// Third-party Imports
import classnames from 'classnames'

// Component Imports
import HorizontalMenu from './HorizontalMenu'

// Config Imports
import themeConfig from '@configs/themeConfig'

// Hook Imports
import { useSettings } from '@core/hooks/useSettings'
import useHorizontalNav from '@menu/hooks/useHorizontalNav'

// Util Imports
import { horizontalLayoutClasses } from '@layouts/utils/layoutClasses'

const Navigation = () => {
  // Hooks
  const { settings } = useSettings()
  const { isBreakpointReached } = useHorizontalNav()

  // Vars
  const headerContentCompact = settings.navbarContentWidth === 'compact'

  return (
    <div
      {...(!isBreakpointReached && {
        className: classnames(horizontalLayoutClasses.navigation, 'relative flex border-bs')
      })}
    >
      <div
        className={classnames(
          !isBreakpointReached && horizontalLayoutClasses.navigationContentWrapper,
          !isBreakpointReached && 'flex items-center is-full plb-2.5'
        )}
        style={
          !isBreakpointReached
            ? {
                padding: `${themeConfig.layoutPadding}px`,
                ...(headerContentCompact && {
                  marginInline: 'auto',
                  maxInlineSize: `${themeConfig.compactContentWidth}px`,
                }),
              }
            : undefined
        }
      >
        <HorizontalMenu />
      </div>
    </div>
  )
}

export default Navigation
