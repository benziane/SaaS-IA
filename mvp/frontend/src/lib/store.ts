/**
 * Zustand Store
 * Global UI state management
 *
 * NOTE: Authentication state is managed exclusively by AuthContext.
 * Do not add auth-related state here. Use useAuth() from '@/contexts/AuthContext'.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

/* ========================================================================
   TYPES
   ======================================================================== */

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
}

interface UIActions {
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
}

export type UIStore = UIState & UIActions;

/* ========================================================================
   UI STORE
   ======================================================================== */

export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set) => ({
        /* State */
        sidebarOpen: true,
        theme: 'light',

        /* Actions */
        toggleSidebar: () =>
          set(
            (state) => ({
              ...state,
              sidebarOpen: !state.sidebarOpen,
            }),
            false,
            'ui/toggleSidebar'
          ),

        setSidebarOpen: (open) =>
          set(
            (state) => ({
              ...state,
              sidebarOpen: open,
            }),
            false,
            'ui/setSidebarOpen'
          ),

        setTheme: (theme) =>
          set(
            (state) => ({
              ...state,
              theme,
            }),
            false,
            'ui/setTheme'
          ),

        toggleTheme: () =>
          set(
            (state) => ({
              ...state,
              theme: state.theme === 'light' ? 'dark' : 'light',
            }),
            false,
            'ui/toggleTheme'
          ),
      }),
      {
        name: 'ui-storage',
      }
    ),
    {
      name: 'UIStore',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
);

/* ========================================================================
   SELECTORS (Optimized)
   ======================================================================== */

export const selectSidebarOpen = (state: UIStore): boolean => state.sidebarOpen;
export const selectTheme = (state: UIStore): 'light' | 'dark' => state.theme;

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useUIStore,
};
