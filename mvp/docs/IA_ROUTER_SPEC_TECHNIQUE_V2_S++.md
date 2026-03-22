# Spécification Technique — Router IA Intelligent v2.0 (Grade S++)

**Version:** 2.0  
**Date:** 2025-11-15  
**Statut:** Spécification complète pour implémentation  
**Auteur:** Architecture Team  
**Niveau:** Enterprise Grade S++

---

## 📋 Table des matières

1. [Contexte et problématique](#1-contexte-et-problématique)
2. [Architecture globale](#2-architecture-globale)
3. [Composants détaillés](#3-composants-détaillés)
4. [Spécifications techniques](#4-spécifications-techniques)
5. [Stratégies de sélection](#5-stratégies-de-sélection)
6. [Configuration et extensibilité](#6-configuration-et-extensibilité)
7. [Observabilité et monitoring](#7-observabilité-et-monitoring)
8. [Tests et validation](#8-tests-et-validation)
9. [Plan d'implémentation](#9-plan-dimplémentation)
10. [Métriques de succès](#10-métriques-de-succès)

---

## 1. Contexte et problématique

### 1.1. Situation actuelle

Le SaaS utilise plusieurs modèles d'IA externes pour diverses tâches :
- **Transcription YouTube** : Gemini Flash, Groq
- **Restructuration de textes** : Gemini Flash, Gemini Pro, GPT-4, Claude
- **Analyse technique** : GPT-4, Claude
- **Traduction** : Gemini Flash, Groq

### 1.2. Problème identifié

**Constat critique** : Certains modèles ont un **style interne incompatible** avec certains types de contenus.

**Exemple concret** : Gemini Flash sur du contenu religieux
- ❌ Embellissement non souhaité ("véritable demeure", "plénitude")
- ❌ Romantisation du discours
- ❌ Ajout d'interprétations
- ❌ Ton littéraire/poétique inapproprié

**Même avec des prompts stricts (STRICT MODE)**, le modèle conserve son style pré-entraîné.

### 1.3. Impact métier

- **Qualité éditoriale dégradée** : Contenus sensibles mal traités
- **Coûts inutiles** : Appels IA multiples pour corriger
- **Risque réputationnel** : Textes religieux/scientifiques altérés
- **Expérience utilisateur** : Résultats imprévisibles

### 1.4. Solution proposée

**Router IA Intelligent** : Système de classification et sélection automatique qui :
1. Analyse le contenu **sans coût IA externe**
2. Détecte le domaine, le ton et la sensibilité
3. Sélectionne le **modèle optimal** automatiquement
4. Applique le **prompt adapté**
5. Garantit la **qualité éditoriale**

---

## 2. Architecture globale

### 2.1. Principe de séparation des responsabilités

```
┌─────────────────────────────────────────────────────────────┐
│                    Requête utilisateur                       │
│                  (texte + métadonnées)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              1. ContentClassifier (0€)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Analyse multi-domaines (scores)                    │   │
│  │ • Détection du ton                                   │   │
│  │ • Évaluation de la sensibilité                       │   │
│  │ • Extraction de mots-clés                            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  Classification
                  {domains, tone, 
                   sensitivity, confidence}
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              2. ModelSelector (0€)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Stratégie de sélection (conservative/balanced)     │   │
│  │ • Fallback automatique                               │   │
│  │ • Vérification disponibilité                         │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                   Modèle sélectionné
                   (ex: "groq")
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              3. PromptSelector (0€)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Sélection du prompt (strict/standard)             │   │
│  │ • Adaptation selon domaine                           │   │
│  │ • Injection de règles spécifiques                    │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  Prompt configuré
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              4. AIProvider (coût IA)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Appel au modèle sélectionné                        │   │
│  │ • Gestion des erreurs                                │   │
│  │ • Retry avec fallback                                │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  Résultat final
```

### 2.2. Avantages de cette architecture

✅ **Single Responsibility Principle** : Chaque composant a une responsabilité unique  
✅ **Testabilité** : Chaque composant testable indépendamment  
✅ **Extensibilité** : Ajout de nouveaux domaines/modèles sans refactoring  
✅ **Maintenabilité** : Code clair, documenté, versionné  
✅ **Observabilité** : Logging à chaque étape  
✅ **Performance** : Classification locale ultra-rapide (<50ms)

---

## 3. Composants détaillés

### 3.1. ContentClassifier

**Responsabilité** : Analyser le contenu et extraire ses caractéristiques

**Fichier** : `backend/app/ai_assistant/classification/content_classifier.py`

**Interface** :

```python
from typing import Dict, List, Optional
from enum import Enum

class ContentDomain(str, Enum):
    RELIGIOUS = "religious"
    SCIENTIFIC = "scientific"
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"
    NARRATIVE = "narrative"
    MEDICAL = "medical"
    LEGAL = "legal"
    FINANCIAL = "financial"
    GENERAL = "general"

class ContentTone(str, Enum):
    POPULAR = "popular"
    NEUTRAL = "neutral"
    ACADEMIC = "academic"
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"

class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ContentClassifier:
    """
    Classifies content using keyword-based rules and patterns.
    Zero external API cost. Fast (<50ms).
    """
    
    @classmethod
    def classify(
        cls, 
        text: str, 
        language: str = "french",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze text and return multi-domain classification.
        
        Args:
            text: Content to analyze
            language: Language code (french, english, arabic)
            metadata: Optional metadata (title, source, etc.)
        
        Returns:
            {
                "domains": {
                    "religious": 0.85,
                    "narrative": 0.45,
                    "general": 0.10
                },
                "primary_domain": "religious",
                "secondary_domain": "narrative",
                "is_mixed_content": True,
                "tone": "popular",
                "sensitivity": {
                    "level": "high",
                    "reasons": ["religious_content", "emotional_topics"],
                    "requires_strict_mode": True
                },
                "confidence": 0.85,
                "keywords_found": {
                    "religious": ["allah", "prophète", "hadith"],
                    "narrative": ["histoire", "récit"]
                },
                "language_detected": "french",
                "text_length": 1250,
                "processing_time_ms": 23
            }
        """
        ...
```

**Algorithme de classification** :

```python
def _calculate_domain_scores(self, text: str, language: str) -> Dict[str, float]:
    """
    Calculate score for each domain based on keyword matching.
    
    Score = (keywords_found / total_keywords) * domain_weight
    """
    text_lower = text.lower()
    scores = {}
    
    for domain, config in self.DOMAIN_CONFIG.items():
        keywords = config["keywords"].get(language, [])
        weight = config.get("weight", 1.0)
        
        # Count matching keywords
        matches = sum(1 for kw in keywords if kw in text_lower)
        
        # Calculate normalized score
        score = (matches / max(len(keywords), 1)) * weight
        scores[domain] = round(score, 3)
    
    return scores

def _detect_tone(self, text: str) -> ContentTone:
    """
    Detect tone using regex patterns.
    """
    text_lower = text.lower()
    
    # Check patterns in priority order
    for tone, patterns in self.TONE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return tone
    
    return ContentTone.NEUTRAL

def _evaluate_sensitivity(
    self, 
    domains: Dict[str, float],
    tone: ContentTone,
    text: str
) -> Dict:
    """
    Evaluate content sensitivity level.
    """
    reasons = []
    level = SensitivityLevel.LOW
    
    # High sensitivity domains
    if domains.get("religious", 0) > 0.5:
        reasons.append("religious_content")
        level = SensitivityLevel.HIGH
    
    if domains.get("medical", 0) > 0.5:
        reasons.append("medical_content")
        level = SensitivityLevel.HIGH
    
    # Emotional keywords
    emotional_keywords = ["mort", "deuil", "souffrance", "tragédie"]
    if any(kw in text.lower() for kw in emotional_keywords):
        reasons.append("emotional_topics")
        level = max(level, SensitivityLevel.MEDIUM)
    
    requires_strict = level in [SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]
    
    return {
        "level": level,
        "reasons": reasons,
        "requires_strict_mode": requires_strict
    }
```

---

### 3.2. ModelSelector

**Responsabilité** : Sélectionner le modèle optimal selon la classification

**Fichier** : `backend/app/ai_assistant/classification/model_selector.py`

**Interface** :

```python
from typing import List, Dict, Optional
from enum import Enum

class AIModel(str, Enum):
    GEMINI_FLASH = "gemini-flash"
    GEMINI_PRO = "gemini-pro"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    CLAUDE_3 = "claude-3"
    CLAUDE_3_OPUS = "claude-3-opus"
    GROQ = "groq"

class SelectionStrategy(str, Enum):
    CONSERVATIVE = "conservative"  # Qualité maximale, coût plus élevé
    BALANCED = "balanced"          # Équilibre qualité/coût
    COST_OPTIMIZED = "cost_optimized"  # Coût minimal

class ModelSelector:
    """
    Selects optimal AI model based on content classification.
    Supports multiple strategies and automatic fallback.
    """
    
    # Stratégies de sélection par domaine
    SELECTION_STRATEGIES = {
        SelectionStrategy.CONSERVATIVE: {
            "religious": [AIModel.GROQ, AIModel.GPT4, AIModel.CLAUDE_3_OPUS],
            "scientific": [AIModel.GPT4, AIModel.CLAUDE_3, AIModel.GEMINI_PRO],
            "technical": [AIModel.GPT4, AIModel.CLAUDE_3, AIModel.GEMINI_PRO],
            "medical": [AIModel.GPT4, AIModel.CLAUDE_3_OPUS],
            "legal": [AIModel.GPT4, AIModel.CLAUDE_3],
            "administrative": [AIModel.GEMINI_PRO, AIModel.GPT4],
            "narrative": [AIModel.GEMINI_PRO, AIModel.CLAUDE_3],
            "general": [AIModel.GEMINI_PRO, AIModel.GEMINI_FLASH]
        },
        SelectionStrategy.BALANCED: {
            "religious": [AIModel.GROQ, AIModel.GEMINI_PRO],
            "scientific": [AIModel.GEMINI_PRO, AIModel.GPT4],
            "technical": [AIModel.GEMINI_PRO, AIModel.GPT4],
            "medical": [AIModel.GEMINI_PRO, AIModel.GPT4],
            "legal": [AIModel.GEMINI_PRO, AIModel.GPT4],
            "administrative": [AIModel.GEMINI_PRO, AIModel.GEMINI_FLASH],
            "narrative": [AIModel.GEMINI_FLASH, AIModel.GEMINI_PRO],
            "general": [AIModel.GEMINI_FLASH, AIModel.GROQ]
        },
        SelectionStrategy.COST_OPTIMIZED: {
            "religious": [AIModel.GROQ, AIModel.GEMINI_FLASH],
            "scientific": [AIModel.GEMINI_FLASH, AIModel.GROQ],
            "technical": [AIModel.GEMINI_FLASH, AIModel.GROQ],
            "general": [AIModel.GEMINI_FLASH, AIModel.GROQ]
        }
    }
    
    @classmethod
    def select_model(
        cls,
        classification: Dict,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        available_models: Optional[List[str]] = None,
        override: Optional[str] = None
    ) -> Dict:
        """
        Select optimal model based on classification and strategy.
        
        Args:
            classification: Output from ContentClassifier
            strategy: Selection strategy to use
            available_models: List of currently available models
            override: Manual model override (bypasses selection)
        
        Returns:
            {
                "model": "groq",
                "strategy_used": "balanced",
                "fallback_used": False,
                "reason": "Primary model for religious content",
                "alternatives": ["gpt-4", "claude-3"]
            }
        """
        # Manual override
        if override:
            return {
                "model": override,
                "strategy_used": "manual_override",
                "fallback_used": False,
                "reason": "Manual override by user",
                "alternatives": []
            }
        
        # Get primary domain
        primary_domain = classification["primary_domain"]
        confidence = classification["confidence"]
        sensitivity = classification["sensitivity"]["level"]
        
        # Low confidence → use conservative approach
        if confidence < 0.3:
            strategy = SelectionStrategy.CONSERVATIVE
        
        # High sensitivity → force conservative
        if sensitivity in ["high", "critical"]:
            strategy = SelectionStrategy.CONSERVATIVE
        
        # Get candidate models for this domain
        candidates = cls.SELECTION_STRATEGIES[strategy].get(
            primary_domain,
            [AIModel.GEMINI_FLASH]
        )
        
        # Filter by availability
        if available_models:
            candidates = [m for m in candidates if m in available_models]
        
        # Select first available
        selected = candidates[0] if candidates else AIModel.GEMINI_FLASH
        fallback_used = selected != candidates[0] if len(candidates) > 1 else False
        
        return {
            "model": selected,
            "strategy_used": strategy,
            "fallback_used": fallback_used,
            "reason": cls._get_selection_reason(primary_domain, selected, sensitivity),
            "alternatives": candidates[1:3]  # Next 2 alternatives
        }
    
    @classmethod
    def _get_selection_reason(
        cls,
        domain: str,
        model: str,
        sensitivity: str
    ) -> str:
        """Generate human-readable selection reason."""
        if sensitivity in ["high", "critical"]:
            return f"Conservative model for sensitive {domain} content"
        return f"Optimal model for {domain} content"
```

---

### 3.3. PromptSelector

**Responsabilité** : Sélectionner et configurer le prompt adapté

**Fichier** : `backend/app/ai_assistant/classification/prompt_selector.py`

**Interface** :

```python
from typing import Dict, Optional
from enum import Enum

class PromptProfile(str, Enum):
    STRICT = "strict"              # STRICT MODE (contenus sensibles)
    STANDARD = "standard"          # Prompt normal
    CREATIVE = "creative"          # Plus de liberté (narratif)
    TECHNICAL = "technical"        # Précision technique
    TRANSLATION = "translation"    # Traduction

class PromptSelector:
    """
    Selects and configures appropriate prompt based on classification.
    """
    
    # Mapping domaine → profil de prompt
    DOMAIN_TO_PROFILE = {
        "religious": PromptProfile.STRICT,
        "scientific": PromptProfile.STRICT,
        "medical": PromptProfile.STRICT,
        "legal": PromptProfile.STRICT,
        "technical": PromptProfile.TECHNICAL,
        "administrative": PromptProfile.STANDARD,
        "narrative": PromptProfile.CREATIVE,
        "general": PromptProfile.STANDARD
    }
    
    @classmethod
    def select_prompt(
        cls,
        classification: Dict,
        task: str,
        model: str
    ) -> Dict:
        """
        Select prompt profile and configuration.
        
        Returns:
            {
                "profile": "strict",
                "task": "format_text",
                "model_specific_rules": [...],
                "additional_constraints": [...]
            }
        """
        primary_domain = classification["primary_domain"]
        sensitivity = classification["sensitivity"]
        
        # Force STRICT for high sensitivity
        if sensitivity["requires_strict_mode"]:
            profile = PromptProfile.STRICT
        else:
            profile = cls.DOMAIN_TO_PROFILE.get(
                primary_domain,
                PromptProfile.STANDARD
            )
        
        # Model-specific adjustments
        model_rules = cls._get_model_specific_rules(model, profile)
        
        # Additional constraints for sensitive content
        additional_constraints = []
        if sensitivity["level"] in ["high", "critical"]:
            additional_constraints = [
                "Interdiction absolue de romantisation",
                "Vocabulaire sobre et factuel uniquement",
                "Respect strict du ton original"
            ]
        
        return {
            "profile": profile,
            "task": task,
            "model_specific_rules": model_rules,
            "additional_constraints": additional_constraints
        }
    
    @classmethod
    def _get_model_specific_rules(cls, model: str, profile: PromptProfile) -> List[str]:
        """
        Get model-specific rules (ex: Gemini needs stricter rules).
        """
        rules = []
        
        if "gemini" in model.lower() and profile == PromptProfile.STRICT:
            rules.extend([
                "STRICT MODE activé",
                "Vocabulaire interdit: plénitude, véritable, élévation, organe, aspire",
                "Style neutre obligatoire"
            ])
        
        return rules
```

---

## 4. Spécifications techniques

### 4.1. Configuration externalisée

**Fichier** : `backend/app/ai_assistant/classification/config/classification_config.yaml`

```yaml
# Configuration du système de classification
version: "2.0"

# Domaines et mots-clés
domains:
  religious:
    weight: 1.5  # Poids plus élevé = plus sensible
    keywords:
      french:
        - allah
        - prophète
        - hadith
        - coran
        - islam
        - musulman
        - prière
        - adoration
        - paradis
        - enfer
        - dhikr
        - astaghfirullah
        - paix soit sur lui
        - salla allahou alayhi wa sallam
      arabic:
        - الله
        - النبي
        - الحديث
        - القرآن
        - الإسلام
      english:
        - allah
        - prophet
        - hadith
        - quran
        - islam
        - muslim
        - prayer
  
  scientific:
    weight: 1.0
    keywords:
      french:
        - équation
        - modèle
        - protocole
        - expérience
        - hypothèse
        - théorie
        - recherche
        - analyse
        - données
        - résultat
        - observation
        - méthode scientifique
      english:
        - equation
        - model
        - protocol
        - experiment
        - hypothesis
        - theory
  
  technical:
    weight: 1.0
    keywords:
      french:
        - serveur
        - api
        - framework
        - docker
        - kubernetes
        - json
        - base de données
        - algorithme
        - code
        - fonction
        - variable
        - backend
        - frontend
        - microservice
      english:
        - server
        - api
        - framework
        - docker
        - json
        - database

# Patterns pour détection du ton
tone_patterns:
  academic:
    - '\b(selon|d''après|conformément à|en référence à)\b'
    - '\b(étude|recherche|analyse|conclusion)\b'
    - '\b(notamment|en effet|par conséquent|ainsi)\b'
  
  formal:
    - '\b(veuillez|nous vous prions|conformément|en vertu de)\b'
    - '\b(article|loi|règlement|décret)\b'
  
  popular:
    - '\b(tu|toi|ton|ta|tes)\b'
    - '[!]{2,}'
    - '\b(super|génial|cool|sympa)\b'

# Stratégies de sélection de modèles
model_selection:
  strategies:
    conservative:
      religious: [groq, gpt-4, claude-3-opus]
      scientific: [gpt-4, claude-3, gemini-pro]
      technical: [gpt-4, claude-3, gemini-pro]
      medical: [gpt-4, claude-3-opus]
      legal: [gpt-4, claude-3]
      general: [gemini-pro, gemini-flash]
    
    balanced:
      religious: [groq, gemini-pro]
      scientific: [gemini-pro, gpt-4]
      technical: [gemini-pro, gpt-4]
      general: [gemini-flash, groq]
    
    cost_optimized:
      religious: [groq, gemini-flash]
      general: [gemini-flash, groq]

# Seuils de confiance
confidence_thresholds:
  high: 0.7
  medium: 0.4
  low: 0.2

# Sensibilité
sensitivity_keywords:
  high:
    - mort
    - deuil
    - souffrance
    - tragédie
    - maladie grave
  medium:
    - santé
    - famille
    - émotion
```

### 4.2. Chargeur de configuration

**Fichier** : `backend/app/ai_assistant/classification/config_loader.py`

```python
import yaml
from pathlib import Path
from typing import Dict
import structlog

logger = structlog.get_logger()

class ConfigLoader:
    """
    Loads and caches classification configuration from YAML.
    """
    
    _config_cache: Dict = None
    _config_path = Path(__file__).parent / "config" / "classification_config.yaml"
    
    @classmethod
    def load_config(cls, force_reload: bool = False) -> Dict:
        """
        Load configuration from YAML file.
        Uses cache for performance.
        """
        if cls._config_cache is None or force_reload:
            try:
                with open(cls._config_path, 'r', encoding='utf-8') as f:
                    cls._config_cache = yaml.safe_load(f)
                
                logger.info(
                    "classification_config_loaded",
                    version=cls._config_cache.get("version"),
                    domains_count=len(cls._config_cache.get("domains", {}))
                )
            except Exception as e:
                logger.error(
                    "classification_config_load_error",
                    error=str(e),
                    path=str(cls._config_path)
                )
                raise
        
        return cls._config_cache
    
    @classmethod
    def get_domain_config(cls, domain: str) -> Dict:
        """Get configuration for specific domain."""
        config = cls.load_config()
        return config.get("domains", {}).get(domain, {})
    
    @classmethod
    def get_strategy_config(cls, strategy: str) -> Dict:
        """Get model selection strategy configuration."""
        config = cls.load_config()
        return config.get("model_selection", {}).get("strategies", {}).get(strategy, {})
```

---

## 5. Stratégies de sélection

### 5.1. Stratégie Conservative (Qualité maximale)

**Cas d'usage** :
- Contenus sensibles (religieux, médical, légal)
- Confiance faible (<0.3)
- Niveau de sensibilité HIGH ou CRITICAL

**Modèles prioritaires** :
1. GPT-4 / Claude-3-Opus (qualité maximale)
2. Gemini Pro (équilibre)
3. Groq (sobre, gratuit)

**Coût** : Plus élevé mais qualité garantie

---

### 5.2. Stratégie Balanced (Par défaut)

**Cas d'usage** :
- Contenus standard
- Confiance moyenne (0.3-0.7)
- Sensibilité LOW ou MEDIUM

**Modèles prioritaires** :
1. Gemini Pro / Groq (bon rapport qualité/coût)
2. GPT-4 (fallback)
3. Gemini Flash (fallback économique)

**Coût** : Modéré

---

### 5.3. Stratégie Cost Optimized (Économie)

**Cas d'usage** :
- Contenus généraux
- Confiance élevée (>0.7)
- Sensibilité LOW
- Volume important

**Modèles prioritaires** :
1. Gemini Flash (gratuit, rapide)
2. Groq (gratuit, sobre)

**Coût** : Minimal

---

## 6. Configuration et extensibilité

### 6.1. Ajout d'un nouveau domaine

**Étape 1** : Ajouter dans `classification_config.yaml`

```yaml
domains:
  psychology:  # Nouveau domaine
    weight: 1.2
    keywords:
      french:
        - psychologie
        - thérapie
        - comportement
        - émotions
```

**Étape 2** : Ajouter dans `ContentDomain` enum

```python
class ContentDomain(str, Enum):
    ...
    PSYCHOLOGY = "psychology"
```

**Étape 3** : Configurer la sélection de modèle

```yaml
model_selection:
  strategies:
    balanced:
      psychology: [gemini-pro, gpt-4]
```

**Aucun autre changement nécessaire** ✅

---

### 6.2. Ajout d'un nouveau modèle

**Étape 1** : Ajouter dans `AIModel` enum

```python
class AIModel(str, Enum):
    ...
    MISTRAL_LARGE = "mistral-large"
```

**Étape 2** : Ajouter dans les stratégies

```yaml
model_selection:
  strategies:
    balanced:
      scientific: [mistral-large, gpt-4]
```

**Étape 3** : Implémenter le provider

```python
# backend/app/ai_assistant/providers/mistral.py
class MistralProvider(BaseAIProvider):
    ...
```

---

## 7. Observabilité et monitoring

### 7.1. Logging structuré

**À chaque classification** :

```python
logger.info(
    "content_classified",
    # Classification
    primary_domain=classification["primary_domain"],
    secondary_domain=classification.get("secondary_domain"),
    confidence=classification["confidence"],
    is_mixed=classification["is_mixed_content"],
    # Sensibilité
    sensitivity_level=classification["sensitivity"]["level"],
    sensitivity_reasons=classification["sensitivity"]["reasons"],
    # Sélection
    model_selected=selection["model"],
    strategy_used=selection["strategy_used"],
    fallback_used=selection["fallback_used"],
    # Performance
    processing_time_ms=classification["processing_time_ms"],
    text_length=classification["text_length"],
    # Contexte
    language=classification["language_detected"],
    keywords_count=sum(len(kw) for kw in classification["keywords_found"].values())
)
```

### 7.2. Métriques Prometheus

```python
from prometheus_client import Counter, Histogram, Gauge

# Compteurs
classification_total = Counter(
    'ai_classification_total',
    'Total classifications',
    ['domain', 'model', 'strategy']
)

classification_errors = Counter(
    'ai_classification_errors_total',
    'Classification errors',
    ['error_type']
)

# Histogrammes
classification_duration = Histogram(
    'ai_classification_duration_seconds',
    'Classification processing time',
    ['domain']
)

confidence_score = Histogram(
    'ai_classification_confidence',
    'Classification confidence score',
    ['domain'],
    buckets=[0.2, 0.4, 0.6, 0.8, 1.0]
)

# Gauges
active_models = Gauge(
    'ai_active_models',
    'Number of active AI models',
    ['model']
)
```

### 7.3. Dashboard Grafana

**Panels recommandés** :

1. **Classifications par domaine** (pie chart)
2. **Modèles sélectionnés** (bar chart)
3. **Confiance moyenne** (gauge)
4. **Temps de traitement** (histogram)
5. **Taux d'erreur** (graph)
6. **Contenus sensibles** (counter)

---

## 8. Tests et validation

### 8.1. Tests unitaires

**Fichier** : `backend/app/ai_assistant/classification/tests/test_content_classifier.py`

```python
import pytest
from app.ai_assistant.classification.content_classifier import (
    ContentClassifier,
    ContentDomain,
    SensitivityLevel
)

class TestContentClassifier:
    
    @pytest.mark.parametrize("text,expected_domain,min_confidence", [
        # Religieux
        (
            "Le Prophète (paix soit sur lui) a dit dans un hadith authentique...",
            ContentDomain.RELIGIOUS,
            0.8
        ),
        (
            "Allah dit dans le Coran que la prière est obligatoire...",
            ContentDomain.RELIGIOUS,
            0.85
        ),
        # Scientifique
        (
            "L'équation de Schrödinger décrit l'évolution quantique...",
            ContentDomain.SCIENTIFIC,
            0.7
        ),
        (
            "Les résultats de l'expérience confirment l'hypothèse initiale...",
            ContentDomain.SCIENTIFIC,
            0.6
        ),
        # Technique
        (
            "Notre API REST utilise FastAPI avec PostgreSQL et Redis...",
            ContentDomain.TECHNICAL,
            0.7
        ),
        (
            "Le serveur backend est déployé sur Kubernetes avec Docker...",
            ContentDomain.TECHNICAL,
            0.75
        ),
        # Administratif
        (
            "Veuillez remplir le formulaire de déclaration conformément...",
            ContentDomain.ADMINISTRATIVE,
            0.6
        ),
    ])
    def test_domain_classification(self, text, expected_domain, min_confidence):
        """Test domain classification accuracy."""
        result = ContentClassifier.classify(text, language="french")
        
        assert result["primary_domain"] == expected_domain
        assert result["confidence"] >= min_confidence
        assert result["domains"][expected_domain] >= min_confidence
    
    def test_sensitivity_detection_religious(self):
        """Test sensitivity detection for religious content."""
        text = "Allah a créé les cieux et la terre. Le Prophète nous enseigne..."
        result = ContentClassifier.classify(text)
        
        assert result["sensitivity"]["level"] == SensitivityLevel.HIGH
        assert "religious_content" in result["sensitivity"]["reasons"]
        assert result["sensitivity"]["requires_strict_mode"] is True
    
    def test_mixed_content_detection(self):
        """Test detection of mixed content (multiple domains)."""
        text = """
        Dans le Coran, Allah mentionne la création de l'univers.
        Les scientifiques modernes ont découvert que l'univers est en expansion.
        Cette observation confirme ce qui est mentionné dans les textes sacrés.
        """
        result = ContentClassifier.classify(text)
        
        assert result["is_mixed_content"] is True
        assert result["domains"]["religious"] > 0.5
        assert result["domains"]["scientific"] > 0.3
    
    def test_performance(self):
        """Test classification performance (<50ms)."""
        text = "Un texte de test pour mesurer la performance" * 50
        result = ContentClassifier.classify(text)
        
        assert result["processing_time_ms"] < 50
    
    def test_keywords_extraction(self):
        """Test keyword extraction."""
        text = "Le Prophète a dit dans un hadith que la prière est importante."
        result = ContentClassifier.classify(text)
        
        keywords = result["keywords_found"]["religious"]
        assert "prophète" in keywords
        assert "hadith" in keywords
        assert "prière" in keywords
```

### 8.2. Tests d'intégration

```python
class TestModelSelector:
    
    def test_conservative_strategy_for_sensitive_content(self):
        """Test that sensitive content uses conservative strategy."""
        classification = {
            "primary_domain": "religious",
            "confidence": 0.85,
            "sensitivity": {"level": "high", "requires_strict_mode": True}
        }
        
        selection = ModelSelector.select_model(
            classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        # Should force conservative for high sensitivity
        assert selection["model"] in ["groq", "gpt-4", "claude-3"]
        assert selection["strategy_used"] == SelectionStrategy.CONSERVATIVE
    
    def test_fallback_mechanism(self):
        """Test automatic fallback when primary model unavailable."""
        classification = {
            "primary_domain": "technical",
            "confidence": 0.7,
            "sensitivity": {"level": "low"}
        }
        
        # Simulate GPT-4 unavailable
        available = ["gemini-pro", "gemini-flash", "groq"]
        
        selection = ModelSelector.select_model(
            classification,
            available_models=available
        )
        
        assert selection["model"] in available
        assert selection["fallback_used"] is True
```

### 8.3. Tests end-to-end

```python
@pytest.mark.asyncio
async def test_full_pipeline_religious_content(db_session):
    """Test complete pipeline for religious content."""
    text = """
    Le Prophète Muhammad (paix soit sur lui) a dit dans un hadith authentique :
    "Les actions ne valent que par les intentions."
    Ce hadith nous enseigne l'importance de la sincérité.
    """
    
    # 1. Classification
    classification = ContentClassifier.classify(text, language="french")
    assert classification["primary_domain"] == "religious"
    assert classification["sensitivity"]["requires_strict_mode"] is True
    
    # 2. Model selection
    selection = ModelSelector.select_model(classification)
    assert selection["model"] in ["groq", "gpt-4"]  # Conservative models
    
    # 3. Prompt selection
    prompt_config = PromptSelector.select_prompt(
        classification,
        task="format_text",
        model=selection["model"]
    )
    assert prompt_config["profile"] == "strict"
    
    # 4. AI processing
    result = await AIAssistantService.process_text_smart(
        db=db_session,
        text=text,
        task="format_text"
    )
    
    assert result["provider_used"] in ["groq", "gpt-4"]
    assert "processed_text" in result
```

---

## 9. Plan d'implémentation

### Phase 1 : Foundation (4-6h) ✅ PRIORITAIRE

**Objectif** : Système fonctionnel avec règles de base

**Tâches** :
1. ✅ Créer structure de dossiers
2. ✅ Implémenter `ContentClassifier` avec scoring multi-domaines
3. ✅ Implémenter `ModelSelector` avec stratégies
4. ✅ Implémenter `PromptSelector`
5. ✅ Créer `classification_config.yaml`
6. ✅ Implémenter `ConfigLoader`
7. ✅ Tests unitaires (>90% coverage)
8. ✅ Logging structuré

**Livrables** :
- Classification fonctionnelle (0€)
- Sélection automatique de modèle
- Configuration externalisée
- Tests validés

---

### Phase 2 : Integration (2-3h)

**Objectif** : Intégration dans le service existant

**Tâches** :
1. ✅ Créer `AIAssistantService.process_text_smart()`
2. ✅ Ajouter endpoint `/api/v2/ai-assistant/process-text`
3. ✅ Ajouter endpoint `/api/ai-assistant/classify-content` (debug)
4. ✅ Migrer les routes existantes vers v2
5. ✅ Tests d'intégration
6. ✅ Documentation API

**Livrables** :
- API v2 fonctionnelle
- Rétrocompatibilité v1
- Documentation complète

---

### Phase 3 : Monitoring (1-2h)

**Objectif** : Observabilité complète

**Tâches** :
1. ✅ Implémenter métriques Prometheus
2. ✅ Créer dashboard Grafana
3. ✅ Configurer alertes
4. ✅ Logger toutes les classifications

**Livrables** :
- Dashboard opérationnel
- Alertes configurées
- Logs structurés

---

### Phase 4 : Optimization (Semaine suivante)

**Objectif** : Amélioration continue

**Tâches** :
1. ✅ Analyser les logs de classification
2. ✅ Ajuster les mots-clés selon les données réelles
3. ✅ Ajouter nouveaux domaines (médical, juridique, finance)
4. ✅ Optimiser les seuils de confiance
5. ✅ A/B testing des stratégies

**Livrables** :
- Précision améliorée (>95%)
- Nouveaux domaines supportés
- Stratégies optimisées

---

### Phase 5 : ML Enhancement (Mois suivant - optionnel)

**Objectif** : Passer à Solution B/C (modèle local)

**Tâches** :
1. ✅ Collecter dataset de classifications réelles
2. ✅ Labelliser manuellement (500-1000 exemples)
3. ✅ Entraîner modèle FastText ou MiniLM
4. ✅ Implémenter router hybride (règles + ML)
5. ✅ Comparer performances

**Livrables** :
- Modèle local entraîné
- Précision >98%
- Router hybride opérationnel

---

## 10. Métriques de succès

### 10.1. Métriques techniques

| Métrique | Cible | Mesure |
|----------|-------|--------|
| **Précision classification** | >90% | Domaine correct vs validation manuelle |
| **Temps de classification** | <50ms | P95 du temps de traitement |
| **Couverture domaines** | >95% | % de textes classifiés (non "general") |
| **Taux d'erreur** | <1% | Erreurs système / total classifications |
| **Disponibilité** | >99.9% | Uptime du service |

### 10.2. Métriques métier

| Métrique | Cible | Mesure |
|----------|-------|--------|
| **Qualité éditoriale** | +40% | Satisfaction utilisateur (sondage) |
| **Réduction coûts IA** | -30% | Coût moyen par traitement |
| **Temps de traitement** | -20% | Durée totale pipeline |
| **Contenus sensibles bien traités** | 100% | Audit manuel échantillon |

### 10.3. KPIs de monitoring

**Dashboard temps réel** :
- 📊 Classifications/heure par domaine
- 🎯 Distribution de confiance
- 🤖 Modèles sélectionnés (répartition)
- ⚡ Temps de réponse P50/P95/P99
- ❌ Taux d'erreur
- 🔥 Contenus sensibles détectés

---

## 11. Annexes

### 11.1. Exemples de classification

**Exemple 1 : Contenu religieux pur**

```python
text = "Le Prophète (paix soit sur lui) a dit : 'Les actions ne valent que par les intentions.'"

result = {
    "domains": {
        "religious": 0.92,
        "narrative": 0.15,
        "general": 0.05
    },
    "primary_domain": "religious",
    "tone": "neutral",
    "sensitivity": {
        "level": "high",
        "reasons": ["religious_content"],
        "requires_strict_mode": True
    },
    "confidence": 0.92,
    "recommended_model": "groq"
}
```

**Exemple 2 : Contenu mixte (religieux + scientifique)**

```python
text = """
Le Coran mentionne que l'univers a été créé en six jours.
Les scientifiques modernes ont découvert que l'univers est en expansion.
Cette observation est cohérente avec les versets coraniques.
"""

result = {
    "domains": {
        "religious": 0.78,
        "scientific": 0.45,
        "general": 0.10
    },
    "primary_domain": "religious",
    "secondary_domain": "scientific",
    "is_mixed_content": True,
    "tone": "academic",
    "sensitivity": {
        "level": "high",
        "reasons": ["religious_content", "scientific_claims"],
        "requires_strict_mode": True
    },
    "confidence": 0.78,
    "recommended_model": "gpt-4"  # Conservative pour contenu mixte sensible
}
```

**Exemple 3 : Contenu technique**

```python
text = "Notre API REST utilise FastAPI avec PostgreSQL et Redis pour le cache."

result = {
    "domains": {
        "technical": 0.85,
        "general": 0.15
    },
    "primary_domain": "technical",
    "tone": "neutral",
    "sensitivity": {
        "level": "low",
        "reasons": [],
        "requires_strict_mode": False
    },
    "confidence": 0.85,
    "recommended_model": "gemini-pro"
}
```

---

## 12. Conclusion

Cette spécification définit un **Router IA Intelligent Grade S++** qui :

✅ **Résout le problème** : Sélection automatique du bon modèle  
✅ **0€ de coût** : Classification locale sans API externe  
✅ **Architecture propre** : Séparation des responsabilités, testable, extensible  
✅ **Production-ready** : Logging, monitoring, métriques, tests  
✅ **Évolutif** : Configuration YAML, ajout facile de domaines/modèles  
✅ **Performant** : <50ms de classification, stratégies optimisées  

**Prochaine étape** : Implémentation Phase 1 (4-6h) pour validation terrain.

---

**Version:** 2.0  
**Statut:** ✅ Prêt pour implémentation  
**Grade:** S++ (Enterprise Production Ready)

