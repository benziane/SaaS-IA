---
name: ai-provider
description: |
  Skill pour l'integration et la gestion des providers IA du projet SaaS-IA.
  TRIGGER quand: ajout/modification d'un provider IA, travail avec Gemini, Claude,
  Groq, OpenAI, AssemblyAI, ou tout code dans app/ai_assistant/.
---

# Integration Providers IA

## Architecture existante

Le systeme utilise un **AI Router** dans `mvp/backend/app/ai_assistant/` qui:
1. Classifie la requete utilisateur
2. Selectionne le provider optimal
3. Route vers le provider choisi
4. Track les couts via le module `cost_tracker`

## Providers configures
| Provider | Cle config | Usage principal |
|----------|-----------|-----------------|
| Gemini | `GEMINI_API_KEY` | Flash 2.0 - usage general |
| Claude | `CLAUDE_API_KEY` | Sonnet - raisonnement |
| Groq | `GROQ_API_KEY` | Llama 3.3 70B - rapide |
| OpenAI | `OPENAI_API_KEY` | GPT - polyvalent, TTS, DALL-E |
| AssemblyAI | `ASSEMBLYAI_API_KEY` | Transcription audio |
| ElevenLabs | `ELEVENLABS_API_KEY` | Voice clone + TTS premium |

## LiteLLM Proxy (integre)

`mvp/backend/app/ai_assistant/litellm_proxy.py` fournit un proxy unifie :
- **Routing intelligent** : selectionne le provider optimal (cout/qualite)
- **Comptage tokens** : calcul auto via LiteLLM (remplace pricing manuel)
- **Fallback chain** : Gemini → Groq → Claude → OpenAI
- **Cost tracking** : integration auto avec `cost_tracker`

```python
from app.ai_assistant.litellm_proxy import LiteLLMProxy

proxy = LiteLLMProxy()
response = await proxy.completion(
    messages=[{"role": "user", "content": prompt}],
    model="gemini/gemini-2.0-flash",
    fallbacks=["groq/llama-3.3-70b", "claude-3-sonnet"]
)
```

## Patterns obligatoires

### Nouveau provider
```python
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        ...

    @abstractmethod
    async def stream(self, prompt: str, **kwargs):
        """Yield des chunks pour le streaming SSE."""
        ...

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        ...
```

### Gestion d'erreurs et fallback
```python
async def generate_with_fallback(prompt: str, providers: list[str]) -> str:
    for provider_name in providers:
        try:
            provider = get_provider(provider_name)
            return await provider.generate(prompt)
        except ProviderError as e:
            logger.warning("provider_failed", provider=provider_name, error=str(e))
            continue
    raise HTTPException(status_code=503, detail="All AI providers unavailable")
```

### Tracking des couts
Toujours enregistrer l'utilisation via le module `cost_tracker`:
```python
await cost_tracker.record_usage(
    user_id=current_user.id,
    provider=provider_name,
    input_tokens=usage.input_tokens,
    output_tokens=usage.output_tokens,
    cost=provider.estimate_cost(usage.input_tokens, usage.output_tokens),
)
```

## Regles

1. **Interface commune** - tous les providers implementent la meme interface
2. **Streaming SSE** - supporter le streaming pour les reponses longues
3. **Fallback automatique** - si un provider echoue, essayer le suivant
4. **Cost tracking** - toujours enregistrer les couts
5. **Rate limiting par provider** - respecter les limites de chaque API
6. **Tests avec mocks** - jamais d'appels reels aux APIs en test
7. **Cles dans .env** - jamais de cle API en dur
