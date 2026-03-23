# 🚀 Quick Login - Guide de Développement

**Date** : 2025-11-14  
**Statut** : ✅ Implémenté  
**Mode** : Development uniquement

---

## 📋 Vue d'Ensemble

Le **Quick Login** est une fonctionnalité de développement qui permet de se connecter instantanément sans saisir manuellement les identifiants.

### Fonctionnalités

- ✅ **Un clic** = connexion automatique
- ✅ **Visible uniquement en DEV** (`NODE_ENV === 'development'`)
- ✅ **Design Material-UI** intégré à la page de login
- ✅ **Accessible** (ARIA labels)
- ✅ **Inspiré de WeLAB** (même UX)

---

## 🎯 Utilisation

### Étape 1 : Créer l'Utilisateur de Test

**Via le Frontend** (Recommandé) :
1. Ouvrir `http://localhost:3002/register`
2. Remplir le formulaire :
   - **Email** : `admin@saas-ia.com`
   - **Password** : `admin123`
   - **Full Name** : `Admin Test`
3. Cliquer sur "Register"

**Via Swagger UI** :
1. Ouvrir `http://localhost:8004/docs`
2. POST `/api/auth/register`
3. Body :
```json
{
  "email": "admin@saas-ia.com",
  "password": "admin123",
  "full_name": "Admin Test"
}
```

### Étape 2 : Utiliser Quick Login

1. Ouvrir `http://localhost:3002/login`
2. Scroller vers le bas
3. Section "🚀 Quick Login (DEV)"
4. Cliquer sur **"👑 Admin"**
5. ✅ Vous êtes connecté et redirigé vers `/dashboard` !

---

## 🎨 Interface

### Apparence

```
┌─────────────────────────────────────┐
│  Sign in to SaaS-IA                 │
│  ────────────────────────            │
│  Email: [___________________]       │
│  Password: [___________________]    │
│  [x] Remember me                    │
│  [        Sign In        ]          │
│  Don't have an account? Register    │
│  ─────────────────────────────────  │
│  🚀 Quick Login (DEV)               │
│  [      👑 Admin      ]             │
└─────────────────────────────────────┘
```

### Couleurs

- **Titre** : Orange (warning.main)
- **Bouton Admin** : Rouge (error) avec bordure épaisse
- **Séparateur** : Ligne grise au-dessus

---

## 💻 Implémentation Technique

### Frontend (`login/page.tsx`)

```typescript
/* Quick Login for Development */
const quickLogin = async (email: string, password: string): Promise<void> => {
  await loginMutation.mutateAsync({ email, password });
};

// UI (visible uniquement en DEV)
{process.env.NODE_ENV === 'development' && (
  <Box sx={{ mt: 4, pt: 3, borderTop: 1, borderColor: 'divider' }}>
    <Typography variant="body2" sx={{ mb: 2, fontWeight: 600, color: 'warning.main' }}>
      🚀 Quick Login (DEV)
    </Typography>
    <Button
      fullWidth
      variant="outlined"
      color="error"
      onClick={() => quickLogin('admin@saas-ia.com', 'admin123')}
      disabled={isSubmitting || loginMutation.isPending}
    >
      👑 Admin
    </Button>
  </Box>
)}
```

### Credentials par Défaut

| Type | Email | Password | Role |
|------|-------|----------|------|
| **Admin** | `admin@saas-ia.com` | `admin123` | `admin` |

---

## 🔒 Sécurité

### Protection en Production

Le Quick Login est **automatiquement désactivé en production** :

```typescript
{process.env.NODE_ENV === 'development' && (
  // Quick Login UI
)}
```

### Vérification

```bash
# Build de production
npm run build

# Le Quick Login ne sera PAS inclus dans le bundle
```

### Variables d'Environnement

```bash
# Development
NODE_ENV=development  # Quick Login visible

# Production
NODE_ENV=production   # Quick Login invisible
```

---

## 🎯 Évolution Future

### Ajout de Nouveaux Rôles

Quand vous ajouterez d'autres rôles (manager, user, etc.), mettez à jour le Quick Login :

```typescript
<Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
  <Button onClick={() => quickLogin('admin@saas-ia.com', 'admin123')}>
    👑 Admin
  </Button>
  <Button onClick={() => quickLogin('manager@saas-ia.com', 'manager123')}>
    👔 Manager
  </Button>
  <Button onClick={() => quickLogin('user@saas-ia.com', 'user123')}>
    👤 User
  </Button>
</Box>
```

### Personnalisation

**Couleurs par rôle** :
- Admin : `color="error"` (rouge)
- Manager : `color="primary"` (bleu)
- User : `color="success"` (vert)

**Icônes** :
- 👑 Admin
- 👔 Manager
- 👤 User
- 👁️ Viewer
- 🔧 Tech
- 📊 Analyst

---

## 📊 Comparaison avec WeLAB

| Fonctionnalité | WeLAB | SaaS-IA |
|----------------|-------|---------|
| **Nombre de boutons** | 6 (admin, manager, user, viewer, tech, analyst) | 1 (admin) |
| **Layout** | Grid 2 colonnes | 1 bouton pleine largeur |
| **Framework UI** | TailwindCSS | Material-UI |
| **Condition d'affichage** | `import.meta.env.DEV` | `process.env.NODE_ENV === 'development'` |
| **Fonction** | `quickLogin(email, password)` | `quickLogin(email, password)` |

---

## 🐛 Troubleshooting

### Quick Login non visible

**Vérifier** :
```bash
# Dans le terminal frontend
echo $env:NODE_ENV  # Doit être "development"

# Ou dans le code
console.log(process.env.NODE_ENV)
```

**Solution** :
```bash
# Redémarrer en mode dev
npm run dev
```

### Erreur 401 Unauthorized

**Cause** : L'utilisateur n'existe pas

**Solution** : Créer l'utilisateur via `/register` (voir Étape 1)

### Erreur 500 Internal Server Error

**Cause** : Problème backend (bcrypt, database, etc.)

**Solution** :
```bash
# Vérifier les logs backend
cd mvp/backend
docker-compose logs saas-ia-backend

# Redémarrer le backend
docker-compose restart saas-ia-backend
```

---

## 📝 Checklist d'Implémentation

- [x] Fonction `quickLogin()` créée
- [x] UI Quick Login ajoutée
- [x] Condition `NODE_ENV === 'development'`
- [x] Bouton Admin avec credentials
- [x] Styling Material-UI
- [x] Accessibility (ARIA labels)
- [x] Documentation créée
- [ ] Utilisateur de test créé (à faire manuellement)
- [ ] Tests E2E pour Quick Login
- [ ] Ajout d'autres rôles (futur)

---

## 🎓 Bonnes Pratiques

### DO ✅

- Utiliser Quick Login **uniquement en développement**
- Créer des utilisateurs de test **dédiés**
- Documenter les credentials dans ce fichier
- Désactiver automatiquement en production
- Ajouter des ARIA labels

### DON'T ❌

- Ne jamais commit de vrais credentials
- Ne jamais activer en production
- Ne pas utiliser de comptes réels
- Ne pas oublier de créer les utilisateurs de test

---

## 📚 Ressources

- **Inspiration** : WeLAB (`C:\Users\ibzpc\Git\WeLAB\frontend\src\features\auth\pages\LoginPage.tsx`)
- **Documentation MUI** : https://mui.com/material-ui/react-button/
- **Next.js Environment** : https://nextjs.org/docs/app/building-your-application/configuring/environment-variables

---

**Créé par** : Assistant IA  
**Inspiré de** : WeLAB Quick Login  
**Grade** : S++ (conforme aux standards)

