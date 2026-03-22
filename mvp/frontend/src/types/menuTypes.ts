/**
 * Menu Types - SaaS-IA MVP
 *
 * Type definitions for vertical and horizontal menu data configuration.
 */

import type { ReactNode } from 'react'
import type { ChipProps } from '@mui/material/Chip'

/* ========================================================================
   VERTICAL MENU DATA TYPES
   ======================================================================== */

export interface VerticalMenuItemDataType {
  label: ReactNode
  href?: string
  icon?: string
  prefix?: ReactNode | ChipProps
  suffix?: ReactNode | ChipProps
  disabled?: boolean
  target?: string
}

export interface VerticalSubMenuDataType {
  label: ReactNode
  href?: string
  icon?: string
  prefix?: ReactNode | ChipProps
  suffix?: ReactNode | ChipProps
  disabled?: boolean
  target?: string
  children?: VerticalMenuDataType[]
}

export interface VerticalSectionDataType {
  label: ReactNode
  isSection: true
  icon?: string
  prefix?: ReactNode | ChipProps
  suffix?: ReactNode | ChipProps
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
  prefix?: ReactNode | ChipProps
  suffix?: ReactNode | ChipProps
  disabled?: boolean
  target?: string
}

export interface HorizontalSubMenuDataType {
  label: ReactNode
  href?: string
  icon?: string
  prefix?: ReactNode | ChipProps
  suffix?: ReactNode | ChipProps
  disabled?: boolean
  target?: string
  children?: HorizontalMenuDataType[]
}

export type HorizontalMenuDataType = HorizontalMenuItemDataType | HorizontalSubMenuDataType
