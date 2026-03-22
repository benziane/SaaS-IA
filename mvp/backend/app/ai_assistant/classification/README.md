# AI Classification Module - Grade S++

## 📋 Vue d'ensemble

Module de **classification intelligente de contenu** et **sélection automatique de modèle IA** pour le SaaS.

**Coût : 0€** (aucun appel API externe pour la classification)  
**Performance : <50ms** pour la classification  
**Couverture tests : >90%**

---

## 🎯 Objectifs

1. **Classifier automatiquement le contenu** (domaine, ton, sensibilité)
2. **Sélectionner le modèle IA optimal** selon le contexte
3. **Choisir le prompt adapté** (strict/standard/creative)
4. **Réduire les coûts IA** en évitant les double appels
5. **Standardiser** le traitement IA à travers tous les modules du SaaS

---

## 🏗️ Architecture

```
classification/
├── __init__.py                 # Exports publics
├── enums.py                    # Enums (ContentDomain, ContentTone, etc.)
├── config_loader.py            # Chargeur de config YAML avec cache
├── content_classifier.py       # Classificateur de contenu (0€)
├── model_selector.py           # Sélecteur de modèle IA
├── prompt_selector.py          # Sélecteur de prompt
├── config/
│   └── classification_config.yaml  # Configuration (domaines, stratégies, etc.)
└── tests/
    ├── test_content_classifier.py
    ├── test_model_selector.py
    ├── test_config_loader.py
    └── test_integration.py
```

---

## 🚀 Utilisation

### Méthode 1 : Via `AIAssistantService.process_text_smart()` (Recommandé)

```python
from app.ai_assistant.service import AIAssistantService
from app.ai_assistant.classification.enums import SelectionStrategy

# Traitement intelligent avec router IA
result = await AIAssistantService.process_text_smart(
    db=db,
    text=transcription_text,
    task="format_text",
    language="french",
    metadata={"title": "Rappel sur la patience", "uploader": "Cheikh..."},
    strategy=SelectionStrategy.BALANCED
)

# Résultat enrichi avec classification
print(result["classification"]["primary_domain"])  # "religious"
print(result["model_selection"]["model"])          # "groq"
print(result["prompt_config"]["use_strict_mode"])  # True
print(result["processed_text"])                    # Texte traité
```

### Méthode 2 : Classification seule (Debug)

```python
from app.ai_assistant.classification import ContentClassifier

classification = ContentClassifier.classify(
    text="Le Prophète (paix soit sur lui) a dit...",
    language="french"
)

print(classification["primary_domain"])     # "religious"
print(classification["confidence"])         # 0.85
print(classification["sensitivity"]["level"])  # "high"
print(classification["keywords_found"])     # {"religious": ["allah", "prophète"]}
```

### Méthode 3 : Sélection de modèle

```python
from app.ai_assistant.classification import ModelSelector
from app.ai_assistant.classification.enums import SelectionStrategy

model_selection = ModelSelector.select_model(
    classification=classification,
    strategy=SelectionStrategy.BALANCED
)

print(model_selection["model"])           # "groq"
print(model_selection["strategy_used"])   # "conservative" (forcé pour contenu sensible)
print(model_selection["reason"])          # "Conservative model for sensitive religious content"
```

### Méthode 4 : Via API (Debug endpoint)

```bash
POST /api/ai-assistant/classify-content
{
  "text": "Le Prophète (paix soit sur lui) a dit...",
  "language": "french",
  "metadata": {"title": "Rappel islamique"}
}
```

---

## 📊 Domaines détectés

| Domaine | Description | Sensibilité | Modèle recommandé |
|---------|-------------|-------------|-------------------|
| `religious` | Contenu religieux | HIGH | Groq, GPT-4, Claude |
| `scientific` | Contenu scientifique | MEDIUM | Gemini Pro, GPT-4 |
| `technical` | Code, infra, API | LOW | Gemini Pro, GPT-4 |
| `medical` | Contenu médical | HIGH | GPT-4, Claude |
| `legal` | Contenu juridique | MEDIUM | Gemini Pro, GPT-4 |
| `financial` | Finance, investissement | MEDIUM | Gemini Pro |
| `administrative` | Formulaires, procédures | LOW | Gemini Pro |
| `narrative` | Récits, histoires | LOW | Gemini Flash |
| `general` | Contenu général | LOW | Gemini Flash, Groq |

---

## 🎚️ Stratégies de sélection

### 1. **CONSERVATIVE** (Qualité maximale)
- Utilisé automatiquement pour contenu sensible (religious, medical, legal)
- Privilégie les modèles les plus fiables (GPT-4, Claude, Groq)
- Coût plus élevé mais qualité garantie

### 2. **BALANCED** (Défaut - Équilibre qualité/coût)
- Bon compromis pour la plupart des cas
- Sélection intelligente selon le domaine
- Ajustement automatique si sensibilité détectée

### 3. **COST_OPTIMIZED** (Coût minimal)
- Privilégie les modèles gratuits (Gemini Flash, Groq)
- Forcé en CONSERVATIVE si contenu sensible détecté
- Idéal pour contenu général ou narratif

---

## 🔒 Gestion de la sensibilité

Le système détecte automatiquement la sensibilité du contenu :

- **HIGH/CRITICAL** : Force stratégie CONSERVATIVE + STRICT MODE
- **MEDIUM** : Ajuste le prompt avec contraintes supplémentaires
- **LOW** : Traitement standard

**Déclencheurs de sensibilité :**
- Domaine sensible (religious, medical, legal)
- Mots-clés sensibles (mort, décès, souffrance, maladie grave, etc.)
- Contenu mixte avec domaine sensible

---

## ⚙️ Configuration

Fichier : `config/classification_config.yaml`

```yaml
domains:
  religious:
    weight: 1.5  # Poids augmenté pour détection sensible
    keywords:
      french: [allah, prophète, hadith, coran, ...]
      english: [allah, prophet, quran, ...]
      arabic: [الله, النبي, ...]

model_selection:
  strategies:
    conservative:
      religious: [groq, gpt-4, claude-3-opus]
      scientific: [gpt-4, claude-3, gemini-pro]
    balanced:
      religious: [groq, gemini-pro]
      general: [gemini-flash, groq]
    cost_optimized:
      religious: [groq, gemini-flash]  # Mais forcé en conservative si sensible
```

**Hot reload :**
```python
from app.ai_assistant.classification import ConfigLoader
ConfigLoader.reload_config()  # Recharge la config sans redémarrer
```

---

## 🧪 Tests

```bash
# Tous les tests
pytest backend/app/ai_assistant/classification/tests/ -v

# Tests spécifiques
pytest backend/app/ai_assistant/classification/tests/test_content_classifier.py -v
pytest backend/app/ai_assistant/classification/tests/test_model_selector.py -v
pytest backend/app/ai_assistant/classification/tests/test_integration.py -v

# Avec coverage
pytest backend/app/ai_assistant/classification/tests/ --cov=app.ai_assistant.classification --cov-report=term
```

**Objectif : >90% coverage**

---

## 📈 Métriques & Observability

Le module log automatiquement :

```python
logger.info("content_classified",
    domain="religious",
    confidence=0.85,
    sensitivity_level="high",
    processing_time_ms=23
)

logger.info("model_selected",
    model="groq",
    strategy="conservative",
    fallback=False,
    reason="Conservative model for sensitive religious content"
)
```

**Prometheus metrics** (à venir Phase 2) :
- `classification_total{domain="religious"}`
- `classification_duration_ms`
- `model_selection_total{model="groq",strategy="conservative"}`

---

## 🔄 Workflow complet

```
1. Utilisateur envoie texte
   ↓
2. ContentClassifier.classify()
   → Domaine: religious
   → Ton: popular
   → Sensibilité: HIGH
   → Confidence: 0.85
   → Temps: 23ms
   → Coût: 0€
   ↓
3. ModelSelector.select_model()
   → Stratégie demandée: BALANCED
   → Stratégie ajustée: CONSERVATIVE (sensibilité HIGH)
   → Modèle: groq
   → Temps: <1ms
   → Coût: 0€
   ↓
4. PromptSelector.select_prompt()
   → Profile: strict
   → STRICT MODE: activé
   → Contraintes: ["Preserve religious meaning", "No embellishment", ...]
   → Temps: <1ms
   → Coût: 0€
   ↓
5. AIAssistantService.process_text()
   → Provider: groq
   → Prompt: STRICT MODE
   → Traitement IA
   → Temps: ~2000ms
   → Coût: ~0.001€
   ↓
6. Résultat enrichi retourné
   → processed_text
   → classification
   → model_selection
   → prompt_config
```

**Total : ~2050ms, ~0.001€**

---

## 🎯 Cas d'usage

### 1. Transcription YouTube religieuse
```python
result = await AIAssistantService.process_text_smart(
    db=db,
    text=transcription_brute,
    task="format_text",
    language="french",
    metadata={"title": "Rappel sur la patience", "uploader": "Cheikh Mohammed"},
    strategy=SelectionStrategy.BALANCED
)
# → Détecte "religious" → Force CONSERVATIVE → Groq + STRICT MODE
```

### 2. Documentation technique
```python
result = await AIAssistantService.process_text_smart(
    db=db,
    text=code_comments,
    task="improve_quality",
    language="french",
    strategy=SelectionStrategy.COST_OPTIMIZED
)
# → Détecte "technical" → COST_OPTIMIZED OK → Gemini Flash + TECHNICAL prompt
```

### 3. Contenu mixte (religieux + scientifique)
```python
result = await AIAssistantService.process_text_smart(
    db=db,
    text="Le Prophète encourageait la recherche scientifique...",
    task="format_text",
    language="french",
    strategy=SelectionStrategy.BALANCED
)
# → Détecte "mixed" (religious + scientific) → Force CONSERVATIVE → Groq + STRICT MODE
```

---

## 🚧 Roadmap

### ✅ Phase 1 (Actuelle)
- [x] ContentClassifier avec scoring multi-domaines
- [x] ModelSelector avec 3 stratégies
- [x] PromptSelector avec profils
- [x] Configuration YAML externalisée
- [x] Tests unitaires (>90% coverage)
- [x] Intégration dans AIAssistantService
- [x] Endpoints API de debug

### 🔜 Phase 2 (Prochaine)
- [ ] Métriques Prometheus
- [ ] Dashboard Grafana
- [ ] Support multilingue étendu (arabe, espagnol, etc.)
- [ ] ML model local (FastText/TF-IDF) pour améliorer précision
- [ ] A/B testing des stratégies
- [ ] Feedback loop (correction manuelle → amélioration auto)

### 🔮 Phase 3 (Future)
- [ ] Nouveaux domaines (psychologie, finance avancée, etc.)
- [ ] Intégration avec d'autres modules SaaS
- [ ] API publique pour classification
- [ ] Versioning de la config (rollback)

---

## 📝 Notes importantes

1. **Coût 0€ pour classification** : Aucun appel IA externe pour les étapes 1-3
2. **Performance <50ms** : Classification ultra-rapide (keyword-based)
3. **Extensible** : Ajout facile de nouveaux domaines/modèles via YAML
4. **Testable** : >90% coverage avec tests unitaires et intégration
5. **Observable** : Logs structurés pour debug et monitoring
6. **Rétrocompatible** : `process_text()` existante conservée

---

## 🤝 Contribution

Pour ajouter un nouveau domaine :

1. Modifier `config/classification_config.yaml` :
   ```yaml
   domains:
     psychology:
       weight: 1.2
       keywords:
         french: [psychologie, thérapie, mental, ...]
   ```

2. Ajouter dans `model_selection.strategies` :
   ```yaml
   balanced:
     psychology: [gemini-pro, gpt-4]
   ```

3. Ajouter dans `prompt_profiles.domain_mapping` :
   ```yaml
   psychology: strict
   ```

4. Ajouter tests dans `tests/test_content_classifier.py`

5. Reload config : `ConfigLoader.reload_config()`

---

## 📚 Références

- Spec technique V2 S++ : `docs/IA_ROUTER_SPEC_TECHNIQUE_V2_S++.md`
- Architecture WeLAB : `docs/build_specs_and_prompts/WeLAB_ARCHITECTURE_SPECIFICATION_v4.0_PERFECT_10.md`
- Tests : `backend/app/ai_assistant/classification/tests/`

---

**Version:** 1.0.0  
**Date:** 2025-11-15  
**Grade:** S++ (Enterprise-ready)  
**Statut:** ✅ Production-ready (Phase 1 terminée)

---

## 📄 Documentation complète

- **Rapport de démo :** `docs/AI_ROUTER_DEMO_REPORT.md` (validation technique)
- **Synthèse exécutive :** `docs/AI_ROUTER_EXECUTIVE_SUMMARY.md` (pour COPIL)
- **Guide d'intégration :** `docs/AI_ROUTER_INTEGRATION_GUIDE.md` (pour développeurs)
- **Spec technique V2 S++ :** `docs/IA_ROUTER_SPEC_TECHNIQUE_V2_S++.md` (architecture complète)

