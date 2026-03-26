/**
 * Menu Types - SaaS-IA MVP
 *
 * Type definitions for vertical and horizontal menu data configuration.
 */

import type { ReactNode } from 'react'

/**
 * Local replacement for MUI ChipProps — only the properties actually used
 * by menu prefix/suffix rendering (label, color, size, variant).
 */
export interface MenuChipProps {
  label: ReactNode
  color?: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'
  size?: 'small' | 'medium'
  variant?: 'filled' | 'outlined'
}

/* ========================================================================
   VERTICAL MENU DATA TYPES
   ======================================================================== */

export interface VerticalMenuItemDataType {
  label: ReactNode
  href?: string
  icon?: string
  prefix?: ReactNode | MenuChipProps
  suffix?: ReactNode | MenuChipProps
  disabled?: boolean
  target?: string
}

export interface VerticalSubMenuDataType {
  label: ReactNode
  href?: string
  icon?: string
  prefix?: ReactNode | MenuChipProps
  suffix?: ReactNode | MenuChipProps
  disabled?: boolean
  target?: string
  children?: VerticalMenuDataType[]
}

export interface VerticalSectionDataType {
  label: ReactNode
  isSection: true
  icon?: string
  prefix?: ReactNode | MenuChipProps
  suffix?: ReactNode | MenuChipProps
  children?: VerticalMenuDataType[]
}

export type VerticalMenuDataType = VerticalMenuItemDataType | VerticalSubMenuDataType | VerticalSectionDataType

/* ========================================================================
   HORIZONTAL MENU DATA TYPES
   ======================================================================== */

export interface HorizontalMenuItemDataType {
  label: ReactNode
  href?: string
  icon?: string
  prefix?: ReactNode | MenuChipProps
  suffix?: ReactNode | MenuChipProps
  disabled?: boolean
  target?: string
}

export interface HorizontalSubMenuDataType {
  label: ReactNode
  href?: string
  icon?: string
  prefix?: ReactNode | MenuChipProps
  suffix?: ReactNode | MenuChipProps
  disabled?: boolean
  target?: string
  children?: HorizontalMenuDataType[]
}

export type HorizontalMenuDataType = HorizontalMenuItemDataType | HorizontalSubMenuDataType
