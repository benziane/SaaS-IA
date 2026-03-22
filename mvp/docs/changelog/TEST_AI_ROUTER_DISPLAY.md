# 🧪 GUIDE DE TEST - AI ROUTER DISPLAY

**Date:** 2025-01-16  
**Objectif:** Valider l'affichage complet des 6 steps avec AI Router

---

## 🚀 Démarrage Rapide

### 1. Backend (si pas déjà démarré)
```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp
docker compose up -d saas-ia-backend
docker compose logs saas-ia-backend -f
```

### 2. Frontend (si pas déjà démarré)
```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\frontend
npm run dev
```

### 3. Ouvrir la Page Debug
```
http://localhost:3002/transcription/debug
```

---

## ✅ Checklist de Test

### Test 1: Timeout Résolu ✅

**Action:**
1. Coller une URL YouTube (vidéo de 5-10 minutes)
2. Cliquer sur "Start Transcription"
3. Attendre la fin complète

**Résultat Attendu:**
- ✅ Pas de timeout après 30 secondes
- ✅ Transcription complète en 1-3 minutes
- ✅ Message "Transcription Complete" affiché

**Si Échec:**
- ❌ Erreur "timeout of 30000ms exceeded"
- → Vérifier que `page.tsx` a bien `timeout: 300000`

---

### Test 2: Step 5 AI Router Visible ✅

**Action:**
1. Pendant la transcription, observer les steps en temps réel
2. Vérifier que STEP 5 apparaît après STEP 4

**Résultat Attendu:**

**STEP 5 - IN_PROGRESS:**
```
🤖 STEP 5: AI ROUTER - CONTENT IMPROVEMENT
Status: IN_PROGRESS
Duration: ~2s

📥 INPUT:
  - raw_text_length: [nombre]
  - language: french/english/arabic
  - task: improve_quality
  - strategy: COST_OPTIMIZED (prefer free models)

ℹ️ INFO:
  - phase_1: Content Classification
  - phase_2: Model Selection
  - phase_3: Content Improvement
  - cost: FREE
```

**STEP 5 - SUCCESS:**
```
🤖 STEP 5: AI ROUTER - CONTENT IMPROVEMENT
Status: SUCCESS
Duration: ~15s

📤 OUTPUT:
  - improved_text_length: [nombre]
  - growth_ratio_percentage: [+/-X.X%]
  - ai_model_used: gemini-flash/groq/gemini-pro
  - cost: FREE 🆓

📊 CLASSIFICATION:
  - primary_domain: general/religious/scientific/technical
  - sensitivity_level: low/medium/high
  - classification_confidence: [0.0-1.0]

📈 STATISTICS:
  - growth_ratio: [+/-X.X%]
```

**Si Échec:**
- ❌ STEP 5 n'apparaît pas
- → Vérifier logs backend : `docker compose logs saas-ia-backend | grep "ai_router"`
- → Vérifier que `debug_logger.py` a bien les nouvelles méthodes

---

### Test 3: Numérotation Correcte ✅

**Action:**
1. Compter les steps affichés
2. Vérifier la séquence complète

**Résultat Attendu:**
```
✅ STEP 1: YOUTUBE URL VALIDATION
📥 STEP 2: YOUTUBE AUDIO DOWNLOAD
🚀 STEP 3: ASSEMBLYAI UPLOAD
⏳ STEP 4: AI TRANSCRIPTION
🤖 STEP 5: AI ROUTER - CONTENT IMPROVEMENT  ← 🆕 NOUVEAU
🧹 STEP 6: CLEANUP TEMPORARY FILES
```

**Si Échec:**
- ❌ STEP 5 manquant
- ❌ Cleanup = STEP 5 (au lieu de 6)
- → Vérifier `debug_logger.py` ligne 390

---

### Test 4: Growth Ratio Affiché ✅

**Action:**
1. Attendre la fin de STEP 5
2. Vérifier les statistiques

**Résultat Attendu:**
```
📈 STATISTICS:
  - original_length: 1500
  - improved_length: 1650
  - difference: +150
  - growth_ratio: +10.0%
```

**Validation:**
- ✅ Growth ratio entre -50% et +50% (idéal)
- ⚠️ Growth ratio > +50% (warning, mais OK)
- ✅ Affichage "✅ Within limits" ou "⚠️ Exceeds +50%"

---

### Test 5: Modèle Sélectionné Affiché ✅

**Action:**
1. Vérifier STEP 5 SUCCESS
2. Lire le modèle utilisé

**Résultat Attendu:**
```
📤 OUTPUT:
  - ai_model_used: gemini-flash  (pour contenu général)
  - ai_model_used: groq          (pour contenu religieux/sensible)
  - ai_model_used: gemini-pro    (pour contenu scientifique)
```

**Validation:**
- ✅ Modèle affiché (pas "unknown")
- ✅ Stratégie = "COST_OPTIMIZED"
- ✅ Coût = "FREE 🆓"

---

### Test 6: Boutons Restructuration Gemini/Groq ✅

**Action:**
1. Attendre "Transcription Complete"
2. Scroller vers le bas
3. Vérifier la section "AI Content Restructuring"

**Résultat Attendu:**
```
🤖 AI Content Restructuring [FREE]

[✨ Restructure with Gemini]  [⚡ Restructure with Groq]
```

**Action:**
1. Cliquer sur "Restructure with Gemini"
2. Attendre le résultat

**Résultat Attendu:**
- ✅ Bouton devient "Restructuring..."
- ✅ Résultat affiché après 10-30s
- ✅ Texte restructuré visible
- ✅ Bouton "Copy Gemini Result" disponible

**Action:**
1. Cliquer sur "Restructure with Groq"
2. Attendre le résultat

**Résultat Attendu:**
- ✅ Bouton devient "Restructuring..."
- ✅ Résultat affiché après 5-15s
- ✅ Texte restructuré visible
- ✅ Bouton "Copy Groq Result" disponible

---

## 🐛 Debugging

### Logs Backend
```powershell
# Voir tous les logs
docker compose logs saas-ia-backend -f

# Filtrer AI Router
docker compose logs saas-ia-backend | grep "ai_router"

# Filtrer STEP 5
docker compose logs saas-ia-backend | grep "STEP 5"
```

### Console Frontend
```javascript
// Ouvrir DevTools (F12)
// Onglet Console

// Vérifier WebSocket
// Devrait afficher:
[WebSocket] Connected to ws://localhost:8004/api/transcription/debug/{job_id}
[WebSocket] Message: {type: "debug_step", step: {...}}

// Vérifier STEP 5
// Chercher: "STEP 5: AI ROUTER"
```

### Vérifier Fichiers Modifiés
```powershell
# Frontend
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\frontend\src\app\(dashboard)\transcription\debug
cat page.tsx | grep "timeout: 300000"
# ✅ Devrait trouver la ligne

# Backend
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\backend\app\transcription
cat debug_logger.py | grep "STEP 5: AI ROUTER"
# ✅ Devrait trouver 3 occurrences (start, complete, failed)

cat debug_logger.py | grep "STEP 6: CLEANUP"
# ✅ Devrait trouver 1 occurrence
```

---

## 📊 Scénarios de Test

### Scénario 1: Contenu Général
**URL:** Vidéo YouTube générale (tutoriel, vlog, etc.)

**Résultat Attendu:**
- Domain: `general`
- Sensitivity: `low`
- Model: `gemini-flash`
- Strategy: `COST_OPTIMIZED`

### Scénario 2: Contenu Religieux
**URL:** Vidéo YouTube religieuse (rappel, hadith, etc.)

**Résultat Attendu:**
- Domain: `religious`
- Sensitivity: `high`
- Model: `groq` ou `gemini-pro`
- Strategy: `CONSERVATIVE`

### Scénario 3: Contenu Scientifique
**URL:** Vidéo YouTube scientifique (documentaire, cours, etc.)

**Résultat Attendu:**
- Domain: `scientific`
- Sensitivity: `medium`
- Model: `gemini-pro`
- Strategy: `BALANCED`

### Scénario 4: Contenu Technique
**URL:** Vidéo YouTube technique (coding, DevOps, etc.)

**Résultat Attendu:**
- Domain: `technical`
- Sensitivity: `low`
- Model: `gemini-flash`
- Strategy: `COST_OPTIMIZED`

---

## ✅ Validation Finale

### Checklist Complète

- [ ] **Timeout:** Transcription complète sans timeout
- [ ] **Step 1:** YouTube URL Validation visible
- [ ] **Step 2:** YouTube Audio Download (START + COMPLETE)
- [ ] **Step 3:** AssemblyAI Upload visible
- [ ] **Step 4:** AI Transcription visible
- [ ] **Step 5:** AI Router visible avec détails complets ← 🆕
  - [ ] Domain détecté
  - [ ] Model sélectionné
  - [ ] Growth ratio
  - [ ] Coût FREE
- [ ] **Step 6:** Cleanup visible
- [ ] **Boutons:** Restructure Gemini/Groq fonctionnels
- [ ] **Résultats:** Texte restructuré affiché
- [ ] **Performance:** Temps total < 3 minutes

---

## 🎯 Critères de Succès

### ✅ PASS
- Tous les 6 steps affichés
- Step 5 AI Router avec détails complets
- Pas de timeout
- Boutons Gemini/Groq fonctionnels
- Growth ratio affiché

### ❌ FAIL
- Timeout après 30s
- Step 5 manquant
- Pas de détails AI Router
- Boutons Gemini/Groq ne fonctionnent pas

---

## 📞 Support

### En cas de problème

1. **Vérifier les logs backend:**
   ```powershell
   docker compose logs saas-ia-backend -f
   ```

2. **Vérifier la console frontend:**
   - F12 → Console
   - Chercher erreurs rouges

3. **Rebuild si nécessaire:**
   ```powershell
   docker compose restart saas-ia-backend
   ```

4. **Vérifier les fichiers:**
   - `CORRECTIONS_AI_ROUTER_DISPLAY.md` (ce document)
   - `frontend/src/app/(dashboard)/transcription/debug/page.tsx`
   - `backend/app/transcription/debug_logger.py`
   - `backend/app/modules/transcription/service.py`
   - `backend/app/modules/transcription/routes.py`

---

**Status:** ✅ READY FOR TESTING  
**Version:** 1.0.0  
**Date:** 2025-01-16

