# 🤖 AI Code Assistant - Auto-Correction Interne

## 🎯 Objectif

Système d'assistance IA pour **corriger automatiquement les bugs** et **améliorer la qualité du code** de ton SaaS en cours de développement.

**Usage** : Outil interne (pas un produit à vendre)

---

## 💡 Contexte & Problème Résolu

### Problème
- 🐛 Bugs détectés en production nécessitent intervention manuelle
- ⏱️ Temps perdu à débugger des erreurs simples
- 📉 Qualité du code variable selon la fatigue/pression
- 🔄 Refactoring manuel long et fastidieux
- 🏗️ Difficile de maintenir cohérence architecturale

### Solution
Système IA qui :
- ✅ Détecte et corrige automatiquement les bugs
- ✅ Analyse le code à chaque commit
- ✅ Valide le respect de l'architecture
- ✅ Suggère des améliorations continues
- ✅ Génère des tests automatiquement

---

## 🏗️ Architecture

```
app/ai/modules/code_assistant/
├── manifest.yaml                   # Configuration du module
├── __init__.py                     # Entry point
│
├── 📂 core/
│   ├── service.py                  # CodeAssistantService (orchestration)
│   ├── context_builder.py          # Construit contexte depuis project-map.json
│   └── config.py                   # Configuration
│
├── 📂 analyzers/                   # Analyseurs de code
│   ├── bug_analyzer.py             # Détecte bugs potentiels
│   ├── security_analyzer.py        # Scan vulnérabilités (SQL injection, XSS, etc.)
│   ├── performance_analyzer.py     # Détecte goulots d'étranglement
│   ├── architecture_validator.py   # Valide respect de l'architecture
│   └── code_quality_analyzer.py    # Code smells, complexité cyclomatique
│
├── 📂 fixers/                      # Générateurs de corrections
│   ├── auto_fixer.py               # Génère corrections automatiques
│   ├── pr_creator.py               # Crée PR GitHub avec le fix
│   ├── test_generator.py           # Génère tests unitaires
│   └── documentation_generator.py  # Génère docstrings
│
├── 📂 providers/                   # Providers IA
│   ├── base_provider.py            # Interface abstraite
│   ├── openai_provider.py          # GPT-4 (analyse profonde)
│   ├── claude_provider.py          # Claude (code review)
│   └── local_analyzer.py           # Outils locaux (pylint, mypy, ruff)
│
├── 📂 hooks/                       # Hooks système
│   ├── pre_commit_hook.py          # Analyse avant commit
│   ├── post_deploy_hook.py         # Validation après déploiement
│   ├── exception_handler.py        # Capture erreurs production
│   └── ci_integration.py           # Intégration CI/CD
│
├── 📂 models/                      # Modèles de données
│   ├── analysis_result.py          # Résultat d'analyse
│   ├── fix_suggestion.py           # Suggestion de correction
│   └── code_context.py             # Contexte du code
│
├── 📂 utils/
│   ├── ast_parser.py               # Parse AST Python
│   ├── diff_analyzer.py            # Analyse les diffs Git
│   └── metrics_calculator.py      # Calcule métriques (complexité, etc.)
│
├── routes.py                       # API endpoints (usage interne)
├── schemas.py                      # Pydantic schemas
└── README.md
```

---

## 🎯 Cas d'Usage Détaillés

### 1. 🚨 Auto-Healing System (Correction Auto en Production)

**Scénario** : Une erreur est levée en production

```python
# app/core/middleware/exception_handler.py

from app.ai.modules.code_assistant.core.service import CodeAssistantService
from app.ai.modules.code_assistant.fixers.pr_creator import PRCreator

@app.exception_handler(Exception)
async def auto_healing_handler(request: Request, exc: Exception):
    """
    Workflow:
    1. Capture l'exception complète
    2. Extrait le contexte (fichier, ligne, traceback)
    3. Charge le contexte projet depuis project-map.json
    4. Envoie à l'AI pour analyse
    5. AI génère un fix
    6. Crée une PR GitHub automatique
    7. Notifie le dev + log audit
    8. Retourne erreur gracieuse à l'utilisateur
    """
    
    # 1. Capture contexte complet
    error_context = {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
        "file_path": exc.__traceback__.tb_frame.f_code.co_filename,
        "line_number": exc.__traceback__.tb_lineno,
        "function_name": exc.__traceback__.tb_frame.f_code.co_name,
        
        # Contexte requête
        "request_url": str(request.url),
        "request_method": request.method,
        "user_id": getattr(request.state, "user_id", None),
        
        # Contexte système
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        
        # Variables locales au moment de l'erreur
        "local_vars": exc.__traceback__.tb_frame.f_locals
    }
    
    # 2. Charge contexte projet
    code_assistant = CodeAssistantService()
    project_context = code_assistant.load_project_context(
        file_path=error_context["file_path"]
    )
    
    # 3. Analyse avec AI
    analysis = await code_assistant.analyze_error(
        error_context=error_context,
        project_context=project_context
    )
    
    # 4. Génère un fix si l'AI est confiant
    if analysis.confidence > 0.85 and analysis.fix_available:
        fix = await code_assistant.generate_fix(analysis)
        
        # 5. Crée une PR GitHub
        pr_creator = PRCreator()
        pr_url = await pr_creator.create_fix_pr(
            branch_name=f"auto-fix/{{error_context['error_type']}}-{{datetime.utcnow().timestamp()}}",
            fix=fix,
            error_context=error_context,
            analysis=analysis
        )
        
        # 6. Notification
        await notify_dev(
            title=f"🤖 Auto-Fix créé: {{error_context['error_type']}}",
            message=f"PR créée automatiquement: {{pr_url}}",
            priority="medium"
        )
        
        # 7. Log audit
        await audit_log.log_auto_fix(
            error=error_context,
            analysis=analysis,
            fix=fix,
            pr_url=pr_url
        )
    else:
        # Pas assez confiant, crée juste une issue GitHub
        await github_service.create_bug_issue(
            title=f"🐛 {{error_context['error_type']}}: {{error_context['error_message'][:50]}}",
            body=format_issue_body(error_context, analysis)
        )
    
    # 8. Retourne erreur gracieuse
    return JSONResponse(
        status_code=500,
        content={
            "error": "Une erreur est survenue",
            "message": "Notre équipe a été notifiée et travaille sur une correction",
            "reference_id": error_context["timestamp"]
        }
    )
```

**Résultat** :
- ✅ Bug détecté automatiquement
- ✅ Fix généré en 5-10 secondes
- ✅ PR prête à review
- ✅ Dev notifié
- ✅ Utilisateur voit message gracieux

---

### 2. 🔍 Code Quality Guardian (Analyse Pre-Commit)

**Scénario** : Développeur essaie de commit du code

```python
# .git/hooks/pre-commit (ou via pre-commit framework)

#!/usr/bin/env python3

import sys
from app.ai.modules.code_assistant.core.service import CodeAssistantService
from app.ai.modules.code_assistant.analyzers.code_quality_analyzer import CodeQualityAnalyzer

async def pre_commit_analysis():
    """
    Workflow:
    1. Récupère les fichiers modifiés
    2. Analyse chaque fichier
    3. Détecte: bugs, security issues, architecture violations
    4. Bloque le commit si critique
    5. Affiche suggestions si warnings
    """
    
    # 1. Fichiers modifiés
    changed_files = git.get_staged_files()
    
    if not changed_files:
        print("✅ Aucun fichier à analyser")
        return 0
    
    print(f"🔍 Analyse de {{len(changed_files)}} fichier(s)....")
    
    # 2. Analyse
    code_assistant = CodeAssistantService()
    issues = {
        "critical": [],
        "warnings": [],
        "suggestions": []
    }
    
    for file_path in changed_files:
        # Skip non-Python files
        if not file_path.endswith('.py'):
            continue
        
        # Charge le contexte projet
        project_context = code_assistant.load_project_context(file_path)
        
        # Analyse multi-niveaux
        result = await code_assistant.analyze_file(
            file_path=file_path,
            project_context=project_context,
            checks=[
                "bugs",
                "security",
                "performance",
                "architecture",
                "code_quality"
            ]
        )
        
        # Catégorise les issues
        issues["critical"].extend(result.critical_issues)
        issues["warnings"].extend(result.warnings)
        issues["suggestions"].extend(result.suggestions)
    
    # 3. Affichage résultats
    if issues["critical"]:
        print("\n❌ COMMIT BLOQUÉ - Issues critiques détectées:\n")
        for issue in issues["critical"]:
            print(f"  ❌ {{issue.file}}:{{issue.line}}")
            print(f"     {{issue.type}}: {{issue.message}}")
            print(f"     💡 Fix suggéré: {{issue.suggested_fix}}\n")
        
        print("👉 Corrige ces issues avant de commit")
        return 1  # Bloque le commit
    
    if issues["warnings"]:
        print("\n⚠️  Warnings détectés (commit autorisé):\n")
        for warning in issues["warnings"]:
            print(f"  ⚠️  {{warning.file}}:{{warning.line}}")
            print(f"     {{warning.message}}")
            print(f"     💡 {{warning.suggestion}}\n")
    
    if issues["suggestions"]:
        print("\n💡 Suggestions d'amélioration:\n")
        for suggestion in issues["suggestions"]:
            print(f"  💡 {{suggestion.file}}:{{suggestion.line}}")
            print(f"     {{suggestion.message}}\n")
    
    if not issues["critical"] and not issues["warnings"] and not issues["suggestions"]:
        print("✅ Code parfait ! Aucune issue détectée")
    
    return 0  # Autorise le commit

if __name__ == "__main__":
    sys.exit(asyncio.run(pre_commit_analysis()))
```

**Exemple de sortie** :

```
🔍 Analyse de 3 fichier(s)...

❌ COMMIT BLOQUÉ - Issues critiques détectées:

  ❌ app/modules/transcription/service.py:45
     SQL Injection: Requête SQL construite avec f-string
     💡 Fix suggéré: Utilise des paramètres bindés:
        # Avant
        query = f"SELECT * FROM users WHERE id = {{user_id}}"
        # Après
        query = "SELECT * FROM users WHERE id = :user_id"
        result = session.execute(query, {{"user_id": user_id}})

  ❌ app/api/v1/auth.py:123
     Security: Mot de passe stocké sans hash
     💡 Fix suggéré: Utilise bcrypt ou passlib

👉 Corrige ces issues avant de commit
```

---

### 3. 🏗️ Architecture Validator

**Scénario** : Valide que le nouveau code respecte l'architecture définie

```python
# app/ai/modules/code_assistant/analyzers/architecture_validator.py

from app.ai.modules.code_assistant.core.context_builder import ContextBuilder

class ArchitectureValidator:
    def __init__(self):
        self.context_builder = ContextBuilder()
        self.project_map = self.context_builder.load_project_map()
    
    async def validate_changes(self, file_path: str, new_code: str) -> ValidationResult:
        """
        Valide que le code respecte l'architecture
        
        Checks:
        1. Module independence (pas de dépendances circulaires)
        2. Layered architecture (API → Service → Repository)
        3. Import rules (core ne dépend pas de modules)
        4. Naming conventions
        5. File placement (bon dossier selon le type)
        """
        
        violations = []
        
        # 1. Analyse des imports
        imports = self.extract_imports(new_code)
        
        # Trouve le module actuel
        current_module = self.find_module_for_file(file_path)
        
        # Vérifie dépendances autorisées
        for imp in imports:
            if not self.is_import_allowed(current_module, imp):
                violations.append({
                    "type": "forbidden_import",
                    "severity": "critical",
                    "message": f"Import non autorisé: {{imp}}",
                    "reason": f"Le module '{{current_module}}' ne peut pas dépendre de '{{imp}}'",
                    "suggestion": self.suggest_alternative_import(current_module, imp)
                })
        
        # 2. Vérifie dépendances circulaires
        if self.creates_circular_dependency(current_module, imports):
            violations.append({
                "type": "circular_dependency",
                "severity": "critical",
                "message": "Dépendance circulaire détectée",
                "cycle": self.find_dependency_cycle(current_module, imports)
            })
        
        # 3. Vérifie layered architecture
        layer_violations = self.check_layer_violations(file_path, imports)
        violations.extend(layer_violations)
        
        # 4. Vérifie naming conventions
        naming_violations = self.check_naming_conventions(file_path, new_code)
        violations.extend(naming_violations)
        
        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations
        )
    
    def is_import_allowed(self, current_module: str, import_path: str) -> bool:
        """
        Règles d'architecture:
        - app.core ne dépend de rien (sauf libs externes)
        - app.models ne dépend que de app.core
        - app.api dépend de app.services
        - app.services dépend de app.models + app.core
        - app.ai.modules peuvent dépendre de app.core + app.models
        - app.ai.modules NE PEUVENT PAS se dépendre entre eux
        """
        
        rules = {
            "app.core": [],  # Pas de dépendances internes
            "app.models": ["app.core"],
            "app.api": ["app.services", "app.schemas", "app.core"],
            "app.services": ["app.models", "app.core"],
            "app.ai.modules.*": ["app.core", "app.models"]  # Mais pas d'autres modules
        }
        
        # Implémentation de la logique...
        return True  # ou False
```

**Exemple d'utilisation** :

```python
# Dans le pre-commit hook

validator = ArchitectureValidator()

for file in changed_files:
    result = await validator.validate_changes(file, new_code)
    
    if not result.valid:
        print(f"\n❌ Violations d'architecture dans {{file}}:")
        for violation in result.violations:
            print(f"  • {{violation['message']}}")
            if 'suggestion' in violation:
                print(f"    💡 {{violation['suggestion']}}")
```

---

### 4. 🔄 Refactoring Assistant (Amélioration Continue)

**Scénario** : Analyse quotidienne automatique du codebase

```python
# app/ai/modules/code_assistant/tasks/daily_code_review.py

from celery import Task
from app.tasks.celery_app import celery_app

@celery_app.task(name="daily_code_review")
async def daily_code_review():
    """
    Tâche planifiée (2h du matin):
    1. Analyse tout le codebase
    2. Détecte code smells, duplications, complexité excessive
    3. Génère suggestions de refactoring
    4. Crée des issues GitHub avec les suggestions
    5. Calcule métriques de qualité (tendances)
    """
    
    code_assistant = CodeAssistantService()
    project_map = code_assistant.load_project_map()
    
    report = {
        "date": datetime.utcnow().isoformat(),
        "modules_analyzed": 0,
        "issues_found": [],
        "refactoring_opportunities": [],
        "metrics": {}
    }
    
    # Analyse chaque module
    for module in project_map["modules"]:
        print(f"🔍 Analyse du module: {{module['name']}}")
        
        module_analysis = await code_assistant.analyze_module(
            module_path=module["path"],
            files=module["files"],
            dependencies=module["dependencies"]
        )
        
        report["modules_analyzed"] += 1
        
        # Code smells
        if module_analysis.code_smells:
            for smell in module_analysis.code_smells:
                report["issues_found"].append({
                    "module": module["name"],
                    "type": "code_smell",
                    "file": smell.file,
                    "line": smell.line,
                    "smell": smell.type,  # "long_method", "god_class", etc.
                    "severity": smell.severity
                })
        
        # Duplication
        if module_analysis.duplications:
            for dup in module_analysis.duplications:
                report["issues_found"].append({
                    "module": module["name"],
                    "type": "duplication",
                    "files": dup.files,
                    "lines": dup.lines_duplicated,
                    "suggestion": "Extraire en fonction commune"
                })
        
        # Complexité excessive
        if module_analysis.complex_functions:
            for func in module_analysis.complex_functions:
                if func.cyclomatic_complexity > 10:
                    report["refactoring_opportunities"].append({
                        "module": module["name"],
                        "type": "high_complexity",
                        "file": func.file,
                        "function": func.name,
                        "complexity": func.cyclomatic_complexity,
                        "suggestion": await code_assistant.suggest_refactoring(func)
                    })
        
        # Métriques
        report["metrics"][module["name"]] = {
            "maintainability_index": module_analysis.maintainability_index,
            "test_coverage": module_analysis.test_coverage,
            "avg_complexity": module_analysis.avg_complexity,
            "code_smells_count": len(module_analysis.code_smells)
        }
    
    # Créer des issues GitHub pour les refactorings suggérés
    for opportunity in report["refactoring_opportunities"]:
        await create_refactoring_issue(opportunity)
    
    # Sauvegarde le rapport
    save_report(report)
    
    # Notifie l'équipe
    await notify_team(
        title="📊 Rapport de qualité de code quotidien",
        message=format_report_summary(report)
    )
    
    return report

async def create_refactoring_issue(opportunity: dict):
    """Crée une issue GitHub avec la suggestion"""
    
    issue_body = f"""
## 🔄 Opportunité de Refactoring

**Module**: {{opportunity['module']}}
**Type**: {{opportunity['type']}}
**Fichier**: {{opportunity['file']}}

### Problème
{opportunity['description']}

### Suggestion
{opportunity['suggestion']['description']}

### Code Avant
```python
{opportunity['suggestion']['before']}
```

### Code Après (suggéré)
```python
{opportunity['suggestion']['after']}
```

### Bénéfices
- Réduction complexité: {{opportunity['complexity']}} → {{opportunity['suggestion']['new_complexity']}}
- Meilleure testabilité
- Plus maintenable

### Effort Estimé
⏱️ {{opportunity['suggestion']['estimated_time']}} minutes

---
*Généré automatiquement par AI Code Assistant*
    """
    
    await github_service.create_issue(
        title=f"♻️ Refactoring: {{opportunity['function']}} ({{opportunity['module']}})",
        body=issue_body,
        labels=["refactoring", "ai-suggested", "low-priority"]
    )
```

**Exemple d'issue GitHub créée** :

```markdown
## 🔄 Opportunité de Refactoring

**Module**: transcription
**Type**: high_complexity
**Fichier**: app/ai/modules/transcription/service.py

### Problème
La fonction `process_transcription` a une complexité cyclomatique de 15 (seuil: 10).
Elle contient trop de branches if/else et gère plusieurs responsabilités.

### Suggestion
Extraire la logique de validation, de traitement et de sauvegarde en méthodes séparées.

### Code Avant
```python
async def process_transcription(self, job_id: str):
    job = await self.get_job(job_id)
    if not job:
        raise NotFound()
    if job.status != "pending":
        raise InvalidStatus()
    # ... 50 lignes de code avec 15 branches
```

### Code Après (suggéré)
```python
async def process_transcription(self, job_id: str):
    job = await self._validate_job(job_id)
    audio_file = await self._extract_audio(job.video_url)
    transcript = await self._transcribe_audio(audio_file)
    await self._save_transcript(job, transcript)

async def _validate_job(self, job_id: str) -> Job:
    # Validation logic
    pass

async def _extract_audio(self, video_url: str) -> AudioFile:
    # Extraction logic
    pass
# ... etc
```

### Bénéfices
- Réduction complexité: 15 → 4 par fonction
- Meilleure testabilité (chaque fonction testable séparément)
- Plus maintenable (responsabilités séparées)

### Effort Estimé
⏱️ 30 minutes

---
*Généré automatiquement par AI Code Assistant*
```

---

## 🔌 Intégration avec project-map.json

**Le fichier project-map.json est ESSENTIEL pour le Code Assistant !**

### Pourquoi ?

```python
# app/ai/modules/code_assistant/core/context_builder.py

class ContextBuilder:
    """
    Construit le contexte riche pour l'AI depuis project-map.json
    """
    
    def __init__(self):
        with open("project-map.json") as f:
            self.project_map = json.load(f)
    
    def build_context_for_error(self, file_path: str, error: Exception) -> str:
        """
        Construit un contexte détaillé pour l'AI
        
        Le project-map.json permet de savoir:
        1. Dans quel module se trouve le fichier
        2. Quelles sont ses dépendances
        3. Quelle est l'architecture globale
        4. Quels autres fichiers sont liés
        """
        
        # 1. Trouve le module
        module = self.find_module_for_file(file_path)
        
        # 2. Charge les dépendances
        dependencies = module["dependencies"]
        
        # 3. Charge les fichiers liés
        related_files = self.find_related_files(file_path, module)
        
        # 4. Construit le prompt pour l'AI
        context = f"""
# Contexte du Projet

## Projet: {{self.project_map['project']['name']}}
Version: {{self.project_map['project']['version']}}

## Module Actuel: {{module['name']}}
Type: {{module['type']}}
Path: {{module['path']}}

## Fichier avec Erreur
Path: {{file_path}}
Exports: {{self.get_file_exports(file_path)}}
Imports: {{self.get_file_imports(file_path)}}

## Dépendances du Module
Internes:
{{self.format_dependencies(dependencies['internal'])}}

Externes:
{{self.format_dependencies(dependencies['external'])}}

## Architecture Globale
{{self.get_architecture_summary()}}

## Fichiers Liés (contexte)
{{self.format_related_files(related_files)}}

## Erreur
Type: {{type(error).__name__}}
Message: {{str(error)}}
Traceback: {{traceback.format_exc()}}

## Règles d'Architecture à Respecter
{{self.get_architecture_rules(module)}}

---

Analyse l'erreur et propose une correction qui:
1. Corrige le bug
2. Respecte l'architecture du projet
3. Ne casse pas les dépendances existantes
4. Suit les conventions de code du projet
        """
        
        return context
    
    def find_module_for_file(self, file_path: str) -> dict:
        """Trouve le module qui contient ce fichier"""
        for module in self.project_map["modules"]:
            if file_path.startswith(module["path"]):
                return module
        return None
    
    def find_related_files(self, file_path: str, module: dict) -> list:
        """
        Trouve les fichiers liés (imports/exports)
        Utilise le project-map pour tracer les dépendances
        """
        related = []
        
        current_file = next(
            (f for f in module["files"] if f["path"] == file_path),
            None
        )
        
        if not current_file:
            return []
        
        # Fichiers qui importent ce fichier
        for file in module["files"]:
            if any(imp in current_file["exports"] for imp in file["imports"]):
                related.append(file)
        
        # Fichiers importés par ce fichier
        for imp in current_file["imports"]:
            for file in module["files"]:
                if imp in file["exports"]:
                    related.append(file)
        
        return related
```

### Exemple de Contexte Généré pour l'AI

```
# Contexte du Projet

## Projet: SaaS-IA
Version: 1.0.0

## Module Actuel: transcription
Type: ai_module
Path: app/ai/modules/transcription

## Fichier avec Erreur
Path: app/ai/modules/transcription/service.py
Exports: ['TranscriptionService', 'process_video']
Imports: ['assemblyai', 'app.core.cache', 'app.models.transcription']

## Dépendances du Module
Internes:
- app.core.cache (CacheService)
- app.core.database (get_session)
- app.models.transcription (Transcription, TranscriptionJob)

Externes:
- assemblyai==1.2.3 (Transcription API)
- yt-dlp==2024.1.1 (YouTube download)
- language-tool-python==2.8 (Correction orthographe)

## Architecture Globale
Le projet suit une architecture modulaire avec:
- Core layer (infrastructure)
- AI modules layer (services IA indépendants)
- API layer (REST endpoints)

Règle: Les modules IA ne peuvent PAS dépendre entre eux.
Règle: Toute interaction avec la DB passe par les services core.

## Fichiers Liés (contexte)
1. app/ai/modules/transcription/routes.py (utilise TranscriptionService)
2. app/models/transcription.py (définit le modèle Transcription)
3. app/core/cache.py (utilisé pour caching)

## Erreur
Type: AttributeError
Message: 'NoneType' object has no attribute 'text'
Traceback: [...] 

## Règles d'Architecture à Respecter
1. Ne pas importer d'autres modules IA
2. Utiliser CacheService pour tout caching
3. Passer par get_session() pour accès DB
4. Lever des exceptions custom (TranscriptionError)
5. Logger toutes les erreurs avec structlog

---

Analyse l'erreur et propose une correction qui:
1. Corrige le bug
2. Respecte l'architecture du projet
3. Ne casse pas les dépendances existantes
4. Suit les conventions de code du projet
```

**Résultat** : L'AI a TOUT le contexte nécessaire pour générer un fix cohérent !

---

## 🤖 Providers IA

### 1. OpenAI Provider (GPT-4)

```python
# app/ai/modules/code_assistant/providers/openai_provider.py

from openai import AsyncOpenAI

class OpenAIProvider:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def analyze_error(self, context: str) -> AnalysisResult:
        """Utilise GPT-4 pour analyser une erreur"""
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """
Tu es un expert Python/FastAPI qui analyse des bugs.
                
Tu dois:
1. Comprendre la cause root du bug
2. Proposer un fix minimal et sûr
3. Générer le code corrigé complet
4. Expliquer pourquoi ce fix fonctionne
5. Suggérer des tests pour valider le fix
                
Réponds en JSON avec cette structure:
{
    "root_cause": "string",
    "confidence": 0.0-1.0,
    "fix": {
        "description": "string",
        "code": "string",
        "diff": "string"
    },
    "tests": ["string"],
    "explanation": "string"
}
"""
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.2  # Bas pour avoir des résultats déterministes
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return AnalysisResult(
            root_cause=result["root_cause"],
            confidence=result["confidence"],
            fix=Fix(**result["fix"]),
            tests=result["tests"],
            explanation=result["explanation"]
        )
```

### 2. Claude Provider (Anthropic)

```python
# app/ai/modules/code_assistant/providers/claude_provider.py

from anthropic import AsyncAnthropic

class ClaudeProvider:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def review_code(self, code: str, context: str) -> ReviewResult:
        """Utilise Claude pour code review approfondie"""
        
        response = await self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"""
Effectue une code review détaillée de ce code.

Context:
{{context}}

Code à review:
```python
{{code}}
```

Analyse:
1. Bugs potentiels
2. Vulnérabilités sécurité
3. Performance issues
4. Code smells
5. Violations best practices

Format JSON:
{{
    "bugs": [...],
    "security": [...],
    "performance": [...],
    "code_quality": [...],
    "suggestions": [...]
}}
"""
            }]
        )
        
        result = json.loads(response.content[0].text)
        return ReviewResult(**result)
```

### 3. Local Analyzer (Outils statiques)

```python
# app/ai/modules/code_assistant/providers/local_analyzer.py

import subprocess
from pylint import epylint as lint
from mypy import api as mypy_api

class LocalAnalyzer:
    """
    Utilise outils locaux (gratuits):
    - pylint (qualité code)
    - mypy (type checking)
    - ruff (linting ultra-rapide)
    - bandit (sécurité)
    """
    
    def analyze_file(self, file_path: str) -> LocalAnalysisResult:
        """Analyse avec tous les outils locaux"""
        
        results = {
            "pylint": self.run_pylint(file_path),
            "mypy": self.run_mypy(file_path),
            "ruff": self.run_ruff(file_path),
            "bandit": self.run_bandit(file_path)
        }
        
        return LocalAnalysisResult(**results)
    
    def run_pylint(self, file_path: str) -> dict:
        """Execute pylint"""
        (stdout, stderr) = lint.py_run(f"{file_path} --output-format=json", return_std=True)
        return json.loads(stdout.getvalue())
    
def run_mypy(self, file_path: str) -> dict:
        """Execute mypy"""
        result = mypy_api.run([file_path, "--json"])
        return json.loads(result[0]) if result[0] else {}
    
def run_ruff(self, file_path: str) -> dict:
        """Execute ruff"""
        result = subprocess.run(
            ["ruff", "check", file_path, "--output-format=json"],
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout) if result.stdout else {}
    
def run_bandit(self, file_path: str) -> dict:
        """Execute bandit (sécurité)"""
        result = subprocess.run(
            ["bandit", "-f", "json", file_path],
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout) if result.stdout else {}
```

**Stratégie combinée** :
1. **Local Analyzer** d'abord (gratuit, rapide) pour détection basique
2. **Claude** pour code review si changements importants
3. **GPT-4** pour génération de fixes complexes

---

## 💰 Estimation des Coûts

### Coûts par Opération

| Opération | Provider | Tokens | Coût Unitaire | Fréquence/Jour |
|-----------|----------|--------|---------------|----------------|
| **Auto-Fix Error** | GPT-4 Turbo | ~2000 | $0.02 | 5-10 |
| **Pre-Commit Analysis** | Local + Claude | ~1000 | $0.005 | 20-50 |
| **Daily Code Review** | Claude Opus | ~10000 | $0.15 | 1 |
| **Architecture Validation** | Local | 0 | $0 | 50-100 |

### Coût Mensuel Estimé

**Développement actif** (1 dev):
- Erreurs production: 10/jour × $0.02 = $0.20/jour = **$6/mois**
- Commits: 30/jour × $0.005 = $0.15/jour = **$4.50/mois**
- Code review: 1/jour × $0.15 = $0.15/jour = **$4.50/mois**

**Total: ~$15/mois** (très abordable pour l'usage interne)

**Équipe 5 devs**: ~$50-75/mois

---

## 📊 Métriques & Suivi

### Dashboard de Métriques

```python
# app/ai/modules/code_assistant/metrics/dashboard.py

class CodeAssistantMetrics:
    """Métriques du Code Assistant"""
    
    async def get_dashboard_data(self) -> dict:
        return {
            "auto_fixes": {
                "total": await self.count_auto_fixes(),
                "success_rate": await self.calculate_success_rate(),
                "avg_confidence": await self.get_avg_confidence(),
                "time_saved_hours": await self.estimate_time_saved()
            },
            "code_quality": {
                "bugs_prevented": await self.count_bugs_prevented(),
                "security_issues_caught": await self.count_security_catches(),
                "architecture_violations_blocked": await self.count_violations_blocked()
            },
            "costs": {
                "monthly_api_cost": await self.calculate_monthly_cost(),
                "cost_per_fix": await self.calculate_cost_per_fix(),
                "roi": await self.calculate_roi()  # Temps gagné vs coût
            }
        }
```

### Exemple de Dashboard

```
╔════════════════════════════════════════════════════════════╗
║           AI Code Assistant - Dashboard                   ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  📊 Auto-Fixes (Ce Mois)                                  ║
║  ├─ Total: 47                                             ║
║  ├─ Success Rate: 87% (41 acceptés, 6 rejetés)           ║
║  ├─ Avg Confidence: 0.89                                  ║
║  └─ Time Saved: ~23.5 heures                              ║
║                                                            ║
║  🛡️  Code Quality                                          ║
║  ├─ Bugs Prevented: 12                                    ║
║  ├─ Security Issues Caught: 3                             ║
║  └─ Architecture Violations Blocked: 8                    ║
║                                                            ║
║  💰 Costs                                                  ║
║  ├─ Monthly API Cost: $14.23                              ║
║  ├─ Cost per Fix: $0.30                                   ║
║  └─ ROI: 98x (23.5h × $50/h = $1,175 saved)              ║
║                                                            ║
║  🔝 Top Issues Fixed                                       ║
║  1. AttributeError (12 occurrences)                       ║
║  2. SQL Injection risks (3 occurrences)                   ║
║  3. Missing error handling (8 occurrences)                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 🚀 Roadmap d'Implémentation

### Semaine 1: Infrastructure de Base
- [ ] Setup module code_assistant
- [ ] Implémentation ContextBuilder (avec project-map.json)
- [ ] Implémentation OpenAI Provider
- [ ] Implémentation LocalAnalyzer
- [ ] Tests unitaires

### Semaine 2: Auto-Healing System
- [ ] Exception handler global
- [ ] Génération de fixes
- [ ] Intégration GitHub (création PR)
- [ ] Tests d'intégration
- [ ] Documentation

### Semaine 3: Pre-Commit Analysis
- [ ] Git hooks setup
- [ ] Analyseurs (bugs, security, architecture)
- [ ] Architecture Validator
- [ ] Tests end-to-end

### Semaine 4: Daily Code Review
- [ ] Tâche Celery planifiée
- [ ] Détection code smells
- [ ] Génération issues GitHub
- [ ] Dashboard métriques

### Semaine 5: Raffinement & Monitoring
- [ ] Amélioration prompts IA
- [ ] Tuning confidence thresholds
- [ ] Dashboard Grafana
- [ ] Documentation utilisateur

---

## 🔒 Sécurité & Bonnes Pratiques

### 1. Validation des Fixes Générés

```python
# Ne JAMAIS appliquer un fix automatiquement en production

# ✅ BON
if analysis.confidence > 0.90 and not is_production():
    await create_fix_pr(fix)  # Crée PR pour review humaine

# ❌ MAUVAIS
if analysis.confidence > 0.80:
    await apply_fix_directly(fix)  # Dangereux !
```

### 2. Audit Trail

```python
# Logger TOUS les fixes générés
await audit_log.log({
    "event": "auto_fix_generated",
    "error": error_context,
    "analysis": analysis,
    "fix": fix,
    "confidence": analysis.confidence,
    "applied": False,
    "pr_url": pr_url
})
```

### 3. Rate Limiting

```python
# Limiter les appels API
if await rate_limiter.is_exceeded("code_assistant", limit=100, window="1h"):
    # Fallback sur LocalAnalyzer
    return await local_analyzer.analyze(file_path)
```

---

## 📝 Configuration

```yaml
# app/ai/modules/code_assistant/manifest.yaml

name: code_assistant
version: 1.0.0
description: AI-powered code analysis and auto-fixing

providers:
  openai:
    enabled: true
    model: gpt-4-turbo-preview
    max_tokens: 4096
    temperature: 0.2  
  
  claude:
    enabled: true
    model: claude-3-opus-20240229
    max_tokens: 4096
  
  local:
    enabled: true
    tools:
      - pylint
      - mypy
      - ruff
      - bandit

features:
  auto_healing:
    enabled: true
    confidence_threshold: 0.85
    create_pr: true
    auto_merge: false  # Toujours false !
  
  pre_commit_analysis:
    enabled: true
    block_on_critical: true
    tools: [local, claude]
  
  architecture_validation:
    enabled: true
    strict_mode: true
    rules_file: architecture-rules.yaml
  
  daily_review:
    enabled: true
    schedule: "0 2 * * *"  # 2h du matin
    create_issues: true

costs:
  monthly_budget: 50  # USD
  alert_threshold: 0.8  # 80% du budget

dependencies:
  internal:
    - app.core.database
    - app.core.cache
    - app.core.github_service
  external:
    - openai==1.12.0
    - anthropic==0.18.1
    - pylint==3.0.3
    - mypy==1.8.0
    - ruff==0.2.1
    - bandit==1.7.6
```

---

## ✅ Checklist de Mise en Production

- [ ] project-map.json généré et à jour
- [ ] Providers IA configurés (API keys)
- [ ] Git hooks installés
- [ ] Tests unitaires >80% coverage
- [ ] Dashboard métriques opérationnel
- [ ] Documentation complète
- [ ] Budget monitoring configuré
- [ ] Audit trail activé
- [ ] Rate limiting configuré
- [ ] Alertes configurées (Slack/Email)

---

## 📞 Support

Pour questions ou issues:
- 📧 Email: dev@saas-ia.com
- 💬 GitHub Issues: /issues
- 📚 Documentation: /docs/code-assistant

---

**Créé le**: 2025-11-13 19:26:19
**Version**: 1.0.0  
**Auteur**: @benziane  
**Statut**: 🚀 Prêt à implémenter