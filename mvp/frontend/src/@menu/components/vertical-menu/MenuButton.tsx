// React Imports
import { cloneElement, createElement, forwardRef } from 'react'
import type { ForwardRefRenderFunction } from 'react'

// Third-party Imports
import classnames from 'classnames'
import { css } from '@emotion/react'

// Type Imports
import type { ChildrenType, MenuButtonProps } from '../../types'

// Component Imports
import { RouterLink } from '../RouterLink'

// Util Imports
import { menuClasses } from '../../utils/menuClasses'

type MenuButtonStylesProps = Partial<ChildrenType> & {
  level: number
  active?: boolean
  disabled?: boolean
  isCollapsed?: boolean
  isPopoutWhenCollapsed?: boolean
}

export const menuButtonStyles = (props: MenuButtonStylesProps) => {
  // Props
  const { level, disabled, children, isCollapsed, isPopoutWhenCollapsed } = props

  return css({
    display: 'flex',
    alignItems: 'center',
    minBlockSize: '30px',
    textDecoration: 'none',
    color: 'inherit',
    boxSizing: 'border-box',
    cursor: 'pointer',
    paddingInlineEnd: '20px',
    paddingInlineStart: `${level === 0 ? 20 : (isPopoutWhenCollapsed && isCollapsed ? level : level + 1) * 20}px`,

    '&:hover, &[aria-expanded="true"]': {
      backgroundColor: 'var(--bg-elevated)'
    },

    '&:focus-visible': {
      outline: 'none',
      backgroundColor: 'var(--bg-elevated)'
    },

    ...(disabled && {
      pointerEvents: 'none',
      cursor: 'default',
      color: 'var(--text-low)'
    }),

    // All the active styles are applied to the button including menu items or submenu
    [`&.${menuClasses.active}`]: {
      ...(!children && { color: 'var(--bg-app)' }),
      backgroundColor: children ? 'var(--bg-elevated)' : 'var(--accent)'
    }
  })
}

const MenuButton: ForwardRefRenderFunction<HTMLAnchorElement, MenuButtonProps> = (
  { className, component, children, ...rest },
  ref
) => {
  if (component) {
    // If component is a string, create a new element of that type
    if (typeof component === 'string') {
      return createElement(
        component,
        {
          className: classnames(className),
          ...rest,
          ref
        },
        children
      )
    } else {
      // Otherwise, clone the element
      const componentProps = component.props as { className?: string } & Record<string, unknown>
      const { className: classNameProp, ...props } = componentProps

      return cloneElement(
        component as any,
        ({
          className: classnames(className, classNameProp),
          ...rest,
          ...props
        } as any),
        children
      )
    }
  } else {
    // If there is no component but href is defined, render RouterLink
    if (rest.href) {
      return (
        <RouterLink ref={ref} className={className} href={rest.href} {...rest}>
          {children}
        </RouterLink>
      )
    } else {
      return (
        <a ref={ref} className={className} {...rest}>
          {children}
        </a>
      )
    }
  }
}

export default forwardRef(MenuButton)
