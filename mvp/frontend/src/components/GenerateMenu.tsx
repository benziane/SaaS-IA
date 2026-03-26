// React Imports
import type { ReactNode } from 'react'

// Type Imports
import type {
  MenuChipProps,
  VerticalMenuDataType,
  VerticalSectionDataType,
  VerticalSubMenuDataType,
  VerticalMenuItemDataType,
  HorizontalMenuDataType,
  HorizontalSubMenuDataType,
  HorizontalMenuItemDataType,
} from '@/types/menuTypes'

// Component Imports
import { SubMenu as HorizontalSubMenu, MenuItem as HorizontalMenuItem } from '@menu/horizontal-menu'
import { SubMenu as VerticalSubMenu, MenuItem as VerticalMenuItem, MenuSection } from '@menu/vertical-menu'

// Design Hub Imports
import { Badge } from '@/lib/design-hub/components/Badge'

/**
 * Render a chip-like badge for prefix/suffix if it has a label property,
 * otherwise render it as-is (ReactNode).
 */
const renderChipOrNode = (value: ReactNode | MenuChipProps | undefined): ReactNode => {
  if (!value) return undefined
  if ((value as MenuChipProps).label) {
    const chipProps = value as MenuChipProps
    return (
      <Badge variant='secondary' className='rounded-full text-xs px-2 py-0.5'>
        {chipProps.label}
      </Badge>
    )
  }
  return value as ReactNode
}

// Generate a menu from the menu data array
export const GenerateVerticalMenu = ({ menuData }: { menuData: VerticalMenuDataType[] }) => {
  // Hooks

  const renderMenuItems = (data: VerticalMenuDataType[]) => {
    // Use the map method to iterate through the array of menu data
    return data.map((item: VerticalMenuDataType, index) => {
      const menuSectionItem = item as VerticalSectionDataType
      const subMenuItem = item as VerticalSubMenuDataType
      const menuItem = item as VerticalMenuItemDataType

      // Check if the current item is a section
      if (menuSectionItem.isSection) {
        const { children, label, icon, prefix, suffix } = menuSectionItem

        const Icon = icon ? <i className={icon} /> : undefined

        // If it is, return a MenuSection component and call generateMenu with the current menuSectionItem's children
        return (
          <MenuSection
            key={index}
            label={label}
            prefix={renderChipOrNode(prefix)}
            suffix={renderChipOrNode(suffix)}
            {...(Icon && { icon: Icon })}
          >
            {children && renderMenuItems(children)}
          </MenuSection>
        )
      }

      // Check if the current item is a sub menu
      if (subMenuItem.children) {
        const { children, icon, prefix, suffix, ...rest } = subMenuItem

        const Icon = icon ? <i className={icon} /> : null

        // If it is, return a SubMenu component and call generateMenu with the current subMenuItem's children
        return (
          <VerticalSubMenu
            key={index}
            prefix={renderChipOrNode(prefix)}
            suffix={renderChipOrNode(suffix)}
            {...rest}
            {...(Icon && { icon: Icon })}
          >
            {children && renderMenuItems(children)}
          </VerticalSubMenu>
        )
      }

      // If the current item is neither a section nor a sub menu, return a MenuItem component
      const { label, icon, prefix, suffix, href, disabled, target } = menuItem

      const Icon = icon ? <i className={icon} /> : null

      return (
        <VerticalMenuItem
          key={index}
          prefix={renderChipOrNode(prefix)}
          suffix={renderChipOrNode(suffix)}
          href={href}
          disabled={disabled}
          target={target}
          {...(Icon && { icon: Icon })}
        >
          {label}
        </VerticalMenuItem>
      )
    })
  }

  return <>{renderMenuItems(menuData)}</>
}

// Generate a menu from the menu data array
export const GenerateHorizontalMenu = ({ menuData }: { menuData: HorizontalMenuDataType[] }) => {
  // Hooks

  const renderMenuItems = (data: HorizontalMenuDataType[]) => {
    // Use the map method to iterate through the array of menu data
    return data.map((item: HorizontalMenuDataType, index) => {
      const subMenuItem = item as HorizontalSubMenuDataType
      const menuItem = item as HorizontalMenuItemDataType

      // Check if the current item is a sub menu
      if (subMenuItem.children) {
        const { children, icon, prefix, suffix, ...rest } = subMenuItem

        const Icon = icon ? <i className={icon} /> : null

        // If it is, return a SubMenu component and call generateMenu with the current subMenuItem's children
        return (
          <HorizontalSubMenu
            key={index}
            prefix={renderChipOrNode(prefix)}
            suffix={renderChipOrNode(suffix)}
            {...rest}
            {...(Icon && { icon: Icon })}
          >
            {children && renderMenuItems(children)}
          </HorizontalSubMenu>
        )
      }

      // If the current item is not a sub menu, return a MenuItem component
      const { label, icon, prefix, suffix, href, disabled, target } = menuItem

      const Icon = icon ? <i className={icon} /> : null

      return (
        <HorizontalMenuItem
          key={index}
          prefix={renderChipOrNode(prefix)}
          suffix={renderChipOrNode(suffix)}
          href={href}
          disabled={disabled}
          target={target}
          {...(Icon && { icon: Icon })}
        >
          {label}
        </HorizontalMenuItem>
      )
    })
  }

  return <>{renderMenuItems(menuData)}</>
}
