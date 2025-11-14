# 📋 Règles de Développement - SaaS-IA

## 🎨 Frontend : Template Sneat MUI v3.0.0

### Règle Absolue

Ce projet utilise la **template premium Sneat MUI Next.js Admin v3.0.0** payée plusieurs centaines d'euros.

**Localisation** : `C:\Users\ibzpc\Git\SaaS-IA\sneat-mui-nextjs-admin-template-v3.0.0` (source originale)

### Commandements du Développement Frontend

1. **Tu NE CRÉERAS PAS** de composants UI from scratch si Sneat les a
2. **Tu RÉUTILISERAS** les composants Material-UI de la template
3. **Tu ADAPTERAS** les pages existantes au lieu de les recréer
4. **Tu EXPLORERAS** la template avant de coder
5. **Tu DEMANDERAS** avant de créer un nouveau composant
6. **Tu EXPLOITERAS** cette ressource premium au maximum
7. **Tu NE RÉINVENTERAS PAS** ce qui existe déjà
8. **Tu RESPECTERAS** le theme et la structure Sneat
9. **Tu DOCUMENTERAS** les adaptations effectuées
10. **Tu PARTAGERAS** les bonnes pratiques avec l'équipe

### Workflow de Développement Frontend

```
1. 💡 Besoin d'un composant
   ↓
2. 🔍 Chercher dans Sneat (`C:\Users\ibzpc\Git\SaaS-IA\sneat-mui-nextjs-admin-template-v3.0.0`)
   ↓
3. ✅ Trouvé ? → RÉUTILISER
   ↓
4. ❌ Pas trouvé ? → Chercher dans Material-UI
   ↓
5. ✅ Trouvé ? → UTILISER Material-UI
   ↓
6. ❌ Vraiment pas trouvé ? → DEMANDER validation
   ↓
7. ✅ Validé ? → Créer en respectant le style Sneat
```

### Exemples de Réutilisation

#### Page Login

```typescript
// ❌ MAUVAIS : Créer from scratch
export default function LoginPage() {
  return <div className="login-container">...</div>
}

// ✅ BON : Adapter la page Sneat existante
import LoginForm from '@/views/pages/auth/LoginForm' // Sneat component
export default function LoginPage() {
  return <LoginForm apiEndpoint="http://localhost:8004/api/auth/login" />
}
```

#### Formulaire

```typescript
// ❌ MAUVAIS : Créer un custom input
export default function CustomInput() {
  return <input className="my-custom-input" />
}

// ✅ BON : Utiliser TextField Material-UI de Sneat
import { TextField } from '@mui/material'
export default function Form() {
  return <TextField label="Email" variant="outlined" />
}
```

#### Layout Admin

```typescript
// ❌ MAUVAIS : Créer un layout custom
export default function MyLayout({ children }) {
  return (
    <div>
      <MySidebar />
      <MyHeader />
      {children}
    </div>
  )
}

// ✅ BON : Utiliser AdminLayout de Sneat
import AdminLayout from '@/layouts/AdminLayout'
export default function DashboardPage() {
  return <AdminLayout>{/* contenu */}</AdminLayout>
}
```

### Checklist Avant Chaque Développement Frontend

- [ ] Ai-je exploré `C:\Users\ibzpc\Git\SaaS-IA\sneat-mui-nextjs-admin-template-v3.0.0\documentation.html` pour ce besoin ?
- [ ] Existe-t-il un composant Sneat similaire ?
- [ ] Existe-t-il un composant Material-UI adapté ?
- [ ] Ai-je demandé validation si je dois créer du custom ?
- [ ] Mon code respecte-t-il le style/theme Sneat ?

### Ressources

- **Template Source** : `C:\Users\ibzpc\Git\SaaS-IA\sneat-mui-nextjs-admin-template-v3.0.0`
- **Documentation Sneat** : Voir `sneat-mui-nextjs-admin-template-v3.0.0/documentation.html`
- **Material-UI Docs** : https://mui.com/material-ui/getting-started/

---

**Cette documentation est à lire OBLIGATOIREMENT avant tout développement frontend.**

**Date de création** : 2025-11-13
**Maintenu par** : @benziane

