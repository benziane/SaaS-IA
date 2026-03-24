---
name: saas-frontend
description: |
  Skill pour le developpement frontend Next.js/Sneat du projet SaaS-IA.
  TRIGGER quand: creation/modification de composants UI, pages dashboard,
  formulaires, ou tout code dans mvp/frontend/.
---

# Developpement Frontend Next.js / Sneat MUI

## REGLE ABSOLUE: Template Sneat MUI v3.0.0

Ce projet utilise la template premium **Sneat MUI Next.js Admin Template v3.0.0**.

### Avant de coder un composant:
1. Ce composant existe-t-il dans Sneat ? → REUTILISER
2. Material-UI (inclus dans Sneat) a ce composant ? → REUTILISER
3. Un composant existant peut etre adapte ? → ADAPTER
4. Aucune option existante → Demander confirmation avant de creer

### INTERDIT
- Creer des composants UI custom si Sneat/MUI les a
- Reinventer les layouts (sidebar, header, footer)
- Utiliser d'autres bibliotheques UI (Bootstrap, Ant Design, Chakra, etc.)
- Modifier le theme Sneat sans validation

## Structure

```
mvp/frontend/src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Pages login, register
│   └── (dashboard)/       # Pages protegees
├── features/              # Modules fonctionnels (miroir backend)
│   └── <module>/
│       ├── components/    # Composants specifiques au module
│       ├── hooks/         # Hooks du module
│       ├── types.ts       # Types TypeScript
│       └── api.ts         # Appels API (TanStack Query)
├── @core/                 # Core Sneat (NE PAS MODIFIER)
├── @layouts/              # Layouts Sneat
├── components/            # Composants reutilisables
├── hooks/                 # Hooks globaux
├── contexts/              # React contexts
└── types/                 # Types globaux
```

## Patterns obligatoires

### Appels API (TanStack Query)
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export const useItems = () => {
  return useQuery({
    queryKey: ['items'],
    queryFn: () => api.get('/api/items').then(res => res.data),
  })
}

export const useCreateItem = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateItemInput) => api.post('/api/items', data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['items'] }),
  })
}
```

### Formulaires (React Hook Form + Zod)
```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  name: z.string().min(1, 'Requis'),
  email: z.string().email('Email invalide'),
})

type FormData = z.infer<typeof schema>
```

### Etat global (Zustand)
```typescript
import { create } from 'zustand'

interface MyStore {
  items: Item[]
  setItems: (items: Item[]) => void
}

export const useMyStore = create<MyStore>((set) => ({
  items: [],
  setItems: (items) => set({ items }),
}))
```

## Regles

1. **TypeScript strict** - pas de `any`, typer toutes les props et retours
2. **Composants fonctionnels** uniquement + Hooks
3. **MUI imports** depuis `@mui/material`
4. **Responsive**: tous les composants doivent etre responsive
5. **Accessibilite**: aria-labels sur les elements interactifs
6. **Pas de CSS custom** si MUI sx/styled peut le faire
