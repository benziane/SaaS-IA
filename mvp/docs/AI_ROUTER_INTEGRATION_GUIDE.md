# 🔌 Guide d'Intégration — AI Router

**Pour :** Développeurs Backend  
**Temps de lecture :** 5 minutes  
**Difficulté :** ⭐ Facile

---

## 🎯 Objectif

Intégrer le Router IA dans votre module pour bénéficier de la sélection automatique du meilleur modèle IA.

**Avant :** Vous choisissez manuellement le modèle  
**Après :** Le Router choisit automatiquement selon le contexte

---

## ⚡ Quick Start (2 minutes)

### Avant (sans Router)

```python
from app.ai_assistant.service import AIAssistantService

result = await AIAssistantService.process_text(
    db=db,
    text=transcription_text,
    task="format_text",
    provider="gemini",  # ❌ Choix manuel
    language="french"
)
```

### Après (avec Router)

```python
from app.ai_assistant.service import AIAssistantService
from app.ai_assistant.classification.enums import SelectionStrategy

result = await AIAssistantService.process_text_smart(  # ✅ Nouvelle méthode
    db=db,
    text=transcription_text,
    task="format_text",
    language="french",
    metadata={"title": "Titre du contenu"},  # Optionnel mais recommandé
    strategy=SelectionStrategy.BALANCED  # Ou CONSERVATIVE, COST_OPTIMIZED
)

# Le Router détecte automatiquement :
# - Domaine (religious, scientific, technical, etc.)
# - Sensibilité (LOW, MEDIUM, HIGH, CRITICAL)
# - Ton (popular, neutral, academic, formal)
# → Sélectionne le meilleur modèle
# → Applique le bon prompt (STRICT MODE si nécessaire)
```

**C'est tout !** 🎉

---

## 📚 API Complète

### Méthode `process_text_smart()`

```python
async def process_text_smart(
    db: AsyncSession,
    text: str,
    task: str,
    language: Optional[str] = None,
    metadata: Optional[Dict] = None,
    strategy: SelectionStrategy = SelectionStrategy.BALANCED,
    provider_override: Optional[str] = None
) -> Dict[str, Any]
```

#### Paramètres

| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `db` | `AsyncSession` | ✅ | Session de base de données |
| `text` | `str` | ✅ | Texte à traiter |
| `task` | `str` | ✅ | Tâche à effectuer (`format_text`, `improve_quality`, `translate`, etc.) |
| `language` | `str` | ❌ | Langue du texte (`french`, `english`, `arabic`) - Défaut: `french` |
| `metadata` | `Dict` | ❌ | Métadonnées (titre, source, uploader, etc.) |
| `strategy` | `SelectionStrategy` | ❌ | Stratégie de sélection - Défaut: `BALANCED` |
| `provider_override` | `str` | ❌ | Forcer un modèle spécifique (bypass le Router) |

#### Retour

```python
{
    "original_text": "...",
    "processed_text": "...",
    "provider_used": "groq",
    "task_performed": "format_text",
    "improvements": [...],
    
    # Informations de classification (nouveau)
    "classification": {
        "primary_domain": "religious",
        "confidence": 0.85,
        "sensitivity": {
            "level": "high",
            "requires_strict_mode": True
        },
        "tone": "popular",
        "is_mixed_content": False,
        ...
    },
    
    # Informations de sélection de modèle (nouveau)
    "model_selection": {
        "model": "groq",
        "strategy_used": "conservative",
        "reason": "Conservative model for sensitive religious content",
        "fallback_used": False,
        ...
    },
    
    # Informations de prompt (nouveau)
    "prompt_config": {
        "profile": "strict",
        "use_strict_mode": True,
        "additional_constraints": [...]
    },
    
    "total_processing_time_ms": 2050
}
```

---

## 🎛️ Stratégies de sélection

### CONSERVATIVE (Qualité maximale)

```python
strategy=SelectionStrategy.CONSERVATIVE
```

- **Usage :** Contenu sensible, critique, important
- **Modèles :** Groq, GPT-4, Claude (les plus fiables)
- **Coût :** Plus élevé
- **Exemple :** Contenu religieux, médical, légal

### BALANCED (Défaut - Équilibre)

```python
strategy=SelectionStrategy.BALANCED  # Défaut
```

- **Usage :** Cas général (recommandé)
- **Modèles :** Gemini Pro, Groq (bon compromis)
- **Coût :** Moyen
- **Ajustement auto :** Force CONSERVATIVE si sensibilité détectée

### COST_OPTIMIZED (Coût minimal)

```python
strategy=SelectionStrategy.COST_OPTIMIZED
```

- **Usage :** Contenu non sensible, volume élevé
- **Modèles :** Gemini Flash, Groq (gratuits)
- **Coût :** Minimal
- **Ajustement auto :** Force CONSERVATIVE si sensibilité détectée

---

## 💡 Exemples d'utilisation

### Exemple 1 : Transcription YouTube

```python
# Module: backend/app/transcription/service.py

async def process_transcription(
    db: AsyncSession,
    transcription_text: str,
    video_metadata: Dict
):
    # Utiliser le Router IA
    result = await AIAssistantService.process_text_smart(
        db=db,
        text=transcription_text,
        task="format_text",
        language="french",
        metadata={
            "title": video_metadata.get("title"),
            "uploader": video_metadata.get("uploader"),
            "source": "youtube"
        },
        strategy=SelectionStrategy.BALANCED
    )
    
    # Résultat enrichi avec classification
    logger.info(
        "transcription_processed",
        domain=result["classification"]["primary_domain"],
        model=result["model_selection"]["model"],
        strict_mode=result["prompt_config"]["use_strict_mode"]
    )
    
    return result["processed_text"]
```

### Exemple 2 : Markdown Viewer

```python
# Module: backend/app/markdown_viewer/service.py

async def improve_markdown(
    db: AsyncSession,
    markdown_text: str
):
    result = await AIAssistantService.process_text_smart(
        db=db,
        text=markdown_text,
        task="improve_quality",
        language="french",
        strategy=SelectionStrategy.COST_OPTIMIZED  # Optimiser coût
    )
    
    return result["processed_text"]
```

### Exemple 3 : Analyse technique

```python
# Module: backend/app/telecom_analysis/service.py

async def analyze_technical_doc(
    db: AsyncSession,
    technical_text: str
):
    result = await AIAssistantService.process_text_smart(
        db=db,
        text=technical_text,
        task="format_text",
        language="french",
        metadata={"type": "technical_documentation"},
        strategy=SelectionStrategy.BALANCED
    )
    
    # Le Router détectera automatiquement "technical"
    # et utilisera le profil TECHNICAL
    
    return result
```

### Exemple 4 : Override manuel (cas spécial)

```python
# Forcer un modèle spécifique (bypass le Router)
result = await AIAssistantService.process_text_smart(
    db=db,
    text=text,
    task="format_text",
    language="french",
    provider_override="gpt-4"  # Force GPT-4
)
```

---

## 🔍 Debug & Monitoring

### Logs structurés

Le Router génère automatiquement des logs structurés :

```python
2025-11-15 23:03:09 [info] content_classified
    primary_domain=religious
    confidence=0.587
    sensitivity_level=high
    processing_time_ms=31.1

2025-11-15 23:03:09 [info] model_selected
    model=groq
    strategy=conservative
    fallback=True
    reason="Conservative model for sensitive religious content"

2025-11-15 23:03:09 [info] prompt_selected
    profile=strict
    strict_mode=True
    constraints_count=6
```

### Endpoint de debug

Pour tester la classification sans traiter le texte :

```bash
POST /api/ai-assistant/classify-content
{
  "text": "Le Prophète (paix soit sur lui) a dit...",
  "language": "french"
}
```

Retourne :
```json
{
  "classification": {...},
  "recommended_model": {...},
  "strategy_comparison": {
    "conservative": {...},
    "balanced": {...},
    "cost_optimized": {...}
  }
}
```

---

## ⚙️ Configuration

### Fichier de configuration

`backend/app/ai_assistant/classification/config/classification_config.yaml`

**Hot reload possible :**
```python
from app.ai_assistant.classification import ConfigLoader
ConfigLoader.reload_config()  # Pas besoin de redémarrer
```

### Ajouter un nouveau domaine

```yaml
domains:
  psychology:  # Nouveau domaine
    weight: 1.2
    keywords:
      french: [psychologie, thérapie, mental, ...]
      english: [psychology, therapy, mental, ...]

model_selection:
  strategies:
    balanced:
      psychology: [gemini-pro, gpt-4]  # Modèles pour ce domaine

prompt_profiles:
  domain_mapping:
    psychology: strict  # Profil de prompt
```

---

## 🚨 Erreurs courantes

### Erreur 1 : Import manquant

```python
# ❌ Erreur
from app.ai_assistant.service import AIAssistantService
result = await AIAssistantService.process_text_smart(...)
# ModuleNotFoundError: No module named 'app.ai_assistant.classification'

# ✅ Solution
# Vérifier que le module classification existe
# Redémarrer le serveur backend
```

### Erreur 2 : Stratégie invalide

```python
# ❌ Erreur
strategy="balanced"  # String au lieu d'enum

# ✅ Solution
from app.ai_assistant.classification.enums import SelectionStrategy
strategy=SelectionStrategy.BALANCED
```

### Erreur 3 : Metadata mal formatée

```python
# ❌ Erreur
metadata="title: Rappel"  # String au lieu de dict

# ✅ Solution
metadata={"title": "Rappel", "uploader": "Cheikh"}
```

---

## 📊 Performance

### Temps de traitement

| Étape | Temps | Coût |
|-------|-------|------|
| Classification | <50ms | 0€ |
| Sélection modèle | <1ms | 0€ |
| Sélection prompt | <1ms | 0€ |
| **Total Router** | **<50ms** | **0€** |
| Traitement IA | ~2000ms | ~0.001€ |
| **TOTAL** | **~2050ms** | **~0.001€** |

**Impact :** +2.5% de latence, 0€ de coût supplémentaire

---

## ✅ Checklist d'intégration

- [ ] Importer `AIAssistantService` et `SelectionStrategy`
- [ ] Remplacer `process_text()` par `process_text_smart()`
- [ ] Ajouter `metadata` (titre, source, etc.)
- [ ] Choisir la stratégie appropriée
- [ ] Tester avec différents types de contenu
- [ ] Vérifier les logs (classification, modèle, prompt)
- [ ] Monitorer la performance (<50ms)
- [ ] Documenter l'intégration

---

## 🆘 Support

**Questions :** Équipe Backend  
**Documentation complète :** `docs/AI_ROUTER_DEMO_REPORT.md`  
**Tests :** `backend/test_ai_router.py`  
**Démo :** `backend/demo_ai_router.py`

---

**TL;DR :** Remplacer `process_text()` par `process_text_smart()` + ajouter `metadata` + choisir `strategy`. C'est tout ! 🎉

