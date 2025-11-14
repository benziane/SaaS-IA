# 🧪 TESTS VALIDATION - INTÉGRATION SNEAT

**Date** : 2025-11-14  
**Version** : 1.0.0  
**Statut** : 📋 À EXÉCUTER

---

## 🎯 OBJECTIF

Valider que l'intégration Sneat fonctionne correctement avec l'authentification JWT backend existante.

---

## ✅ CHECKLIST TESTS MANUELS

### Phase 1 : Démarrage & Accès (5 min)

- [ ] **1.1 Démarrer l'environnement**
  ```powershell
  cd C:\Users\ibzpc\Git\SaaS-IA\mvp\tools\env_mng
  .\start-env.bat
  ```

- [ ] **1.2 Vérifier statut**
  ```powershell
  .\check-status.bat
  ```
  **Attendu** :
  - ✅ Backend (FastAPI) : Port 8004
  - ✅ Frontend (Next.js) : Port 3002
  - ✅ PostgreSQL : Port 5435
  - ✅ Redis : Port 6382

- [ ] **1.3 Ouvrir frontend**
  - URL : `http://localhost:3002`
  - **Attendu** : Redirection automatique vers `/login`

---

### Phase 2 : Page Login (5 min)

- [ ] **2.1 Vérifier UI Sneat**
  - ✅ Layout BlankLayout (pas de sidebar)
  - ✅ Design professionnel Sneat
  - ✅ Responsive (tester mobile view)
  - ✅ Dark mode toggle visible

- [ ] **2.2 Tester formulaire login**
  - Email : `admin@saas-ia.com`
  - Password : `admin123`
  - Cliquer "Se connecter"
  
  **Attendu** :
  - ✅ Validation Zod fonctionne
  - ✅ Requête POST `/api/auth/login` envoyée
  - ✅ Token JWT reçu et stocké
  - ✅ Redirection vers `/dashboard`

- [ ] **2.3 Tester erreurs**
  - Essayer login avec mauvais credentials
  - **Attendu** : Toast d'erreur affiché (sonner)

---

### Phase 3 : Dashboard (10 min)

- [ ] **3.1 Vérifier Layout Sneat**
  - ✅ VerticalLayout avec sidebar
  - ✅ Menu vertical à gauche
  - ✅ Items menu : "Dashboard", "Transcriptions"
  - ✅ User dropdown en haut à droite
  - ✅ Dark mode toggle fonctionne

- [ ] **3.2 Vérifier AuthGuard**
  - Se déconnecter
  - Essayer d'accéder à `/dashboard` directement
  - **Attendu** : Redirection vers `/login`

- [ ] **3.3 Tester navigation**
  - Cliquer sur "Dashboard" dans le menu
  - Cliquer sur "Transcriptions" dans le menu
  - **Attendu** : Navigation fluide, pas d'erreurs console

- [ ] **3.4 Vérifier responsive**
  - Réduire largeur navigateur (mobile view)
  - **Attendu** : Menu devient hamburger, layout s'adapte

---

### Phase 4 : Page Transcription (5 min)

- [ ] **4.1 Accéder à la page**
  - Cliquer "Transcriptions" dans le menu
  - **Attendu** : Page s'affiche avec layout Sneat

- [ ] **4.2 Vérifier UI**
  - ✅ Layout Sneat cohérent
  - ✅ Formulaire visible
  - ✅ Composants MUI/Sneat

---

### Phase 5 : Tests Techniques (10 min)

- [ ] **5.1 Console Browser**
  - Ouvrir DevTools (F12)
  - Onglet Console
  - **Attendu** : Aucune erreur critique
  - **Toléré** : Warnings TypeScript (désactivés temporairement)

- [ ] **5.2 Network**
  - Onglet Network
  - Faire login
  - **Attendu** :
    - POST `/api/auth/login` → 200 OK
    - Header `Authorization: Bearer <token>` sur requêtes suivantes

- [ ] **5.3 React Query Devtools**
  - Ouvrir React Query Devtools (coin bas droite)
  - **Attendu** :
    - Queries visibles
    - Cache fonctionne
    - Pas d'erreurs

- [ ] **5.4 Zustand Store**
  - Installer Redux DevTools Extension
  - Ouvrir Redux DevTools
  - Sélectionner "AuthStore"
  - **Attendu** :
    - `isAuthenticated: true` après login
    - `user` object présent
    - `token` stocké

---

### Phase 6 : Tests de Régression (10 min)

- [ ] **6.1 Fonctionnalités existantes**
  - ✅ Login/Logout fonctionne
  - ✅ JWT auth fonctionne
  - ✅ API calls backend fonctionnent
  - ✅ TanStack Query fonctionne
  - ✅ Zustand store fonctionne

- [ ] **6.2 Performance**
  - Ouvrir Lighthouse (DevTools)
  - Lancer audit Performance
  - **Attendu** : Score ≥ 80

- [ ] **6.3 Accessibilité**
  - Lancer audit Accessibility (Lighthouse)
  - **Attendu** : Score ≥ 90

---

## 🐛 BUGS CONNUS & SOLUTIONS

### Bug 1 : `useAuth is not a function`

**Symptôme** :
```
Runtime TypeError: (0, useAuth.default) is not a function
```

**Cause** : `useAuth` n'existe pas, il faut utiliser `useAuthStore`

**Solution** : ✅ CORRIGÉ
```typescript
// ❌ AVANT
import useAuth from '@/features/auth/hooks/useAuth'
const { isAuthenticated, isLoading } = useAuth()

// ✅ APRÈS
import { useAuthStore } from '@/lib/store'
const isAuthenticated = useAuthStore(state => state.isAuthenticated)
const isLoading = useAuthStore(state => state.isLoading)
```

---

## 📊 RÉSULTATS ATTENDUS

### Critères de Succès

| Critère | Cible | Statut |
|---------|-------|--------|
| **Login fonctionne** | ✅ | ⏳ À tester |
| **Dashboard accessible** | ✅ | ⏳ À tester |
| **Layout Sneat affiché** | ✅ | ⏳ À tester |
| **Menu navigation OK** | ✅ | ⏳ À tester |
| **AuthGuard protège routes** | ✅ | ⏳ À tester |
| **GuestOnlyRoute fonctionne** | ✅ | ⏳ À tester |
| **Responsive OK** | ✅ | ⏳ À tester |
| **Dark mode OK** | ✅ | ⏳ À tester |
| **Aucune erreur console critique** | ✅ | ⏳ À tester |
| **Performance ≥ 80** | ✅ | ⏳ À tester |

---

## 🚀 COMMANDES RAPIDES

### Démarrer environnement
```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\tools\env_mng
.\start-env.bat
```

### Vérifier statut
```powershell
.\check-status.bat
```

### Redémarrer frontend (si bug)
```powershell
.\restart-env.bat
```

### Logs frontend
```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\frontend
npm run dev
```

### Logs backend
```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\backend
poetry run uvicorn app.main:app --reload --port 8004
```

---

## 📝 RAPPORT DE TESTS

**À remplir après exécution des tests**

### Tests Réussis ✅
- [ ] Login/Logout
- [ ] Dashboard
- [ ] Navigation menu
- [ ] AuthGuard
- [ ] GuestOnlyRoute
- [ ] Responsive
- [ ] Dark mode
- [ ] Performance

### Tests Échoués ❌
- [ ] (À documenter si échecs)

### Bugs Trouvés 🐛
- [ ] (À documenter si bugs)

---

**Document créé par** : Assistant IA  
**Date** : 2025-11-14  
**Version** : 1.0.0  
**Statut** : 📋 Prêt pour tests manuels

