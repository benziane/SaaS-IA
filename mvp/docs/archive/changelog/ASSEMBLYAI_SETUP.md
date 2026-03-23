# 🎙️ ASSEMBLYAI INTEGRATION GUIDE

## ⚠️ SÉCURITÉ CRITIQUE

**JAMAIS** partager votre clé API AssemblyAI publiquement !
- ❌ Ne pas commit `.env` dans Git
- ❌ Ne pas partager la clé dans les messages/code
- ✅ Utiliser `.env` pour stocker la clé
- ✅ Révoquer immédiatement si exposée

---

## 🚀 CONFIGURATION

### 1. Obtenir une clé API AssemblyAI

1. Créer un compte sur [AssemblyAI](https://www.assemblyai.com/)
2. Aller sur le [Dashboard](https://www.assemblyai.com/dashboard)
3. Copier votre clé API

### 2. Configurer la clé API

**Option A : Mode MOCK (par défaut)**
```bash
# backend/.env
ASSEMBLYAI_API_KEY=MOCK
```
- ✅ Pas besoin de clé API réelle
- ✅ Transcriptions simulées instantanées
- ✅ Idéal pour le développement/tests

**Option B : Mode RÉEL (production)**
```bash
# backend/.env
ASSEMBLYAI_API_KEY=votre_cle_api_reelle_ici
```
- ✅ Transcriptions réelles via AssemblyAI
- ✅ Support de YouTube URLs directement
- ⚠️ Consomme des crédits AssemblyAI

### 3. Redémarrer le backend

```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\tools\env_mng
.\restart-env.ps1
```

---

## 📝 UTILISATION

### URLs YouTube supportées

```
✅ https://youtube.com/watch?v=pAwRgHoBHR0
✅ https://youtu.be/pAwRgHoBHR0
✅ https://youtu.be/pAwRgHoBHR0?si=OhTfiOUU4W4b4Vwc
✅ https://youtube.com/watch?v=pAwRgHoBHR0&t=10s
✅ https://www.youtube.com/embed/pAwRgHoBHR0
```

### Frontend

1. Aller sur http://localhost:3002/transcription
2. Coller l'URL YouTube
3. Cliquer sur "Start Transcription"
4. Attendre la fin du traitement

### Backend API

```bash
# Créer une transcription
POST http://localhost:8004/api/transcription
Content-Type: application/json
Authorization: Bearer <token>

{
  "video_url": "https://youtu.be/pAwRgHoBHR0?si=OhTfiOUU4W4b4Vwc"
}

# Récupérer le statut
GET http://localhost:8004/api/transcription/{job_id}
Authorization: Bearer <token>
```

---

## 🏗️ ARCHITECTURE

### Services créés

1. **`app/transcription/youtube_service.py`**
   - Extraction de l'ID vidéo YouTube
   - Validation des URLs
   - Normalisation des URLs

2. **`app/transcription/assemblyai_service.py`**
   - Transcription via AssemblyAI
   - Support du mode synchrone et asynchrone
   - Gestion des erreurs

3. **`app/modules/transcription/service.py`** (mis à jour)
   - Intégration YouTube + AssemblyAI
   - Mode MOCK pour le développement
   - Traitement en arrière-plan

### Flux de traitement

```
1. Frontend envoie URL YouTube
   ↓
2. Backend valide l'URL (YouTubeService)
   ↓
3. Backend crée un job (status: PENDING)
   ↓
4. Background task démarre (status: PROCESSING)
   ↓
5. YouTubeService normalise l'URL
   ↓
6. AssemblyAIService transcrit (mode MOCK ou RÉEL)
   ↓
7. Backend met à jour le job (status: COMPLETED)
   ↓
8. Frontend affiche la transcription
```

---

## 🧪 TESTS

### Mode MOCK (sans clé API)

```bash
# Le backend détecte automatiquement le mode MOCK
# Logs backend :
⚠️  Mode MOCK activé pour Assembly AI - Transcriptions simulées
```

**Comportement** :
- Transcription instantanée (2 secondes)
- Texte simulé avec informations de debug
- Pas de consommation de crédits

### Mode RÉEL (avec clé API)

```bash
# Le backend détecte la clé API réelle
# Logs backend :
✅ Assembly AI configuré avec clé API réelle
```

**Comportement** :
- Transcription réelle via AssemblyAI
- Temps de traitement variable (selon durée vidéo)
- Consomme des crédits AssemblyAI

---

## 🐛 DÉPANNAGE

### Erreur : "Invalid YouTube URL"

**Cause** : URL YouTube non reconnue

**Solution** :
- Vérifier que l'URL est valide
- Utiliser un format supporté (voir section URLs)

### Erreur : "AssemblyAI transcription failed"

**Cause** : Problème avec l'API AssemblyAI

**Solutions** :
1. Vérifier que la clé API est valide
2. Vérifier les crédits AssemblyAI
3. Passer en mode MOCK pour tester

### Mode MOCK ne se désactive pas

**Cause** : Clé API invalide détectée

**Solution** :
```bash
# backend/.env
# Vérifier que la clé ne contient pas :
# - "MOCK"
# - "your-"
# - "change-"

# Exemple de clé valide :
ASSEMBLYAI_API_KEY=30efa8c7565e4344ab96182c233a1793
```

---

## 📊 LOGS

### Logs importants

```bash
# Mode détecté
⚠️  Mode MOCK activé pour Assembly AI
✅ Assembly AI configuré avec clé API réelle

# Traitement
transcription_job_created: job_id=xxx, mock_mode=true
transcription_processing_started: job_id=xxx
youtube_video_id_extracted: video_id=pAwRgHoBHR0
assemblyai_transcribe_start: audio_url=https://...
assemblyai_transcribe_success: transcript_id=xxx
transcription_completed: job_id=xxx

# Erreurs
transcription_failed: job_id=xxx, error=...
youtube_invalid_url: url=...
assemblyai_transcribe_error: error=...
```

---

## 💰 COÛTS ASSEMBLYAI

### Tarification (2025)

- **Gratuit** : 5 heures/mois
- **Pay-as-you-go** : $0.37/heure audio
- **Pro** : À partir de $50/mois

### Optimisation des coûts

1. **Utiliser le mode MOCK** pour le développement
2. **Tester avec des vidéos courtes** en mode RÉEL
3. **Monitorer l'usage** sur le dashboard AssemblyAI

---

## 🔗 RESSOURCES

- [AssemblyAI Documentation](https://www.assemblyai.com/docs)
- [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard)
- [AssemblyAI Python SDK](https://github.com/AssemblyAI/assemblyai-python-sdk)
- [AssemblyAI Pricing](https://www.assemblyai.com/pricing)

---

## ✅ CHECKLIST DE DÉPLOIEMENT

Avant de déployer en production :

- [ ] Clé API AssemblyAI configurée dans `.env`
- [ ] `.env` dans `.gitignore` (ne pas commit)
- [ ] Tests réalisés en mode MOCK
- [ ] Tests réalisés en mode RÉEL avec vidéos courtes
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] Monitoring AssemblyAI configuré
- [ ] Budget AssemblyAI défini

---

**Version:** 1.0.0  
**Date:** 2025-11-14  
**Auteur:** SaaS-IA Team

