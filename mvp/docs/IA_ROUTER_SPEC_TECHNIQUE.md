
# Spécification Technique — Router IA Interne & Sélection Automatique de Modèle

## 1. Contexte et Problème

Le SaaS (WeLAB / plate-forme IA interne) utilise plusieurs modèles d’IA externes (Gemini Flash, Gemini Pro, GPT-4.x, Claude, Groq, etc.) pour des tâches variées :
- Transcription et restructuration de textes (YouTube, audio, documents)
- Analyse de contenus techniques (télécom, code, infra)
- Reformulation, correction, enrichissement éditorial
- Résumés, documentation, assistance métier, etc.

Constat :
- Certains modèles ont un **style interne très marqué** (ex. Gemini Flash : ton littéraire, inspiré, amplifié).
- Pour des contenus **sensibles** (religieux, scientifiques, juridiques, techniques), ce style cause :
  - Embellissement non souhaité
  - Romantisation du discours
  - Ajout de formulations interprétatives
  - Écart par rapport à la sobriété demandée

Les prompts ont déjà été renforcés (règles strictes, “STRICT MODE”, interdictions explicites), mais :
- Le modèle **continue à influer fortement par son style pré-entraîné**.
- On observe une limite structurelle côté modèle, pas seulement côté prompt.

Problème métier :
- On ne peut pas envoyer aveuglément tous les contenus au même modèle.
- On doit **choisir intelligemment le modèle IA selon le contexte** du texte.

Contraintes :
- La **détection du contexte** (religieux, scientifique, etc.) ne doit **pas utiliser de jetons IA externes**.
- Cette détection doit être :
  - Interne
  - Rapide
  - Peu coûteuse
  - Standardisée pour tous les modules IA du SaaS.

---

## 2. Objectifs du Router IA Interne

Construire un composant interne “Router IA” qui, pour chaque contenu à traiter, réalise en amont :

1. **Analyse du texte brut** (et métadonnées éventuelles)
2. **Classification du domaine** (religieux, scientifique, technique, administratif, narratif, général…)
3. **Analyse du ton** (populaire, neutre, académique, formel, sensible…)
4. **Sélection automatique du modèle IA** le plus adapté (Gemini Pro, Flash, GPT-4.x, Claude, Groq…)
5. **Sélection du profil de tâche / prompt** adapté (restructuration stricte, correction simple, traduction, etc.)

Le tout :
- Sans appel à une IA externe pour cette phase de classification.
- Avec une architecture extensible (ajout de nouveaux domaines, modèles, règles).

---

## 3. Exigences Fonctionnelles

### 3.1. Entrées du Router IA

Pour chaque requête IA (par exemple : restructurer une transcription YouTube), le Router reçoit :

- `text` : contenu texte brut (obligatoire)
- Métadonnées (optionnel mais recommandé) :
  - `title` (ex : titre de la vidéo YouTube)
  - `uploader` / `source`
  - `language` (ex : `fr`, `en`, `ar`)
  - `module` (ex : `youtube_transcription`, `markdown_viewer`, `telecom_analysis`, etc.)

### 3.2. Sorties du Router IA

Le Router retourne un objet structuré, par exemple :

```json
{
  "domain": "religious",
  "tone": "popular",
  "language": "fr",
  "confidence": 0.87,
  "recommended_model": "gemini-pro",
  "task_profile": "format_text_strict",
  "keywords_found": ["allah", "prophète", "hadith"]
}
```

Ce résultat permet ensuite :
- de sélectionner le bon **provider IA / modèle**, 
- de choisir le **prompt / profil de tâche** adapté.

### 3.3. Domaines à gérer en priorité

- **Religious** : textes religieux, prêches, rappels, citations de textes sacrés.
- **Scientific** : contenus scientifiques, analyses, hypothèses, résultats d’études.
- **Technical** : textes techniques (code, infra, réseaux, télécom, API, etc.).
- **Administrative** : contenus administratifs, formulaires, procédures, règlements.
- **Narrative** : récits, histoires, contenu littéraire, témoignages.
- **General** : tout ce qui ne rentre pas clairement dans les catégories ci-dessus.

### 3.4. Ton du texte

- **Popular** : style conversationnel, tutoiement, expressions familières, adressé au grand public.
- **Neutral** : ton standard, informatif, sans marque d’émotion forte.
- **Academic** : structure argumentative, références, connecteurs logiques (“en effet”, “par conséquent”).
- **Formal** : style administratif, légal, institutionnel.
- **Sensitive** : texte évoquant des sujets sensibles (religion, deuil, santé, etc.) détecté via mots-clés ou contexte.

---

## 4. Approche Technique – Solutions Envisagées

### 4.1. Solution A — Classification par Règles (Heuristiques)

Principe :
- Utiliser des **listes de mots-clés** et des **patterns** pour identifier :
  - le **domaine** (religieux, scientifique, etc.)
  - le **ton** (populaire, académique, etc.).

Caractéristiques :
- 0 € de coût (aucun appel IA externe)
- Implémentation rapide (2–4h pour un premier jet)
- Maintenance facile (ajout/suppression de mots-clés)
- Transparence et débogage faciles (comportement explicite)

Exemples de mots-clés :

- Domaine **religieux** (FR) : `allah`, `prophète`, `hadith`, `coran`, `adoration`, `paradis`, `enfer`, `dhikr`, `astaghfirullah`, `paix soit sur lui`
- Domaine **scientifique** (FR) : `équation`, `modèle`, `protocole`, `résultat`, `données`, `expérience`, `hypothèse`
- Domaine **technique** (FR) : `serveur`, `api`, `framework`, `docker`, `json`, `base de données`, `requête`, `code`, `fonction`
- Domaine **administratif** (FR) : `procédure`, `formulaire`, `dossier`, `déclaration`, `registre`, `règlement`

Patterns pour le ton :
- **Academic** : présence de connecteurs et vocabulaire : `selon`, `d’après`, `conformément`, `étude`, `recherche`, `analyse`, `conclusion`, `notamment`, `en effet`, `par conséquent`.
- **Formal** : `veuillez`, `nous vous prions`, `conformément à`, `en vertu de`, `article`, `décret`.
- **Popular** : tutoiement (`tu`, `toi`, `ton`, `ta`), ponctuation expressive (`!!`), lexique familier.

Avantages :
- Simple, efficace pour 80–90% des cas.
- Parfait comme première version de mise en production.

Limites :
- Moins performant sur les textes ambigus.
- Nécessite une mise à jour régulière des mots-clés en fonction des retours terrain.

---

### 4.2. Solution B — Modèle Local Léger (FastText / TF-IDF / MiniLM)

Principe :
- Utiliser un **modèle de classification local**, entraîné sur un corpus interne.
- Pas d’appel API → pas de coût en jetons.

Options :
- **FastText** (Facebook) : classification de texte rapide.
- **TF-IDF + SVM / Logistic Regression** (scikit-learn) : classique et robuste.
- **MiniLM SentenceTransformer** (20–60 Mo) : embeddings + classifieur.

Avantages :
- Plus flexible que les règles simples.
- Peut apprendre à partir de nos propres données WeLAB.
- Facile à versionner, monitorer, améliorer.

Inconvénients :
- Nécessite un petit dataset d’entraînement labellisé.
- Complexité de mise en place plus élevée.

---

### 4.3. Solution C — Router Hybride (Règles + Modèle Local)

Principe :
- Combiner A + B :
  - Les **règles** font une première classification rapide.
  - Le **modèle local** valide ou corrige la classification.
- Sortir un score final + justification (mots-clés / features).

Avantages :
- Très robuste sur le long terme.
- Adaptable à tous les modules IA.
- Réduction des erreurs de classification dans les cas ambigus.

Inconvénients :
- Plus complexe à implémenter.
- Nécessite quelques itérations / entraînements.

---

## 5. Spécification du Composant `ContentClassifier` (Solution A — v1)

### 5.1. Interface

Fichier suggéré :
- `backend/app/ai_assistant/content_classifier.py`

Signature principale :

```python
class ContentClassifier:
    @classmethod
    def classify(cls, text: str, language: str = "french") -> Dict:
        ...
```

Retour attendu :

```python
{
    "domain": "religious",
    "tone": "popular",
    "confidence": 0.85,
    "recommended_model": "gpt-4",
    "keywords_found": ["allah", "prophète", "hadith"]
}
```

### 5.2. Enumérations

```python
from enum import Enum

class ContentDomain(str, Enum):
    RELIGIOUS = "religious"
    SCIENTIFIC = "scientific"
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"
    NARRATIVE = "narrative"
    GENERAL = "general"

class ContentTone(str, Enum):
    POPULAR = "popular"
    NEUTRAL = "neutral"
    ACADEMIC = "academic"
    FORMAL = "formal"
    SENSITIVE = "sensitive"

class AIModel(str, Enum):
    GEMINI_FLASH = "gemini-flash"
    GEMINI_PRO = "gemini-pro"
    GPT4 = "gpt-4"
    CLAUDE = "claude"
    GROQ = "groq"
```

### 5.3. Mots-clés et Patterns (exemple simplifié)

```python
DOMAIN_KEYWORDS = {
    ContentDomain.RELIGIOUS: {
        "french": ["allah", "prophète", "hadith", "coran", "islam", "musulman",
                   "prière", "adoration", "paradis", "enfer", "dhikr", "astaghfirullah"],
    },
    ContentDomain.SCIENTIFIC: {
        "french": ["équation", "modèle", "protocole", "expérience", "hypothèse",
                   "données", "analyse", "résultat"],
    },
    ContentDomain.TECHNICAL: {
        "french": ["serveur", "api", "framework", "docker", "json", "base de données",
                   "requête", "algorithme", "code", "backend", "frontend"],
    },
    ContentDomain.ADMINISTRATIVE: {
        "french": ["procédure", "formulaire", "dossier", "déclaration", "registre",
                   "règlement", "administration"],
    },
}
```

Patterns ton :

```python
TONE_PATTERNS = {
    ContentTone.ACADEMIC: [
        r"\b(selon|d'après|conformément à|en référence à)\b",
        r"\b(étude|recherche|analyse|conclusion)\b",
        r"\b(notamment|en effet|par conséquent|ainsi)\b"
    ],
    ContentTone.FORMAL: [
        r"\b(veuillez|nous vous prions|conformément|en vertu de)\b",
        r"\b(article|loi|règlement|décret)\b"
    ],
    ContentTone.POPULAR: [
        r"\b(tu|toi|ton|ta|tes)\b",
        r"[!]{2,}"
    ]
}
```

### 5.4. Mapping Domaine → Modèle recommandé

```python
MODEL_MAPPING = {
    ContentDomain.RELIGIOUS: AIModel.GPT4,
    ContentDomain.SCIENTIFIC: AIModel.GPT4,
    ContentDomain.TECHNICAL: AIModel.GPT4,
    ContentDomain.ADMINISTRATIVE: AIModel.GEMINI_PRO,
    ContentDomain.NARRATIVE: AIModel.GEMINI_FLASH,
    ContentDomain.GENERAL: AIModel.GEMINI_FLASH
}
```

---

## 6. Intégration dans le Service IA

### 6.1. Service `AIAssistantService`

Fichier suggéré :
- `backend/app/ai_assistant/service.py`

```python
from app.ai_assistant.content_classifier import ContentClassifier

class AIAssistantService:
    @staticmethod
    async def process_text_smart(
        db: AsyncSession,
        text: str,
        task: str,
        language: Optional[str] = None,
        provider_override: Optional[str] = None
    ) -> Dict[str, Any]:

        # 1. Classification interne (0€)
        classification = ContentClassifier.classify(text, language or "french")

        # 2. Choix du modèle (avec override possible)
        provider_name = provider_override or classification["recommended_model"]

        # 3. Ajustement du profil de tâche selon le domaine
        if classification["domain"] in ("religious", "scientific"):
            # Utiliser un prompt plus strict, sans embellissement
            task = "format_text_strict"

        # 4. Appel IA externe avec le bon modèle + prompt
        return await AIAssistantService.process_text(
            db=db,
            text=text,
            task=task,
            provider=provider_name,
            language=language
        )
```

### 6.2. Endpoint de test

```python
@router.post("/classify-content")
async def classify_content(data: Dict[str, str]):
    text = data.get("text", "")
    language = data.get("language", "french")
    classification = ContentClassifier.classify(text, language)
    return {"classification": classification}
```

---

## 7. Roadmap d’Implémentation

### Phase 1 — v1 (Solution A — Règles enrichies)
- Implémenter `ContentClassifier` avec DOMAIN_KEYWORDS + TONE_PATTERNS.
- Intégrer le router dans `AIAssistantService.process_text_smart`.
- Ajouter des logs pour monitorer :
  - domaine détecté
  - modèle choisi
  - confiance
- Tester sur un set de textes représentatifs :
  - religieux (FR)
  - scientifiques
  - techniques
  - administratifs
  - généraux

### Phase 2 — Améliorations
- Étendre les mots-clés (ajouter arabe, anglais, etc.).
- Ajouter des domaines spécifiques (médical, financier, juridique).
- Ajouter un flag `sensitive = True` si certains mots-clés apparaissent.

### Phase 3 — Option B/C (Modèle Local / Hybride)
- Si nécessaire, introduire un modèle de classification local pour améliorer la précision :
  - Collecte de dataset interne
  - Entraînement d’un modèle (FastText / TF-IDF / MiniLM)
  - Intégration à côté des règles (hybride).

---

## 8. Bénéfices Attendus

- **Réduction des coûts IA** : plus besoin de double appels pour la classification.
- **Standardisation** : même logique de décision pour tous les modules IA du SaaS.
- **Meilleure qualité éditoriale** : sélection du modèle cohérente avec le contexte.
- **Respect des contenus sensibles** : texte religieux / scientifique traité par des modèles plus sobres.
- **Évolutivité** : possibilité d’ajouter facilement de nouveaux modèles et de nouveaux domaines.

