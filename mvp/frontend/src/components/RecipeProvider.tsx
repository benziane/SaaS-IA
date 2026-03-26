'use client'

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

type RecipeId = 'saas-ia' | 'cockpit-ui' | 'automation-tool'

interface RecipeContextValue {
  activeRecipe: RecipeId
  setRecipe: (id: RecipeId) => void
  mode: 'dark' | 'light'
  setMode: (mode: 'dark' | 'light') => void
}

const RecipeContext = createContext<RecipeContextValue>({
  activeRecipe: 'saas-ia',
  setRecipe: () => {},
  mode: 'dark',
  setMode: () => {},
})

export const useRecipe = () => useContext(RecipeContext)

// Map pages to their recipe
const PAGE_RECIPE_MAP: Record<string, RecipeId> = {
  '/monitoring': 'cockpit-ui',
  '/costs': 'cockpit-ui',
  '/data': 'cockpit-ui',
  '/security': 'automation-tool',
  '/audit': 'automation-tool',
  '/feature-flags': 'automation-tool',
  '/secrets': 'automation-tool',
}

export function RecipeProvider({ children }: { children: ReactNode }) {
  const [activeRecipe, setActiveRecipe] = useState<RecipeId>('saas-ia')
  const [mode, setMode] = useState<'dark' | 'light'>('dark')

  useEffect(() => {
    const html = document.documentElement
    // Only set data-recipe for alternate recipes (saas-ia tokens are in :root)
    if (activeRecipe !== 'saas-ia') {
      html.setAttribute('data-recipe', activeRecipe)
    } else {
      html.removeAttribute('data-recipe')
    }
    html.setAttribute('data-mode', mode)
  }, [activeRecipe, mode])

  useEffect(() => {
    // Auto-detect recipe from current path
    const path = window.location.pathname.replace(/^\/?(dashboard\/)?/, '/')
    const matchedRecipe = Object.entries(PAGE_RECIPE_MAP).find(
      ([route]) => path.startsWith(route)
    )
    if (matchedRecipe) {
      setActiveRecipe(matchedRecipe[1])
    } else {
      setActiveRecipe('saas-ia')
    }
  }, [])

  return (
    <RecipeContext.Provider value={{ activeRecipe, setRecipe: setActiveRecipe, mode, setMode }}>
      {children}
    </RecipeContext.Provider>
  )
}
