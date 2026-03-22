"""AI Assistant Service Layer - Grade S++"""

import structlog
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant.providers.base import BaseAIProvider
from app.ai_assistant.providers import GeminiProvider, ClaudeProvider, GroqProvider

# AI Router components
from app.ai_assistant.classification.content_classifier import ContentClassifier
from app.ai_assistant.classification.model_selector import ModelSelector
from app.ai_assistant.classification.prompt_selector import PromptSelector
from app.ai_assistant.classification.enums import SelectionStrategy

logger = structlog.get_logger(__name__)


class AIAssistantService:
    """
    Service layer for AI Assistant operations.
    
    Handles business logic for AI text processing, provider management,
    and intelligent fallback.
    """
    
    # Provider registry
    _providers: dict[str, type[BaseAIProvider]] = {
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "groq": GroqProvider
    }
    
    # Fallback order (prioritize free providers)
    _fallback_order: list[str] = ["groq", "gemini", "claude"]
    
    # Provider metadata
    _provider_metadata: dict[str, dict] = {
        "groq": {
            "display_name": "Groq Llama 3.3 70B (Ultra-Fast)",
            "is_free": True,
            "cost_tier": "free",
            "speed": "ultra-fast",
            "priority": 1
        },
        "gemini": {
            "display_name": "Google Gemini 2.0 Flash",
            "is_free": True,
            "cost_tier": "free",
            "speed": "fast",
            "priority": 2
        },
        "claude": {
            "display_name": "Claude Sonnet 3.5 (Most Intelligent)",
            "is_free": False,
            "cost_tier": "high",
            "speed": "medium",
            "priority": 3
        }
    }
    
    @classmethod
    def get_provider(cls, provider_name: str) -> BaseAIProvider:
        """
        Get AI provider instance.
        
        Args:
            provider_name: Name of provider (gemini, claude, groq)
        
        Returns:
            BaseAIProvider: Provider instance
        
        Raises:
            ValueError: If provider not found or not configured
        """
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        try:
            provider_class = cls._providers[provider_name]
            provider = provider_class()
            logger.info(
                "provider_initialized",
                provider=provider_name,
                model=provider.model_name
            )
            return provider
        except ValueError as e:
            logger.error(
                "provider_initialization_failed",
                provider=provider_name,
                error=str(e)
            )
            raise
    
    @classmethod
    def get_best_provider(cls, prefer_free: bool = True, exclude: list[str] = None) -> str:
        """
        Get the best available provider based on preferences.
        
        Args:
            prefer_free: Prefer free providers over paid ones
            exclude: List of provider names to exclude
            
        Returns:
            str: Name of the best provider
        """
        exclude = exclude or []
        available_providers = [p for p in cls._fallback_order if p not in exclude]
        
        if not available_providers:
            raise ValueError("No providers available")
        
        if prefer_free:
            # Find first free provider
            for provider_name in available_providers:
                try:
                    provider = cls.get_provider(provider_name)
                    if provider.is_free:
                        logger.info(
                            "best_provider_selected",
                            provider=provider_name,
                            reason="free_and_available"
                        )
                        return provider_name
                except Exception:
                    continue
        
        # Return first available
        best = available_providers[0]
        logger.info(
            "best_provider_selected",
            provider=best,
            reason="first_available"
        )
        return best
    
    @classmethod
    def list_providers(cls) -> list[dict]:
        """
        List all available providers with metadata.
        
        Returns:
            list[dict]: List of provider information
        """
        providers = []
        for name in cls._fallback_order:
            metadata = cls._provider_metadata.get(name, {})
            try:
                provider = cls.get_provider(name)
                is_free = provider.is_free
                providers.append({
                    "name": name,
                    "display_name": metadata.get("display_name", name),
                    "available": True,
                    "is_free": is_free,
                    "cost_tier": provider.cost_tier,
                    "cost_label": "FREE 🆓" if is_free else "PAID 💰",
                    "model_name": provider.model_name,
                    "priority": metadata.get("priority", 999)
                })
            except Exception:
                is_free = metadata.get("is_free", False)
                providers.append({
                    "name": name,
                    "display_name": metadata.get("display_name", name),
                    "available": False,
                    "is_free": is_free,
                    "cost_tier": metadata.get("cost_tier", "unknown"),
                    "cost_label": "FREE 🆓" if is_free else "PAID 💰",
                    "model_name": "N/A",
                    "priority": metadata.get("priority", 999)
                })
        
        return providers
    
    @staticmethod
    async def process_text(
        text: str,
        task: str,
        provider_name: str = "gemini",
        language: Optional[str] = None
    ) -> dict:
        """
        Process text using AI (correction, formatting, etc.).
        
        Args:
            text: Text to process
            task: Type of processing (correct_spelling, add_punctuation, etc.)
            provider_name: AI provider to use
            language: Language code (e.g., 'fr', 'en')
        
        Returns:
            dict: Processing results
        """
        logger.info(
            "text_processing_start",
            task=task,
            provider=provider_name,
            text_length=len(text),
            language=language
        )
        
        # Get provider
        service = AIAssistantService()
        provider = service.get_provider(provider_name)
        
        # Build prompt based on task
        prompts = {
            "correct_spelling": f"""Corrige UNIQUEMENT les fautes d'orthographe dans ce texte {f'en {language}' if language else ''}. 
Ne change PAS la structure, ne reformule PAS, ne modifie PAS le style.

NE REFORMULE PAS, ne change pas les mots, ne change pas l'ordre des phrases.
N'ajoute aucun mot.
N'ajoute aucune introduction ni conclusion.

Retourne SEULEMENT le texte corrigé, sans commentaire ni explication.

       EXECUTION PROTOCOL — OBLIGATOIRE

       0. Style : Style simple, direct, neutre, sans poésie, sans embellissement, sans formulations nobles, sans ton inspiré ou spirituel.

       1. Réécriture : Réécrire uniquement pour clarifier, pas pour embellir.

       2. Vocabulaire interdit : Interdits : "profondément", "authentique", "véritable", "éloquents", "jardins éternels", "foyer véritable", "épanouissement", tous mots littéraires ou poétiques.

       3. Structure :
          - Pas de titres ajoutés
          - Pas d'introduction
          - Pas de conclusion
          - Pas de transitions embellies

       4. Fidélité :
          - Interdiction d'inventer une idée
          - Interdiction de changer le ton
          - Interdiction d'ajouter des émotions

       5. Output :
          - UNIQUEMENT le texte restructuré
          - Aucun commentaire
          - Aucun ajout
          - Aucun titre
          - Aucune phrase hors du texte source

       Si une règle entre en conflit avec une tendance stylistique du modèle, les règles priment.

       Texte à corriger:
       {text}""",
            
            "add_punctuation": f"""Ajoute la ponctuation manquante dans ce texte {f'en {language}' if language else ''}.
Ajoute les points, virgules, points d'exclamation, etc.
Ne change PAS le contenu, ne reformule PAS.

NE REFORMULE PAS, ne change pas les mots, ne change pas l'ordre des phrases.
N'ajoute aucun mot.
N'ajoute aucune introduction ni conclusion.

Retourne SEULEMENT le texte avec ponctuation, sans commentaire.

STRICT MODE — OBLIGATOIRE
Applique une réécriture minimaliste du texte selon les règles suivantes :

R1. Pas de poésie, pas d'embellissement, pas de mots nobles, pas de formulations "belles".
R2. Remplacer tout vocabulaire abstrait, noble ou spirituel par des formulations simples.
R3. Interdiction d'ajouter des émotions, des intentions divines, des jugements, des conclusions ou des intensifications.
R4. Interdiction d'ajouter une introduction, une conclusion, un titre ou une phrase hors du texte.
R5. Interdiction d'augmenter la force émotionnelle ou spirituelle du texte.
R6. Interdiction d'ajouter des synonymes plus "élevés" (ex : "plénitude", "véritable demeure", "félicité").
R7. Le style doit rester neutre, simple, concret.
R8. Si une phrase est claire, réécris-la presque à l'identique.
R9. Si tu dois reformuler, reste au niveau de vocabulaire d'un article simple, sans termes religieux sophistiqués.
R10. Tout le texte doit rester strict, factuel, sobre.

Résultat attendu : une version simple, directe, sans amplification littéraire, sans vocabulaire noble, sans poésie, sans envolées spirituelles.

Texte:
{text}""",
            
            "format_paragraphs": f"""Formate ce texte {f'en {language}' if language else ''} en paragraphes cohérents.
Ajoute des sauts de ligne où nécessaire.
Ne change PAS le contenu, ne reformule PAS.

NE REFORMULE PAS, ne change pas les mots, ne change pas l'ordre du texte.
N'ajoute aucune phrase.
N'ajoute aucune introduction ni conclusion.

Retourne SEULEMENT le texte formaté, sans commentaire.

STRICT MODE — OBLIGATOIRE
Applique une réécriture minimaliste du texte selon les règles suivantes :

R1. Pas de poésie, pas d'embellissement, pas de mots nobles, pas de formulations "belles".
R2. Remplacer tout vocabulaire abstrait, noble ou spirituel par des formulations simples.
R3. Interdiction d'ajouter des émotions, des intentions divines, des jugements, des conclusions ou des intensifications.
R4. Interdiction d'ajouter une introduction, une conclusion, un titre ou une phrase hors du texte.
R5. Interdiction d'augmenter la force émotionnelle ou spirituelle du texte.
R6. Interdiction d'ajouter des synonymes plus "élevés" (ex : "plénitude", "véritable demeure", "félicité").
R7. Le style doit rester neutre, simple, concret.
R8. Si une phrase est claire, réécris-la presque à l'identique.
R9. Si tu dois reformuler, reste au niveau de vocabulaire d'un article simple, sans termes religieux sophistiqués.
R10. Tout le texte doit rester strict, factuel, sobre.

Résultat attendu : une version simple, directe, sans amplification littéraire, sans vocabulaire noble, sans poésie, sans envolées spirituelles.

Texte:
{text}""",
            
            "improve_quality": f"""Tu es un expert en transcription {f'en langue {language}' if language else ''}. 
Améliore cette transcription audio en appliquant ces corrections :

1. **Orthographe** : Corrige TOUTES les fautes (ex: "lettres humain" → "l'être humain")
2. **Ponctuation** : Ajoute points, virgules, deux-points, guillemets
3. **Majuscules** : Début de phrases, noms propres (Allah, Prophète)
4. **Formatage** : Sépare en paragraphes logiques (tous les 3-4 phrases)
5. **Cohérence** : Vérifie que le texte a du sens

RÈGLES STRICTES :
- NE CHANGE PAS le sens original
- NE REFORMULE PAS les phrases
- NE SUPPRIME AUCUNE information
- N'ajoute aucune introduction ni conclusion
- Retourne UNIQUEMENT le texte amélioré, sans commentaire ni explication

STRICT MODE — OBLIGATOIRE
Applique une réécriture minimaliste du texte selon les règles suivantes :

R1. Pas de poésie, pas d'embellissement, pas de mots nobles, pas de formulations "belles".
R2. Remplacer tout vocabulaire abstrait, noble ou spirituel par des formulations simples.
R3. Interdiction d'ajouter des émotions, des intentions divines, des jugements, des conclusions ou des intensifications.
R4. Interdiction d'ajouter une introduction, une conclusion, un titre ou une phrase hors du texte.
R5. Interdiction d'augmenter la force émotionnelle ou spirituelle du texte.
R6. Interdiction d'ajouter des synonymes plus "élevés" (ex : "plénitude", "véritable demeure", "félicité").
R7. Le style doit rester neutre, simple, concret.
R8. Si une phrase est claire, réécris-la presque à l'identique.
R9. Si tu dois reformuler, reste au niveau de vocabulaire d'un article simple, sans termes religieux sophistiqués.
R10. Tout le texte doit rester strict, factuel, sobre.

Résultat attendu : une version simple, directe, sans amplification littéraire, sans vocabulaire noble, sans poésie, sans envolées spirituelles.

Transcription à améliorer:
{text}

Texte amélioré:""",
            
            "translate": f"""Traduis ce texte vers {language if language else 'anglais'}.

N'ajoute rien. Traduis uniquement. Aucun ajout, aucune reformulation personnelle.
N'ajoute aucune introduction ni conclusion.

Retourne SEULEMENT la traduction, sans commentaire.

STRICT MODE — OBLIGATOIRE
Applique une réécriture minimaliste du texte selon les règles suivantes :

R1. Pas de poésie, pas d'embellissement, pas de mots nobles, pas de formulations "belles".
R2. Remplacer tout vocabulaire abstrait, noble ou spirituel par des formulations simples.
R3. Interdiction d'ajouter des émotions, des intentions divines, des jugements, des conclusions ou des intensifications.
R4. Interdiction d'ajouter une introduction, une conclusion, un titre ou une phrase hors du texte.
R5. Interdiction d'augmenter la force émotionnelle ou spirituelle du texte.
R6. Interdiction d'ajouter des synonymes plus "élevés" (ex : "plénitude", "véritable demeure", "félicité").
R7. Le style doit rester neutre, simple, concret.
R8. Si une phrase est claire, réécris-la presque à l'identique.
R9. Si tu dois reformuler, reste au niveau de vocabulaire d'un article simple, sans termes religieux sophistiqués.
R10. Tout le texte doit rester strict, factuel, sobre.

Résultat attendu : une version simple, directe, sans amplification littéraire, sans vocabulaire noble, sans poésie, sans envolées spirituelles.

Texte:
{text}""",
            
            "format_text": f"""Tu es un expert en restructuration de contenu {f'en langue {language}' if language else ''}.

Ta mission : transformer cette transcription brute en un contenu professionnel, fluide et engageant, tout en préservant l'intégrité de l'information.

OBJECTIFS DE RESTRUCTURATION :

1. **Correction linguistique** :
   - Corrige toutes les erreurs de transcription automatique
   - Améliore la grammaire, l'orthographe et la syntaxe
   - Utilise un vocabulaire précis et approprié au contexte

2. **Structure narrative** :
   - Organise le contenu en sections logiques avec des transitions fluides
   - Crée des paragraphes cohérents (3-5 phrases chacun)
   - Ajoute des titres de section si le contenu s'y prête naturellement

3. **Enrichissement contextuel** (maximum +50% de volume) :
   - Développe les concepts mentionnés de manière naturelle
   - Ajoute des clarifications uniquement si elles sont évidentes dans le contexte
   - Explicite les liens logiques entre les idées
   - Renforce la cohérence narrative

4. **Humanisation du style** :
   - Transforme le style oral brut en prose écrite naturelle
   - Élimine les répétitions inutiles tout en gardant les emphases importantes
   - Maintiens le ton et l'intention originale du discours
   - Préserve les expressions idiomatiques et culturelles
   - Reste sobre : pas de lyrisme, pas de dramatisation, pas d'effets littéraires inutiles

LIGNE ÉDITORIALE UNIVERSELLE :
Analyse le texte en profondeur et reformule-le avec précision. Améliore sa clarté, sa cohérence et son organisation sans dénaturer son sens ni son intention. Enrichis intelligemment les idées en ajoutant des explications utiles, des nuances pertinentes et des clarifications contextuelles, mais ne crée jamais de contenu imaginaire ou incompatible avec le sujet.

Adopte un ton équilibré : humain mais professionnel, riche mais maîtrisé, profond mais sans exagération. Évite les effets littéraires excessifs ou les formulations trop décoratives. La structure doit être fluide, logique et naturelle — jamais forcée ou académique.

Respecte rigoureusement l'esprit, la culture et le registre du texte : si le texte est émotionnel, garde cette chaleur ; s'il est scientifique, reste factuel ; s'il est philosophique, approfondis sans dériver. Ne projette pas de croyances ou de conclusions extérieures au texte.

PRÉCISION POUR TEXTES SENSIBLES :
Lorsque le texte traite d'un sujet religieux, scientifique, culturel ou historique, ne modifie jamais les fondements, les concepts ou les citations. Ne romantise pas, ne dramatise pas, n'ajoute pas d'affirmations non sourcées. Enrichissement autorisé : explications, contexte, clarifications pédagogiques. Enrichissement interdit : inventions, interprétations personnelles, extensions doctrinales ou embellissements émotionnels. Lorsque tu présentes une explication, distingue clairement ce qui vient du texte et ce qui est une mise en contexte neutre.

RÈGLES ABSOLUES :
- ✅ FIDÉLITÉ : Conserve 100% des informations factuelles
- ✅ AUTHENTICITÉ : N'invente AUCUNE information, citation ou référence
- ✅ CONTEXTE : Adapte la structure au type de contenu détecté (éducatif, narratif, argumentatif, etc.)
- ✅ VOLUME : Maximum +50% de longueur par rapport à l'original
- ✅ PROFONDEUR : Le résultat final doit être fidèle au message, mieux expliqué, mieux organisé, plus lisible, plus cohérent, plus profond
- ✅ SOBRIÉTÉ : La précision prime sur la beauté littéraire
- ❌ INTERDICTIONS : Pas de résumé, pas d'omission, pas d'invention, pas de commentaire méta, pas de décoration littéraire excessive
- ❌ N'ajoute aucune introduction ni conclusion globale

FORMAT DE SORTIE :
Retourne UNIQUEMENT le contenu restructuré, sans introduction, sans conclusion ajoutée, sans commentaire sur le travail effectué.

STRICT MODE — OBLIGATOIRE
Applique une réécriture minimaliste du texte selon les règles suivantes :

R1. Pas de poésie, pas d'embellissement, pas de mots nobles, pas de formulations "belles".
R2. Remplacer tout vocabulaire abstrait, noble ou spirituel par des formulations simples.
R3. Interdiction d'ajouter des émotions, des intentions divines, des jugements, des conclusions ou des intensifications.
R4. Interdiction d'ajouter une introduction, une conclusion, un titre ou une phrase hors du texte.
R5. Interdiction d'augmenter la force émotionnelle ou spirituelle du texte.
R6. Interdiction d'ajouter des synonymes plus "élevés" (ex : "plénitude", "véritable demeure", "félicité", "organe", "marques", "indicateurs clairs", "aspire", "élévation").
R7. Le style doit rester neutre, simple, concret.
R8. Si une phrase est claire, réécris-la presque à l'identique.
R9. Si tu dois reformuler, reste au niveau de vocabulaire d'un article simple, sans termes religieux sophistiqués.
R10. Tout le texte doit rester strict, factuel, sobre.

Résultat attendu : une version simple, directe, sans amplification littéraire, sans vocabulaire noble, sans poésie, sans envolées spirituelles.

Transcription brute à restructurer :
{text}

Contenu restructuré :"""
        }
        
        prompt = prompts.get(task, prompts["improve_quality"])
        
        # Process with AI
        try:
            processed_text = await provider.complete(prompt)
            
            logger.info(
                "text_processing_success",
                task=task,
                provider=provider_name,
                original_length=len(text),
                processed_length=len(processed_text)
            )
            
            return {
                "original_text": text,
                "processed_text": processed_text.strip(),
                "provider_used": provider_name,
                "task_performed": task,
                "improvements": [f"Processed with {provider.model_name}"]
            }
            
        except Exception as e:
            logger.error(
                "text_processing_error",
                task=task,
                provider=provider_name,
                error=str(e)
            )
            raise
    
    @staticmethod
    async def process_text_smart(
        db: AsyncSession,
        text: str,
        task: str,
        language: Optional[str] = None,
        metadata: Optional[Dict] = None,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        provider_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        🆕 NOUVELLE MÉTHODE : Traitement intelligent avec Router IA.
        
        Utilisable par TOUS les modules du SaaS (transcription, markdown, etc.).
        
        Pipeline complet :
        1. Classification du contenu (0€, <50ms) - domaine, ton, sensibilité
        2. Sélection du modèle optimal (0€) - selon stratégie et contexte
        3. Sélection du prompt adapté (0€) - strict/standard/creative
        4. Traitement avec le provider sélectionné (coût IA)
        
        Args:
            db: Database session
            text: Text to process
            task: Task name (format_text, improve_quality, translate, etc.)
            language: Language code (french, english, arabic)
            metadata: Optional metadata (title, source, uploader, etc.)
            strategy: Selection strategy (CONSERVATIVE, BALANCED, COST_OPTIMIZED)
            provider_override: Force specific provider (bypasses router)
        
        Returns:
            {
                "original_text": "...",
                "processed_text": "...",
                "provider_used": "groq",
                "task_performed": "format_text",
                "improvements": [...],
                "classification": {
                    "primary_domain": "religious",
                    "confidence": 0.85,
                    "sensitivity": {...},
                    ...
                },
                "model_selection": {
                    "model": "groq",
                    "strategy_used": "balanced",
                    "reason": "...",
                    ...
                },
                "prompt_config": {
                    "profile": "strict",
                    "use_strict_mode": True,
                    ...
                },
                "total_processing_time_ms": 1234
            }
        
        Example:
            # Transcription YouTube religieuse
            result = await AIAssistantService.process_text_smart(
                db=db,
                text=transcription_text,
                task="format_text",
                language="french",
                metadata={"title": "Rappel sur la patience", "uploader": "Cheikh..."},
                strategy=SelectionStrategy.BALANCED
            )
            
            # Le router détectera automatiquement :
            # - Domaine: religious
            # - Sensibilité: high
            # - Modèle: groq (conservateur pour contenu religieux)
            # - Prompt: strict mode
        """
        start_time = datetime.utcnow()
        
        # 1. Classification du contenu (0€, <50ms)
        classification = ContentClassifier.classify(
            text=text,
            language=language or "french",
            metadata=metadata
        )
        
        logger.info(
            "content_classified",
            domain=classification["primary_domain"],
            confidence=classification["confidence"],
            sensitivity=classification["sensitivity"]["level"],
            is_mixed=classification["is_mixed_content"],
            processing_time_ms=classification["processing_time_ms"]
        )
        
        # 2. Sélection du modèle (0€)
        model_selection = ModelSelector.select_model(
            classification=classification,
            strategy=strategy,
            override=provider_override
        )
        
        provider_name = model_selection["model"]
        
        logger.info(
            "model_selected",
            model=provider_name,
            strategy=model_selection["strategy_used"],
            fallback=model_selection["fallback_used"],
            reason=model_selection["reason"]
        )
        
        # 3. Sélection du prompt (0€)
        prompt_config = PromptSelector.select_prompt(
            classification=classification,
            task=task,
            model=provider_name
        )
        
        logger.info(
            "prompt_selected",
            profile=prompt_config["profile"],
            task=task,
            strict_mode=prompt_config["use_strict_mode"],
            constraints_count=len(prompt_config["additional_constraints"])
        )
        
        # 4. Traitement avec le provider sélectionné (coût IA)
        # Note: La méthode process_text existante gère déjà les prompts STRICT MODE
        result = await AIAssistantService.process_text(
            db=db,
            text=text,
            task=task,
            provider=provider_name,
            language=language
        )
        
        # Enrichir le résultat avec les infos de classification
        result["classification"] = classification
        result["model_selection"] = model_selection
        result["prompt_config"] = prompt_config
        result["total_processing_time_ms"] = (
            datetime.utcnow() - start_time
        ).total_seconds() * 1000
        
        logger.info(
            "smart_processing_complete",
            domain=classification["primary_domain"],
            model=provider_name,
            strategy=model_selection["strategy_used"],
            total_time_ms=result["total_processing_time_ms"]
        )
        
        return result

