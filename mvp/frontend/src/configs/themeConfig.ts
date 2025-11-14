/**
 * Theme Configuration - Grade S++
 * Adapted from Sneat MUI Template
 */

import type { Mode, Skin, Layout, LayoutComponentPosition, LayoutComponentWidth } from '@core/types';

/* ========================================================================
   TYPES
   ======================================================================== */

interface Navbar {
  type: LayoutComponentPosition;
  contentWidth: LayoutComponentWidth;
  floating: boolean;
  detached: boolean;
  blur: boolean;
}

interface Footer {
  type: LayoutComponentPosition;
  contentWidth: LayoutComponentWidth;
  detached: boolean;
}

export interface Config {
  templateName: string;
  homePageUrl: string;
  settingsCookieName: string;
  mode: Mode;
  skin: Skin;
  semiDark: boolean;
  layout: Layout;
  layoutPadding: number;
  navbar: Navbar;
  contentWidth: LayoutComponentWidth;
  compactContentWidth: number;
  footer: Footer;
  disableRipple: boolean;
}

/* ========================================================================
   CONFIGURATION
   ======================================================================== */

const themeConfig: Config = {
  /* App Info */
  templateName: 'SaaS-IA',
  homePageUrl: '/dashboard',
  settingsCookieName: 'saas-ia-settings',
  
  /* Theme */
  mode: 'system', // 'system', 'light', 'dark'
  skin: 'default', // 'default', 'bordered'
  semiDark: false,
  
  /* Layout */
  layout: 'vertical', // 'vertical', 'collapsed', 'horizontal'
  layoutPadding: 24,
  compactContentWidth: 1440,
  contentWidth: 'compact', // 'compact', 'wide'
  
  /* Navbar */
  navbar: {
    type: 'fixed',
    contentWidth: 'compact',
    floating: true,
    detached: true,
    blur: true,
  },
  
  /* Footer */
  footer: {
    type: 'static',
    contentWidth: 'compact',
    detached: true,
  },
  
  /* Material-UI */
  disableRipple: true,
};

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default themeConfig;

