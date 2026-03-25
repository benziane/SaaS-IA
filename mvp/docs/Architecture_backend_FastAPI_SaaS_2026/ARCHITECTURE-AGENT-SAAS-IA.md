# 🧠 Architecture Agent-Driven — SaaS IA Platform

**Version** : 3.0.0  
**Date** : 2026-03-25  
**Statut** : ✅ Validé — Aligné avec MVP existant  
**Base** : Blueprint Self-Improving Agent (Cassy Garner) adapté au stack Python/FastAPI  
**Cible** : Écosystème SaaS IA modulaire avec orchestration intelligente

---

## 📋 RÉSUMÉ EXÉCUTIF

Ce document définit l'architecture adaptée du système d'agents IA pour la plateforme SaaS-IA. Il fusionne trois sources :

1. **MVP existant** — FastAPI + SQLModel + Next.js 15 (Sneat MUI), auth JWT S++ (94/100), ports 8004/3002/5435/6382
2. **Architecture modulaire documentée** — Plugin system, Event Bus, Service Registry, Module Orchestrator
3. **Blueprint Self-Improving Agent** — Patterns agent-as-tool, two-tier classification, reactive/proactive autonomy

**Résultat** : Une architecture en 4 couches qui transforme la plateforme de "collection de modules IA" en "écosystème intelligent auto-optimisant", tout en respectant les contraintes MVP (BackgroundTasks, pas Celery ; Whisper API, pas Assembly AI ; YouTube Transcript API, pas yt-dlp).

---

## 🏗️ ARCHITECTURE GLOBALE — 4 COUCHES

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COUCHE 4 : AGENT SUPERVISOR                         │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  Platform Guardian (méta-agent)                                  │  │
│   │  • Monitoring intelligent des modules                            │  │
│   │  • Corrections réactives automatiques                            │  │
│   │  • Recommandations proactives (approval humain)                  │  │
│   │  • Rapport quotidien (webhook/email)                             │  │
│   │  • Détection module bloat (>5 endpoints = alerte)                │  │
│   └──────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                    COUCHE 3 : MODULE ROUTER                            │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  Intent Classifier (two-tier)                                    │  │
│   │  ├─ Fast Path : regex + keyword matching (gratuit, <1ms)         │  │
│   │  └─ Slow Path : LLM fallback Whisper/Claude (si ambiguïté)      │  │
│   │                                                                  │  │
│   │  Module Orchestrator (existant, enrichi)                         │  │
│   │  ├─ Découverte automatique via manifest.yaml                     │  │
│   │  ├─ Hot reload sans redémarrage                                  │  │
│   │  ├─ Cross-module context chaining (via Event Bus)                │  │
│   │  └─ Dependency resolution entre modules                          │  │
│   └──────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                    COUCHE 2 : AI MODULES                               │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │Transcript.│ │ Résumé   │ │Traduction│ │ Analyse  │ │  [N+1]   │   │
│   │  YouTube  │ │ Intelli. │ │ Multi-L  │ │Sémantique│ │ Extensib.│   │
│   │ ✅ MVP   │ │ 🔮 Ph.2  │ │ 🔮 Ph.2  │ │ 🔮 Ph.3  │ │ 🚀 15min │   │
│   └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘   │
│         └─────────────┴─────────────┴─────────────┴───────────┘       │
│                              │ Event Bus                               │
├──────────────────────────────┼──────────────────────────────────────────┤
│                    COUCHE 1 : CORE PLATFORM                            │
│   ┌──────────────────────────┴──────────────────────────────────────┐  │
│   │  FastAPI (port 8004)          │  Next.js 15 + Sneat MUI (3002) │  │
│   │  ├─ Auth JWT + RBAC (S++)     │  ├─ Dashboard adaptatif        │  │
│   │  ├─ SQLModel + AsyncPG        │  ├─ Module UI auto-discovery   │  │
│   │  ├─ Redis (6382) cache        │  ├─ React Query polling        │  │
│   │  ├─ Rate Limiting (slowapi)   │  └─ WebSocket (Phase 2)        │  │
│   │  ├─ Prometheus metrics        │                                │  │
│   │  └─ PostgreSQL (5435)         │                                │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 COUCHE 1 : CORE PLATFORM (existant)

### Ce qui existe déjà

Le MVP fournit une base solide qu'on ne touche pas :

- **Auth JWT** grade S++ (93/100) avec bcrypt, rate limiting 5 req/min login, RBAC
- **SQLModel** async avec AsyncPG, pool 20 connexions
- **Redis** cache + sessions (TTL 7 jours)
- **Prometheus** metrics middleware
- **OWASP** security headers (X-Frame-Options, CSP, HSTS)
- **Sentry** integration pour error tracking

### Adaptations nécessaires

```python
# app/core/config.py — Ajouts pour l'écosystème IA

class Settings(BaseSettings):
    # ... existant ...
    
    # ============================================
    # AI SERVICES
    # ============================================
    
    openai_api_key: str = Field(
        default="",
        description="Clé API OpenAI (Whisper transcription)"
    )
    
    anthropic_api_key: str = Field(
        default="",
        description="Clé API Anthropic (classification, résumé)"
    )
    
    # ============================================
    # MODULE SYSTEM
    # ============================================
    
    modules_path: str = Field(
        default="app/ai/modules",
        description="Chemin des modules IA"
    )
    
    modules_auto_discover: bool = Field(
        default=True,
        description="Découverte automatique des modules au démarrage"
    )
    
    module_health_interval: int = Field(
        default=60,
        description="Intervalle health check modules (secondes)"
    )
    
    # ============================================
    # GUARDIAN (Couche 4)
    # ============================================
    
    guardian_enabled: bool = Field(
        default=False,
        description="Active le Platform Guardian (Phase 3+)"
    )
    
    guardian_cron_hour: int = Field(
        default=22,
        description="Heure d'exécution du cron Guardian (22 = 22h)"
    )
    
    guardian_webhook_url: str = Field(
        default="",
        description="URL webhook pour rapports Guardian"
    )
```

---

## 📡 COUCHE 2 : AI MODULES

### Architecture de chaque module

Chaque module IA est un plugin auto-contenu qui suit le pattern standardisé. Aucune modification du code core n'est nécessaire pour en ajouter un.

```
app/ai/modules/{module_name}/
├── manifest.yaml          # Métadonnées, events, permissions
├── __init__.py            # Classe principale (extends BaseAIModule)
├── service.py             # Logique métier IA
├── routes.py              # Endpoints FastAPI
├── schemas.py             # Pydantic request/response
├── models.py              # SQLModel tables
├── events.py              # Event handlers (pub/sub)
├── config.py              # Config spécifique au module
└── tests/
    ├── test_service.py
    ├── test_routes.py
    └── test_events.py
```

### Module Transcription (MVP — Priorité 1)

```yaml
# app/ai/modules/transcription/manifest.yaml

name: transcription
version: 1.0.0
description: "Transcription automatique de vidéos YouTube avec correction linguistique"
author: Ibrahim Benziane
class_name: TranscriptionModule

# Stratégie duale :
# 1. YouTube Transcript API (gratuit, instantané, ~60% succès)
# 2. Whisper API fallback ($0.36/h, 97% moins cher qu'Assembly AI)
ai_provider: whisper
fallback_provider: youtube_transcript_api

dependencies:
  - youtube-transcript-api
  - openai  # Whisper API

endpoints:
  - POST /transcribe
  - GET /status/{job_id}
  - GET /list
  - GET /{transcription_id}
  - DELETE /{transcription_id}

permissions_required:
  - transcription:create
  - transcription:read
  - transcription:delete

events_emitted:
  - transcription.started
  - transcription.progress
  - transcription.completed
  - transcription.failed

events_subscribed: []

resources:
  cpu: "0.5"
  memory: "512Mi"
  max_concurrent_jobs: 5

configuration:
  max_video_duration: 3600        # 1h max
  rate_limit: "5/hour"            # Par utilisateur
  supported_languages:
    - fr
    - en
    - ar
    - auto
  correction_enabled: true
  cache_ttl: 86400                # 24h cache Redis
```

### Flow de traitement

```
┌──────────────────────────────────────────────────────────────────┐
│  POST /api/v1/modules/transcription/transcribe                   │
│  Body: { "youtube_url": "...", "language": "fr" }                │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 1. Validation                │
│    ├─ JWT check              │
│    ├─ Rate limit (5/h)       │
│    ├─ URL YouTube valide     │
│    └─ Durée < 1h             │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 2. Create DB Record          │
│    status: PENDING            │
│    progress: 0%               │
│    Event: transcription.started│
└──────────────┬───────────────┘
               │
               ▼ BackgroundTasks (pas Celery pour MVP)
┌──────────────────────────────┐
│ 3. Stratégie 1 :             │
│    YouTube Transcript API     │
│    (gratuit, instantané)      │
│    ├─ Succès (~60%) → étape 5│
│    └─ Échec → étape 4        │
└──────────────┬───────────────┘
               │ (si échec)
               ▼
┌──────────────────────────────┐
│ 4. Stratégie 2 :             │
│    Whisper API (OpenAI)       │
│    ($0.006/min)               │
│    progress: 40%              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 5. Correction & Formatage    │
│    ├─ Regex nettoyage         │
│    ├─ Ponctuation             │
│    ├─ Segmentation phrases    │
│    └─ (Phase 2: LanguageTool) │
│    progress: 70%              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ 6. Sauvegarde résultat       │
│    ├─ DB: status COMPLETED    │
│    ├─ Cache Redis (24h)       │
│    ├─ progress: 100%          │
│    └─ Event:                  │
│       transcription.completed │
└──────────────────────────────┘
```

### Service de transcription

```python
# app/ai/modules/transcription/service.py

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from openai import AsyncOpenAI
from sqlmodel.ext.asyncio.session import AsyncSession
from app.ai.modules.transcription.models import Transcription, TranscriptionStatus
from app.ai.modules.transcription.correction import CorrectionService
from app.core.event_bus import event_bus
from uuid import UUID
import re
import logging

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Service de transcription YouTube.
    
    Stratégie duale :
    1. YouTube Transcript API (gratuit, légal, ~60% succès)
    2. Whisper API fallback ($0.006/min)
    
    Coûts MVP (100 vidéos/mois, 10min moyenne) :
    - YouTube API : $0 (60% des cas)
    - Whisper : ~$2.4/mois (40% restants)
    - Total : ~$2.4/mois vs $250/mois (Assembly AI)
    """
    
    def __init__(self, openai_api_key: str):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.correction = CorrectionService()
    
    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extrait l'ID vidéo depuis une URL YouTube."""
        patterns = [
            r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'(?:embed/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"URL YouTube invalide: {url}")
    
    async def transcribe_youtube(
        self,
        video_id: str,
        language: str = "auto"
    ) -> tuple[str, str]:
        """
        Transcrit une vidéo YouTube.
        
        Returns:
            tuple: (texte_transcrit, source) 
                   source = "youtube_api" ou "whisper"
        """
        # Stratégie 1 : YouTube Transcript API
        languages = [language] if language != "auto" else ["fr", "en", "ar"]
        
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=languages
            )
            raw_text = " ".join([item["text"] for item in transcript_list])
            logger.info(f"YouTube transcript trouvé pour {video_id} ({len(raw_text)} chars)")
            return raw_text, "youtube_api"
            
        except NoTranscriptFound:
            logger.info(f"Pas de transcript YouTube pour {video_id}, fallback Whisper")
        except Exception as e:
            logger.warning(f"Erreur YouTube API pour {video_id}: {e}")
        
        # Stratégie 2 : Whisper API (fallback)
        # Note: nécessite l'URL du stream audio
        # Pour MVP, on utilise yt-dlp en mode extract_info (pas de download)
        raw_text = await self._whisper_transcribe(video_id, language)
        return raw_text, "whisper"
    
    async def _whisper_transcribe(
        self,
        video_id: str,
        language: str
    ) -> str:
        """Transcription via Whisper API."""
        # TODO: Implémenter extraction audio stream + Whisper
        # Pour MVP Phase 1 : lever une exception claire
        raise NotImplementedError(
            "Whisper fallback à implémenter en Phase 1.5. "
            "La vidéo n'a pas de sous-titres YouTube disponibles."
        )
    
    async def process_transcription(
        self,
        transcription_id: UUID,
        session: AsyncSession
    ):
        """Background task : traitement complet d'une transcription."""
        transcription = await session.get(Transcription, transcription_id)
        if not transcription:
            logger.error(f"Transcription {transcription_id} introuvable")
            return
        
        try:
            # Update: PROCESSING
            transcription.status = TranscriptionStatus.PROCESSING
            transcription.progress = 10
            await session.commit()
            
            await event_bus.publish(
                "transcription.progress",
                {"id": str(transcription_id), "progress": 10},
                source_module="transcription"
            )
            
            # Extraire video_id
            video_id = self.extract_video_id(transcription.youtube_url)
            transcription.video_id = video_id
            transcription.progress = 20
            await session.commit()
            
            # Transcrire
            raw_text, source = await self.transcribe_youtube(
                video_id,
                transcription.language
            )
            transcription.raw_transcript = raw_text
            transcription.source = source
            transcription.progress = 60
            await session.commit()
            
            # Corriger et formater
            corrected = self.correction.correct_and_format(
                raw_text, transcription.language
            )
            
            # Sauvegarder résultat
            transcription.transcript_text = corrected
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.progress = 100
            await session.commit()
            
            await event_bus.publish(
                "transcription.completed",
                {
                    "id": str(transcription_id),
                    "video_id": video_id,
                    "source": source,
                    "char_count": len(corrected),
                },
                source_module="transcription"
            )
            
            logger.info(f"Transcription {transcription_id} terminée ({source})")
            
        except Exception as e:
            logger.error(f"Transcription {transcription_id} échouée: {e}")
            transcription.status = TranscriptionStatus.FAILED
            transcription.error_message = str(e)
            transcription.progress = 0
            await session.commit()
            
            await event_bus.publish(
                "transcription.failed",
                {"id": str(transcription_id), "error": str(e)},
                source_module="transcription"
            )
```

### Service de correction

```python
# app/ai/modules/transcription/correction.py

import re
from typing import Optional


class CorrectionService:
    """
    Correction et formatage du texte transcrit.
    
    MVP : règles regex basiques.
    Phase 2 : intégration LanguageTool API.
    Phase 3 : correction par LLM (Claude/GPT).
    """
    
    def correct_and_format(
        self,
        text: str,
        language: str = "fr"
    ) -> str:
        """Pipeline de correction complète."""
        text = self._clean_whitespace(text)
        text = self._fix_punctuation(text, language)
        text = self._capitalize_sentences(text)
        text = self._format_paragraphs(text)
        return text.strip()
    
    def _clean_whitespace(self, text: str) -> str:
        """Nettoie les espaces multiples et caractères spéciaux."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\[.*?\]', '', text)  # Enlever [Musique], [Applaudissements]
        text = text.replace('\n', ' ')
        return text
    
    def _fix_punctuation(self, text: str, language: str) -> str:
        """Corrige la ponctuation selon la langue."""
        # Espace avant ponctuation double (français)
        if language in ("fr", "auto"):
            text = re.sub(r'\s*([?!;:])', r' \1', text)
        
        # Point après les phrases sans ponctuation
        text = re.sub(r'([a-zéèêëàâäùûüôöîïç])\s+([A-ZÉÈÊËÀÂÄÙÛÜÔÖÎÏÇ])', r'\1. \2', text)
        
        return text
    
    def _capitalize_sentences(self, text: str) -> str:
        """Met en majuscule le début de chaque phrase."""
        sentences = re.split(r'([.!?]\s+)', text)
        result = []
        for i, part in enumerate(sentences):
            if i == 0 or (i > 0 and re.match(r'[.!?]\s+', sentences[i - 1])):
                part = part[:1].upper() + part[1:] if part else part
            result.append(part)
        return ''.join(result)
    
    def _format_paragraphs(self, text: str) -> str:
        """Découpe en paragraphes lisibles (~3-5 phrases)."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        paragraphs = []
        current = []
        
        for sentence in sentences:
            current.append(sentence)
            if len(current) >= 4:
                paragraphs.append(' '.join(current))
                current = []
        
        if current:
            paragraphs.append(' '.join(current))
        
        return '\n\n'.join(paragraphs)
```

---

## 🔀 COUCHE 3 : MODULE ROUTER

### Intent Classifier — Adaptation du Two-Tier Pattern

Le blueprint propose un système de classification à deux niveaux. Voici l'adaptation pour notre contexte SaaS IA, utile dès le 2ème module :

```python
# app/core/intent_classifier.py

from typing import Optional, Dict, List
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Résultat de classification d'intention."""
    module_name: str
    confidence: float
    method: str  # "keyword" ou "llm"
    cost: float  # en USD


class IntentClassifier:
    """
    Classifieur d'intention two-tier.
    
    Adapté du blueprint Self-Improving Agent :
    - Fast Path : regex + keywords (gratuit, <1ms)
    - Slow Path : LLM fallback (seulement si ambiguïté)
    
    70%+ des requêtes routées gratuitement via keywords.
    """
    
    # Patterns par module (extensible via manifest.yaml)
    MODULE_PATTERNS: Dict[str, List[str]] = {
        "transcription": [
            r"transcri[rpb]",          # transcrire, transcription, transcript
            r"sous.?titr",             # sous-titre, sous titres
            r"youtube\.com|youtu\.be", # URLs YouTube
            r"vid[eé]o.*texte",        # vidéo en texte
            r"audio.*texte",           # audio en texte
            r"speech.?to.?text",       # speech to text
        ],
        "summary": [  # Phase 2
            r"r[eé]sum[eé]",           # résumé, résumer
            r"synth[eè]se",            # synthèse
            r"points?\s+cl[eé]s?",     # points clés
            r"tl;?dr",                 # TLDR
        ],
        "translation": [  # Phase 2
            r"tradui[rst]",            # traduire, traduction, traduis
            r"translat",              # translate, translation
            r"en\s+(anglais|français|arabe)",
        ],
        "analysis": [  # Phase 3
            r"analy[sz]",              # analyser, analysis
            r"sentiment",
            r"entit[eé]s?",            # entités
            r"mots?.?cl[eé]s?",        # mots-clés
            r"th[eè]mes?",
        ],
    }
    
    # Poids par module (priorité si match multiple)
    MODULE_WEIGHTS: Dict[str, float] = {
        "transcription": 1.0,
        "summary": 0.9,
        "translation": 0.9,
        "analysis": 0.8,
    }
    
    CONFIDENCE_THRESHOLD = 0.6
    
    def classify(self, text: str) -> Optional[ClassificationResult]:
        """
        Classifie une requête.
        
        1. Essaie keyword matching (gratuit)
        2. Si pas assez confiant → LLM fallback
        3. Si toujours ambiguë → retourne None
        """
        # Fast Path : Keywords
        result = self._keyword_match(text)
        if result and result.confidence >= self.CONFIDENCE_THRESHOLD:
            logger.debug(f"Intent classified via keywords: {result.module_name} ({result.confidence:.2f})")
            return result
        
        # Slow Path : LLM (Phase 2, désactivé pour MVP)
        # result = await self._llm_classify(text)
        # if result:
        #     return result
        
        return result  # Peut être None ou low-confidence
    
    def _keyword_match(self, text: str) -> Optional[ClassificationResult]:
        """Classification par patterns regex."""
        text_lower = text.lower()
        scores: Dict[str, float] = {}
        
        for module, patterns in self.MODULE_PATTERNS.items():
            matches = sum(1 for p in patterns if re.search(p, text_lower))
            if matches > 0:
                score = (matches / len(patterns)) * self.MODULE_WEIGHTS.get(module, 1.0)
                scores[module] = score
        
        if not scores:
            return None
        
        best_module = max(scores, key=scores.get)
        return ClassificationResult(
            module_name=best_module,
            confidence=scores[best_module],
            method="keyword",
            cost=0.0
        )
    
    def register_module_patterns(
        self,
        module_name: str,
        patterns: List[str],
        weight: float = 1.0
    ):
        """
        Enregistre les patterns d'un module dynamiquement.
        Appelé par le Module Orchestrator au chargement.
        """
        self.MODULE_PATTERNS[module_name] = patterns
        self.MODULE_WEIGHTS[module_name] = weight
        logger.info(f"Patterns enregistrés pour module '{module_name}': {len(patterns)} patterns")
```

### Module Orchestrator enrichi

```python
# app/core/module_orchestrator.py (enrichi avec Intent Classifier)

from pathlib import Path
from importlib import import_module
from typing import Dict, Optional, List, Any
from app.ai.base_module import BaseAIModule
from app.core.service_registry import ServiceRegistry
from app.core.intent_classifier import IntentClassifier
import yaml
import logging

logger = logging.getLogger(__name__)


class ModuleOrchestrator:
    """
    Orchestrateur de modules IA avec classification d'intention.
    
    Enrichi par rapport à la version existante :
    - Intégration IntentClassifier pour routing intelligent
    - Chargement dynamique des patterns depuis manifest.yaml
    - Health monitoring avec métriques par module
    - Support hot reload sans redémarrage
    """
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.modules: Dict[str, BaseAIModule] = {}
        self.classifier = IntentClassifier()
        self.app = None
    
    async def start_all_modules(
        self,
        app,
        event_bus,
        modules_path: Path
    ) -> Dict[str, bool]:
        """Découvre, charge et démarre tous les modules."""
        self.app = app
        results = {}
        
        # Découverte
        for module_dir in sorted(modules_path.iterdir()):
            manifest_path = module_dir / "manifest.yaml"
            if not module_dir.is_dir() or not manifest_path.exists():
                continue
            
            module_name = module_dir.name
            
            try:
                # Charger manifest
                with open(manifest_path) as f:
                    manifest = yaml.safe_load(f)
                
                # Import dynamique
                module_package = import_module(f"app.ai.modules.{module_name}")
                module_class = getattr(module_package, manifest["class_name"])
                module_instance = module_class()
                
                # Initialiser
                success = await module_instance.initialize()
                if not success:
                    results[module_name] = False
                    continue
                
                # Enregistrer dans Service Registry
                await self.service_registry.register_module(
                    module_instance,
                    manifest.get("endpoints", [])
                )
                
                # Monter le routeur FastAPI
                router = module_instance.get_router()
                app.include_router(
                    router,
                    prefix=f"/api/v1/modules/{module_name}",
                    tags=[module_name]
                )
                
                # Enregistrer les événements
                module_instance.register_events(event_bus)
                
                # Enregistrer les patterns de classification
                if "classification_patterns" in manifest:
                    self.classifier.register_module_patterns(
                        module_name,
                        manifest["classification_patterns"],
                        manifest.get("classification_weight", 1.0)
                    )
                
                self.modules[module_name] = module_instance
                results[module_name] = True
                
                logger.info(
                    f"✅ Module chargé: {module_name} "
                    f"v{manifest['version']} "
                    f"({len(manifest.get('endpoints', []))} endpoints)"
                )
                
            except Exception as e:
                logger.error(f"❌ Erreur chargement {module_name}: {e}")
                results[module_name] = False
        
        return results
    
    async def route_request(self, text: str) -> Optional[str]:
        """
        Route une requête texte vers le bon module.
        Utilise le two-tier classifier.
        """
        result = self.classifier.classify(text)
        if result and result.module_name in self.modules:
            return result.module_name
        return None
    
    async def reload_module(self, module_name: str) -> bool:
        """Hot reload d'un module sans redémarrer l'app."""
        if module_name not in self.modules:
            return False
        
        old_module = self.modules[module_name]
        await old_module.shutdown()
        await self.service_registry.unregister_module(module_name)
        
        # Recharger
        modules_path = Path("app/ai/modules")
        # ... (rechargement dynamique)
        
        return True
    
    def get_module(self, name: str) -> Optional[BaseAIModule]:
        """Récupère une instance de module."""
        return self.modules.get(name)
    
    def list_modules(self) -> List[Dict[str, Any]]:
        """Liste tous les modules avec leur état."""
        return [
            {
                "name": name,
                "version": module.get_metadata().version,
                "status": "active",
                "endpoints": module.get_metadata().endpoints,
            }
            for name, module in self.modules.items()
        ]
```

### Event Bus

```python
# app/core/event_bus.py

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Événement système."""
    name: str
    data: Dict[str, Any]
    source_module: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class EventBus:
    """
    Bus d'événements in-process pour communication inter-modules.
    
    MVP : pub/sub en mémoire (suffisant pour mono-instance).
    Phase 3 : migration vers Redis Streams pour multi-instance.
    
    Pattern utilisé :
    - Modules publient des événements (transcription.completed)
    - Autres modules s'abonnent (summary écoute transcription.completed)
    - Découplage total : les modules ne se connaissent pas
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._history: List[Event] = []
        self._max_history: int = 1000
    
    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Enregistre un handler pour un événement."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.debug(f"Souscription: {handler.__qualname__} → {event_name}")
    
    async def publish(
        self,
        event_name: str,
        data: Dict[str, Any],
        source_module: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """Publie un événement à tous les abonnés."""
        event = Event(
            name=event_name,
            data=data,
            source_module=source_module,
            correlation_id=correlation_id
        )
        
        # Historique (pour debugging et audit)
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # Dispatch
        handlers = self._handlers.get(event_name, [])
        if not handlers:
            logger.debug(f"Event {event_name} publié, aucun handler")
            return
        
        logger.info(
            f"Event {event_name} → {len(handlers)} handler(s) "
            f"(source: {source_module})"
        )
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Erreur handler {handler.__qualname__} "
                    f"pour {event_name}: {e}"
                )
    
    def get_history(
        self,
        event_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Event]:
        """Récupère l'historique des événements."""
        events = self._history
        if event_name:
            events = [e for e in events if e.name == event_name]
        return events[-limit:]


# Singleton global
event_bus = EventBus()
```

---

## 🛡️ COUCHE 4 : PLATFORM GUARDIAN

### Adaptation du pattern Agent Lab

Le Platform Guardian est l'adaptation du méta-agent "Agent Lab" du blueprint. Différences clés :

| Aspect | Agent Lab (Blueprint) | Platform Guardian (SaaS IA) |
|--------|----------------------|----------------------------|
| **Stack** | TypeScript + Supabase | Python + SQLModel + PostgreSQL |
| **Interface** | Telegram bot | Webhook + Dashboard admin |
| **Sources IA** | 6 blogs RSS | Logs système + métriques modules |
| **Autonomie** | Auto-apply + approval | Même principe, adapté aux modules |
| **Cron** | Nightly 10 PM | Configurable (défaut 22h) |
| **Phase** | Dès le début | Phase 3+ (quand >3 modules actifs) |

### Architecture Guardian

```python
# app/guardian/guardian_service.py

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    REACTIVE = "reactive"      # Auto-apply (low risk)
    PROACTIVE = "proactive"    # Approval required (higher risk)


class ChangeStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class GuardianRecommendation:
    """Recommandation du Guardian pour améliorer un module."""
    id: str
    type: ChangeType
    target_module: str
    title: str
    description: str
    rationale: str
    status: ChangeStatus = ChangeStatus.PENDING
    priority: int = 5  # 1-10
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class PlatformGuardian:
    """
    Méta-agent de supervision de la plateforme.
    
    Adapté du pattern Agent Lab (blueprint Self-Improving Agent).
    
    Responsabilités :
    1. Monitoring intelligent des modules (pas juste up/down)
    2. Corrections réactives automatiques (low risk)
    3. Recommandations proactives (approval humain)
    4. Détection de module bloat
    5. Rapport quotidien
    
    Déployé en Phase 3+ quand la plateforme a >3 modules actifs.
    """
    
    # ─────────────────────────────────────────
    # SEUILS DE SURVEILLANCE
    # ─────────────────────────────────────────
    
    ENDPOINT_BLOAT_WARNING = 5   # Alerte si module > 5 endpoints
    ENDPOINT_BLOAT_SPLIT = 8    # Recommander split si > 8 endpoints
    ERROR_RATE_THRESHOLD = 0.05  # 5% taux d'erreur = alerte
    LATENCY_THRESHOLD_MS = 2000  # 2s = alerte performance
    
    def __init__(self, orchestrator, event_bus):
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.recommendations: List[GuardianRecommendation] = []
    
    # ─────────────────────────────────────────
    # RÉACTIF : Auto-apply (sans approval)
    # ─────────────────────────────────────────
    
    async def reactive_checks(self) -> List[GuardianRecommendation]:
        """
        Corrections automatiques à faible risque.
        
        Inclut :
        - Restart modules en erreur récurrente
        - Nettoyage cache expiré
        - Reset compteurs après incidents résolus
        - Correction configs détectées comme invalides
        """
        fixes = []
        
        for name, module in self.orchestrator.modules.items():
            health = await module.health_check()
            
            # Module unhealthy → tenter restart
            if health.status == "unhealthy":
                logger.warning(f"Module {name} unhealthy, tentative restart")
                fix = GuardianRecommendation(
                    id=f"reactive-restart-{name}-{datetime.utcnow().isoformat()}",
                    type=ChangeType.REACTIVE,
                    target_module=name,
                    title=f"Restart automatique : {name}",
                    description=f"Module détecté comme unhealthy, restart déclenché.",
                    rationale=f"Health check: {health.status}",
                    status=ChangeStatus.APPLIED,
                    priority=9
                )
                
                # Auto-apply : restart le module
                success = await self.orchestrator.reload_module(name)
                if success:
                    fix.status = ChangeStatus.APPLIED
                else:
                    fix.status = ChangeStatus.PENDING
                    fix.type = ChangeType.PROACTIVE  # Escalade
                
                fixes.append(fix)
        
        return fixes
    
    # ─────────────────────────────────────────
    # PROACTIF : Recommandations (avec approval)
    # ─────────────────────────────────────────
    
    async def proactive_analysis(self) -> List[GuardianRecommendation]:
        """
        Analyse approfondie avec recommandations pour approval humain.
        
        Inclut :
        - Module bloat detection (>5 endpoints)
        - Performance dégradée persistante
        - Patterns d'erreurs récurrents
        - Suggestions d'optimisation
        """
        recommendations = []
        
        for name, module in self.orchestrator.modules.items():
            metadata = module.get_metadata()
            
            # ── Détection bloat ──
            endpoint_count = len(metadata.endpoints)
            
            if endpoint_count >= self.ENDPOINT_BLOAT_SPLIT:
                recommendations.append(GuardianRecommendation(
                    id=f"proactive-bloat-{name}",
                    type=ChangeType.PROACTIVE,
                    target_module=name,
                    title=f"Module bloat critique : {name} ({endpoint_count} endpoints)",
                    description=(
                        f"Le module {name} a {endpoint_count} endpoints (seuil: {self.ENDPOINT_BLOAT_SPLIT}). "
                        f"Recommandation : splitter en sous-modules spécialisés."
                    ),
                    rationale="Pattern Agent Lab : flag à 5, split recommandé à 8+",
                    priority=7
                ))
            elif endpoint_count >= self.ENDPOINT_BLOAT_WARNING:
                recommendations.append(GuardianRecommendation(
                    id=f"proactive-bloat-warning-{name}",
                    type=ChangeType.PROACTIVE,
                    target_module=name,
                    title=f"Module bloat warning : {name} ({endpoint_count} endpoints)",
                    description=f"Le module {name} approche du seuil de bloat.",
                    rationale="Surveillance préventive",
                    priority=4
                ))
            
            # ── Analyse métriques ──
            metrics = module.get_metrics()
            if metrics:
                error_rate = metrics.get("error_rate", 0)
                avg_latency = metrics.get("avg_latency_ms", 0)
                
                if error_rate > self.ERROR_RATE_THRESHOLD:
                    recommendations.append(GuardianRecommendation(
                        id=f"proactive-errors-{name}",
                        type=ChangeType.PROACTIVE,
                        target_module=name,
                        title=f"Taux d'erreur élevé : {name} ({error_rate:.1%})",
                        description=f"Investiguer les erreurs récurrentes du module.",
                        rationale=f"Seuil: {self.ERROR_RATE_THRESHOLD:.1%}, actuel: {error_rate:.1%}",
                        priority=8
                    ))
                
                if avg_latency > self.LATENCY_THRESHOLD_MS:
                    recommendations.append(GuardianRecommendation(
                        id=f"proactive-latency-{name}",
                        type=ChangeType.PROACTIVE,
                        target_module=name,
                        title=f"Performance dégradée : {name} ({avg_latency}ms)",
                        description=f"Latence moyenne au-dessus du seuil acceptable.",
                        rationale=f"Seuil: {self.LATENCY_THRESHOLD_MS}ms, actuel: {avg_latency}ms",
                        priority=6
                    ))
        
        return recommendations
    
    # ─────────────────────────────────────────
    # CRON QUOTIDIEN
    # ─────────────────────────────────────────
    
    async def daily_cycle(self) -> Dict[str, Any]:
        """
        Cycle quotidien du Guardian.
        
        Séquence (inspirée du pipeline Agent Lab) :
        1. HEALTH CHECK : vérifier tous les modules
        2. REACTIVE : appliquer corrections automatiques
        3. PROACTIVE : analyser et recommander
        4. REPORT : générer rapport quotidien
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "modules_checked": len(self.orchestrator.modules),
            "reactive_fixes": [],
            "proactive_recommendations": [],
            "overall_health": "healthy"
        }
        
        # 1. Reactive
        reactive = await self.reactive_checks()
        report["reactive_fixes"] = [
            {"module": r.target_module, "title": r.title, "status": r.status.value}
            for r in reactive
        ]
        
        # 2. Proactive
        proactive = await self.proactive_analysis()
        report["proactive_recommendations"] = [
            {
                "module": r.target_module,
                "title": r.title,
                "priority": r.priority,
                "status": r.status.value
            }
            for r in proactive
        ]
        self.recommendations.extend(proactive)
        
        # 3. Overall health
        if any(r.priority >= 8 for r in reactive + proactive):
            report["overall_health"] = "degraded"
        if any(r.priority >= 9 for r in reactive if r.status != ChangeStatus.APPLIED):
            report["overall_health"] = "critical"
        
        # 4. Publier rapport via Event Bus
        await self.event_bus.publish(
            "guardian.daily_report",
            report,
            source_module="guardian"
        )
        
        logger.info(
            f"Guardian daily cycle: "
            f"{len(reactive)} fixes, "
            f"{len(proactive)} recommendations, "
            f"health: {report['overall_health']}"
        )
        
        return report
```

---

## 📁 STRUCTURE DE PROJET COMPLÈTE

```
SaaS-IA/
├── mvp/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                      # Point d'entrée + lifespan
│   │   │   ├── config.py                    # Settings (existant + AI settings)
│   │   │   ├── database.py                  # SQLModel async engine
│   │   │   ├── auth.py                      # JWT + RBAC (existant, S++)
│   │   │   ├── rate_limit.py                # Slowapi (existant)
│   │   │   │
│   │   │   ├── core/                        # Infrastructure partagée
│   │   │   │   ├── __init__.py
│   │   │   │   ├── event_bus.py             # 🆕 Pub/Sub in-process
│   │   │   │   ├── service_registry.py      # 🆕 Registre modules
│   │   │   │   ├── module_orchestrator.py   # 🆕 Orchestrateur + classifier
│   │   │   │   ├── intent_classifier.py     # 🆕 Two-tier classification
│   │   │   │   └── redis.py                 # Client Redis (existant)
│   │   │   │
│   │   │   ├── ai/                          # Écosystème IA
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_module.py           # 🆕 Interface abstraite
│   │   │   │   │
│   │   │   │   └── modules/                 # Modules auto-découverts
│   │   │   │       ├── transcription/       # ✅ MVP Priority 1
│   │   │   │       │   ├── manifest.yaml
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── service.py       # YouTubeService + Whisper
│   │   │   │       │   ├── correction.py    # CorrectionService
│   │   │   │       │   ├── routes.py        # FastAPI endpoints
│   │   │   │       │   ├── schemas.py       # Pydantic models
│   │   │   │       │   ├── models.py        # SQLModel tables
│   │   │   │       │   ├── events.py        # Event handlers
│   │   │   │       │   └── tests/
│   │   │   │       │
│   │   │   │       ├── summary/             # 🔮 Phase 2
│   │   │   │       │   └── manifest.yaml
│   │   │   │       │
│   │   │   │       └── translation/         # 🔮 Phase 2
│   │   │   │           └── manifest.yaml
│   │   │   │
│   │   │   ├── guardian/                    # 🆕 Phase 3+
│   │   │   │   ├── __init__.py
│   │   │   │   ├── guardian_service.py
│   │   │   │   ├── models.py               # Recommendation, ChangeLog
│   │   │   │   └── routes.py               # Admin endpoints
│   │   │   │
│   │   │   ├── models/                      # SQLModel (existant)
│   │   │   │   ├── user.py
│   │   │   │   └── transcription.py         # 🆕 Transcription model
│   │   │   │
│   │   │   └── schemas/                     # Pydantic (existant)
│   │   │       ├── user.py
│   │   │       └── transcription.py         # 🆕 Transcription schemas
│   │   │
│   │   ├── alembic/                         # Migrations DB
│   │   ├── tests/                           # Tests
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── e2e/
│   │   │
│   │   ├── pyproject.toml                   # Dépendances Python
│   │   └── Dockerfile
│   │
│   ├── frontend/                            # Next.js 15 + Sneat MUI
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── transcription/       # Page transcription
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── modules/             # Dashboard modules
│   │   │   │   │       └── page.tsx
│   │   │   │   └── (auth)/                  # Login/Register (existant)
│   │   │   │
│   │   │   ├── features/
│   │   │   │   ├── auth/                    # Auth hooks (existant)
│   │   │   │   └── transcription/           # 🆕
│   │   │   │       ├── hooks/
│   │   │   │       │   └── useTranscription.ts
│   │   │   │       └── components/
│   │   │   │           ├── TranscriptionForm.tsx
│   │   │   │           ├── TranscriptionProgress.tsx
│   │   │   │           └── TranscriptionResult.tsx
│   │   │   │
│   │   │   └── services/
│   │   │       └── transcriptionApi.ts      # 🆕 API client
│   │   │
│   │   ├── package.json
│   │   └── next.config.ts
│   │
│   ├── docker-compose.yml                   # Orchestration
│   └── tools/                               # Scripts dev (existant)
│
└── docs/                                    # Documentation
    ├── ARCHITECTURE-AGENT-SAAS-IA.md        # CE DOCUMENT
    └── ...
```

---

## 🔄 LIFESPAN APPLICATION (main.py enrichi)

```python
# app/main.py — Séquence de démarrage enrichie

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.module_orchestrator import ModuleOrchestrator
from app.core.service_registry import ServiceRegistry
from app.core.event_bus import event_bus
from app.database import init_db, close_db
from app.core.redis import redis_service
from app.config import get_settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Cycle de vie enrichi avec Module Orchestrator.
    
    Séquence startup :
    1. PostgreSQL (existant)
    2. Redis (existant)
    3. Service Registry (nouveau)
    4. Event Bus (nouveau)
    5. Module Orchestrator → découverte + démarrage modules (nouveau)
    6. Guardian (Phase 3+, optionnel)
    """
    logger.info("🚀 SaaS-IA Platform starting...")
    
    # 1. Database
    await init_db()
    logger.info("✅ PostgreSQL connected (port 5435)")
    
    # 2. Redis
    await redis_service.connect()
    logger.info("✅ Redis connected (port 6382)")
    
    # 3. Service Registry
    service_registry = ServiceRegistry()
    app.state.service_registry = service_registry
    logger.info("✅ Service Registry initialized")
    
    # 4. Event Bus
    app.state.event_bus = event_bus
    logger.info("✅ Event Bus initialized")
    
    # 5. Module Orchestrator
    orchestrator = ModuleOrchestrator(service_registry)
    app.state.orchestrator = orchestrator
    
    modules_path = Path(settings.modules_path)
    if modules_path.exists():
        results = await orchestrator.start_all_modules(
            app=app,
            event_bus=event_bus,
            modules_path=modules_path
        )
        success = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"✅ Modules: {success}/{total} démarrés")
        for name, ok in results.items():
            logger.info(f"   {'✅' if ok else '❌'} {name}")
    else:
        logger.warning(f"⚠️ Modules path not found: {modules_path}")
    
    # 6. Guardian (Phase 3+)
    if settings.guardian_enabled:
        from app.guardian.guardian_service import PlatformGuardian
        guardian = PlatformGuardian(orchestrator, event_bus)
        app.state.guardian = guardian
        logger.info("✅ Platform Guardian activated")
    
    logger.info("=" * 60)
    logger.info("🎉 SaaS-IA Platform ready!")
    logger.info(f"   API: http://localhost:{settings.api_port}/docs")
    logger.info("=" * 60)
    
    yield  # ← Application tourne ici
    
    # Shutdown
    logger.info("🛑 SaaS-IA Platform shutting down...")
    
    if hasattr(app.state, 'orchestrator'):
        for name in list(orchestrator.modules.keys()):
            await orchestrator.modules[name].shutdown()
    
    await redis_service.close()
    await close_db()
    
    logger.info("✅ SaaS-IA Platform stopped cleanly")


# Application
app = FastAPI(
    title="SaaS-IA Platform",
    description="Écosystème modulaire de services d'intelligence artificielle",
    version="2.0.0",
    lifespan=lifespan,
)

# Auth routes (existant)
from app.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# Module management API
@app.get("/api/v1/modules", tags=["modules"])
async def list_modules():
    """Liste tous les modules IA actifs."""
    orchestrator = app.state.orchestrator
    return orchestrator.list_modules()

@app.get("/api/v1/modules/{module_name}/health", tags=["modules"])
async def module_health(module_name: str):
    """Health check d'un module spécifique."""
    module = app.state.orchestrator.get_module(module_name)
    if not module:
        from fastapi import HTTPException
        raise HTTPException(404, f"Module '{module_name}' non trouvé")
    health = await module.health_check()
    return health
```

---

## 💰 COÛTS ESTIMÉS

### MVP (Phase 1)

| Service | Coût/mois | Détail |
|---------|-----------|--------|
| YouTube Transcript API | $0 | Gratuit, ~60% des vidéos |
| Whisper API (40% fallback) | $2-6 | 50-200 vidéos, 10min moy. |
| PostgreSQL | $0 | Docker local |
| Redis | $0 | Docker local |
| **Total MVP** | **$2-6/mois** | |

### Comparaison avec alternatives

| Stack | Coût 100 vidéos/mois |
|-------|---------------------|
| **SaaS IA (Whisper)** | **$6** |
| Assembly AI | $250 |
| Rev.ai | $180 |
| Google Speech-to-Text | $144 |

### Production (Hetzner Cloud)

| Service | Coût/mois |
|---------|-----------|
| VPS CX21 | €5.83 |
| Whisper API | $6-30 |
| Domain + SSL (Caddy) | ~$1 |
| **Total prod** | **~$15-40/mois** |

---

## 📅 PLAN D'IMPLÉMENTATION

### Phase 1 : Module Transcription MVP (12-14h)

```
Jour 1 (6h) — Backend :
  ├─ [1h] Core infrastructure (event_bus, service_registry, base_module)
  ├─ [0.5h] Model Transcription (SQLModel) + migration Alembic
  ├─ [0.5h] Schemas Pydantic
  ├─ [1h] YouTubeService (YouTube Transcript API)
  ├─ [1h] CorrectionService (regex MVP)
  ├─ [1h] Background processor + routes API
  └─ [1h] Tests unitaires (≥85%)

Jour 2 (6h) — Frontend + intégration :
  ├─ [2h] Page /transcription (Sneat MUI)
  ├─ [1h] TranscriptionForm + validation (Zod)
  ├─ [1h] Polling status + progress bar (React Query)
  ├─ [1h] Affichage résultat + export TXT
  └─ [1h] Tests E2E basiques

Buffer (2h) — Debug + polish
```

### Phase 2 : Modules additionnels (2-3 semaines)

```
Semaine 1 : Module Résumé
  ├─ Écoute transcription.completed via Event Bus
  ├─ Intégration Claude API pour résumé intelligent
  └─ Multi-format (bullets, paragraphe, outline)

Semaine 2 : Module Traduction
  ├─ Intégration DeepL ou Claude pour traduction
  ├─ 50+ langues
  └─ Glossaire personnalisable

Semaine 3 : Intent Classifier LLM fallback
  ├─ Activer le slow path (Claude Haiku)
  ├─ Routing intelligent entre 3+ modules
  └─ WebSocket real-time updates
```

### Phase 3 : Platform Guardian (1 semaine)

```
  ├─ Guardian service + cron quotidien
  ├─ Dashboard admin recommandations
  ├─ Webhook rapports (email/Slack)
  └─ Module bloat monitoring
```

### Phase 4 : Production hardening

```
  ├─ Migration Celery (si >1000 jobs/jour)
  ├─ Monitoring Grafana dashboards
  ├─ CI/CD GitHub Actions
  ├─ Hetzner deployment + Caddy HTTPS
  └─ Semantic search (différenciateur marché)
```

---

## ✅ DÉCISIONS ARCHITECTURALES (ADR)

### ADR-001 : BackgroundTasks > Celery (MVP)

**Contexte** : Le MVP n'a pas besoin de queue distribuée.  
**Décision** : Utiliser FastAPI BackgroundTasks.  
**Raison** : 0 infrastructure supplémentaire, <100ms latency, suffisant pour <1000 jobs/jour.  
**Migration** : Celery en Phase 4 si volume >1000/jour (effort : 4-6h).

### ADR-002 : Whisper API > Assembly AI

**Contexte** : Choix du provider de transcription.  
**Décision** : Whisper API (OpenAI) avec YouTube Transcript API en primary.  
**Raison** : 97% moins cher ($0.36/h vs $15/h), qualité équivalente.

### ADR-003 : Event Bus in-process > Redis Streams (MVP)

**Contexte** : Communication inter-modules.  
**Décision** : Pub/sub Python in-process.  
**Raison** : Mono-instance MVP, 0 overhead, testable. Migration Redis Streams en Phase 3.

### ADR-004 : Two-tier classifier > LLM-only routing

**Contexte** : Routing des requêtes vers les modules.  
**Décision** : Keywords d'abord (gratuit), LLM fallback seulement si ambiguïté.  
**Raison** : 70%+ des requêtes routées gratuitement, ~$0 vs ~$0.001/requête.

### ADR-005 : Guardian Phase 3+ > Guardian immédiat

**Contexte** : Quand activer le méta-agent de supervision.  
**Décision** : Phase 3, quand >3 modules actifs.  
**Raison** : Inutile avec 1 module, overhead de maintenance. Le pattern reactive/proactive prend tout son sens avec un écosystème de modules.

### ADR-006 : YouTube Transcript API > yt-dlp

**Contexte** : Extraction du contenu vidéo YouTube.  
**Décision** : YouTube Transcript API (officielle, gratuite).  
**Raison** : Légal (pas de violation ToS), gratuit, instantané. yt-dlp viole les conditions d'utilisation de YouTube.

---

## 🎯 CRITÈRES DE SUCCÈS

| Métrique | Cible | Phase |
|----------|-------|-------|
| Temps ajout nouveau module | < 15 min | 1 |
| Latence API p95 | < 100ms | 1 |
| Test coverage | ≥ 85% | 1 |
| Cache hit rate | ≥ 95% | 2 |
| Score sécurité | ≥ 93/100 (S++) | 1 |
| Coût transcription/vidéo | < $0.05 | 1 |
| Uptime | ≥ 99.5% | 3 |
| Modules actifs | 5+ | 3 |
| Guardian auto-fixes/mois | > 0 | 3 |

---

## 📚 RÉFÉRENCES

- **Blueprint source** : Self-Improving AI Agent System (@cassygarner)
- **Architecture existante** : ARCHITECTURE-SAAS-IA-SCALABLE-V2.md
- **MVP simplifié** : MODULE_TRANSCRIPTION_MVP_SIMPLIFIE.md
- **Audit sécurité** : AUDIT_SECURITE_AUTH.md (Grade S++ 93/100)
- **État des lieux** : ETAT_DES_LIEUX_COMPLET.md

---

*Document créé le : 2026-03-25*  
*Version : 3.0.0*  
*Auteur : Architecture Team + AI Assistant*  
*Statut : ✅ PRÊT POUR IMPLÉMENTATION*
