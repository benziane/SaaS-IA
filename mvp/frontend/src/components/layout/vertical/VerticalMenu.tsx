// MUI Imports
import { useTheme } from '@mui/material/styles'

// Third-party Imports
import PerfectScrollbar from 'react-perfect-scrollbar'

// Type Imports
import type { VerticalMenuContextProps } from '@menu/components/vertical-menu/Menu'
import type { VerticalMenuDataType, VerticalMenuItemDataType } from '@/types/menuTypes'

// Component Imports
import { Menu, MenuItem, MenuSection, SubMenu } from '@menu/vertical-menu'

// Data Imports
import verticalMenuData from '@/data/navigation/verticalMenuData'

// Hook Imports
import useVerticalNav from '@menu/hooks/useVerticalNav'

// Styled Component Imports
import StyledVerticalNavExpandIcon from '@menu/styles/vertical/StyledVerticalNavExpandIcon'

// Style Imports
import menuItemStyles from '@core/styles/vertical/menuItemStyles'
import menuSectionStyles from '@core/styles/vertical/menuSectionStyles'

type RenderExpandIconProps = {
  open?: boolean
  transitionDuration?: VerticalMenuContextProps['transitionDuration']
}

type Props = {
  scrollMenu: (container: any, isPerfectScrollbar: boolean) => void
}

const RenderExpandIcon = ({ open, transitionDuration }: RenderExpandIconProps) => (
  <StyledVerticalNavExpandIcon open={open} transitionDuration={transitionDuration}>
    <i className='tabler-chevron-right' />
  </StyledVerticalNavExpandIcon>
)

/**
 * Convert icon string (e.g. 'tabler:smart-home') to a React element
 */
const renderIcon = (iconStr?: string) => {
  if (!iconStr) return undefined

  // Convert 'tabler:smart-home' to 'tabler-smart-home'
  const className = iconStr.replace(':', '-')

  return <i className={className} />
}

/**
 * Recursively render menu items from navigation data
 */
const renderMenuItems = (items: VerticalMenuDataType[]) => {
  return items.map((item, index) => {
    // Section header
    if ('isSection' in item && item.isSection) {
      return (
        <MenuSection key={`section-${index}`} label={item.label}>
          {item.children ? renderMenuItems(item.children) : null}
        </MenuSection>
      )
    }

    // SubMenu (has children)
    if ('children' in item && item.children) {
      return (
        <SubMenu key={`submenu-${index}`} label={item.label} icon={renderIcon(item.icon)}>
          {renderMenuItems(item.children)}
        </SubMenu>
      )
    }

    // Regular menu item
    const menuItem = item as VerticalMenuItemDataType
    return (
      <MenuItem
        key={`item-${index}`}
        href={menuItem.href}
        icon={renderIcon(menuItem.icon)}
        target={menuItem.target}
        disabled={menuItem.disabled}
      >
        {menuItem.label}
      </MenuItem>
    )
  })
}

const VerticalMenu = ({ scrollMenu }: Props) => {
  // Hooks
  const theme = useTheme()
  const verticalNavOptions = useVerticalNav()

  // Vars
  const { transitionDuration, isBreakpointReached } = verticalNavOptions
  const menuData = verticalMenuData()

  const ScrollWrapper = isBreakpointReached ? 'div' : PerfectScrollbar

  return (
    // eslint-disable-next-line lines-around-comment
    /* Custom scrollbar instead of browser scroll, remove if you want browser scroll only */
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
      {/* Vertical Menu */}
      <Menu
        popoutMenuOffset={{ mainAxis: 27 }}
        menuItemStyles={menuItemStyles(verticalNavOptions, theme)}
        renderExpandIcon={({ open }) => <RenderExpandIcon open={open} transitionDuration={transitionDuration} />}
        renderExpandedMenuItemIcon={{ icon: <i className='tabler-circle-filled' style={{ fontSize: 6 }} /> }}
        menuSectionStyles={menuSectionStyles(verticalNavOptions, theme)}
      >
        {renderMenuItems(menuData)}
      </Menu>
    </ScrollWrapper>
  )
}

export default VerticalMenu
