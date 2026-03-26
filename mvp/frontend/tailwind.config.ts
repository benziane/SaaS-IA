import type { Config } from 'tailwindcss'
import sneatPlugin from './src/@core/tailwind/plugin'

// Design-hub presets (CJS modules — require for compatibility)
const basePreset = require('./src/lib/design-hub/configs/tailwind/base-preset')
const saasIaPreset = require('./src/lib/design-hub/recipes/saas-ia/tailwind.preset')

/**
 * Unified Tailwind Configuration — Phase C.4
 *
 * Merge order (last wins on conflicts):
 *   1. design-hub base-preset   → shared keyframes, animations
 *   2. saas-ia recipe preset    → brand colors (primary/neutral via CSS vars), radius, shadows, fonts
 *   3. this config              → Sneat MUI bridge plugin + shadcn semantic colors + content paths
 *
 * The Sneat MUI bridge plugin is KEPT during migration so existing MUI-based
 * pages continue working alongside new design-hub components.
 */
const config: Config = {
  darkMode: 'class',

  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './src/@core/**/*.{js,ts,jsx,tsx}',
    './src/lib/design-hub/**/*.{js,ts,jsx,tsx}',
  ],

  presets: [
    // 1. Design-hub shared animations & keyframes
    basePreset,
    // 2. SaaS-IA recipe: brand colors, radius, shadows, timing, fonts
    saasIaPreset,
  ],

  plugins: [
    // Sneat MUI bridge — maps MUI CSS vars to Tailwind utilities
    // KEEP during migration; remove only after full MUI-to-design-hub transition
    sneatPlugin,
  ],

  theme: {
    extend: {
      // ---------------------------------------------------------------
      // shadcn-compatible semantic color names (CSS custom properties)
      // These enable shadcn/ui-style components to work alongside MUI.
      // Values are defined in globals.css (:root / [data-theme='dark']).
      //
      // Uses var() directly (not the hsl(var()/alpha) trick) so that
      // existing hex CSS vars in globals.css keep working without
      // breaking direct `var(--primary)` references in CSS/MUI.
      // For alpha support, use Tailwind's bg-opacity or text-opacity.
      // ---------------------------------------------------------------
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--card-foreground)',
        },
        popover: {
          DEFAULT: 'var(--popover)',
          foreground: 'var(--popover-foreground)',
        },
        // Note: "primary" scale (50-950) comes from saas-ia preset via
        // --color-primary-{50..950} CSS vars. This adds the shadcn
        // DEFAULT/foreground semantic pair for bg-primary, text-primary, etc.
        primary: {
          DEFAULT: 'var(--primary)',
          foreground: 'var(--primary-foreground)',
        },
        secondary: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--secondary-foreground)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-foreground)',
        },
        destructive: {
          DEFAULT: 'var(--destructive)',
          foreground: 'var(--destructive-foreground)',
        },
        border: 'var(--border)',
        input: 'var(--input)',
        ring: 'var(--ring)',
        // Chart semantic colors
        chart: {
          '1': 'var(--chart-1)',
          '2': 'var(--chart-2)',
          '3': 'var(--chart-3)',
          '4': 'var(--chart-4)',
          '5': 'var(--chart-5)',
        },
        // Sidebar semantic colors
        sidebar: {
          DEFAULT: 'var(--sidebar-background)',
          foreground: 'var(--sidebar-foreground)',
          primary: 'var(--sidebar-primary)',
          'primary-foreground': 'var(--sidebar-primary-foreground)',
          accent: 'var(--sidebar-accent)',
          'accent-foreground': 'var(--sidebar-accent-foreground)',
          border: 'var(--sidebar-border)',
          ring: 'var(--sidebar-ring)',
        },
      },
      // Container center + padding default (shadcn convention)
      container: {
        center: true,
        padding: '2rem',
      },
    },
  },
}

export default config
