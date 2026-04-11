# AutoResearch - Analyse des Opportunités pour SaaS-IA

**Date**: 2026-04-08  
**Version**: 1.0  
**Projet source**: [karpathy/autoresearch](https://github.com/karpathy/autoresearch)  
**Clone local**: `C:\Users\ibzpc\Git\projets_poc\autoresearch-master`

---

## 📋 Executive Summary

AutoResearch est un framework expérimental de **recherche autonome en IA** développé par Andrej Karpathy. Le concept : donner à un agent IA un environnement d'entraînement LLM minimal et le laisser expérimenter de manière autonome pour améliorer les performances du modèle.

### Concept Clé
- **Budget de temps fixe** : 5 minutes d'entraînement par expérience
- **Métrique unique** : `val_bpb` (validation bits per byte) - indépendante de la taille du vocabulaire
- **Fichier unique modifiable** : `train.py` (architecture, optimiseur, hyperparamètres)
- **Instructions agent** : `program.md` (le "skill" qui guide l'agent)
- **Boucle autonome** : l'agent modifie le code, entraîne, évalue, garde ou rejette les changements

### Résultats Attendus
- ~12 expériences/heure
- ~100 expériences pendant une nuit de sommeil
- Amélioration progressive du modèle via sélection évolutive

---

## 🎯 Opportunités d'Intégration dans SaaS-IA

### 1. **Module `auto_research` - Recherche Autonome IA** ⭐⭐⭐⭐⭐

**Priorité**: P0 (Haute Innovation)  
**Effort**: 8-12 jours  
**Impact**: Très élevé - Feature unique et différenciante

#### Description
Créer un nouveau module permettant aux utilisateurs de lancer des sessions de recherche autonome sur leurs propres modèles ou tâches IA.

#### Architecture Proposée

```
mvp/backend/app/modules/auto_research/
├── manifest.json
├── schemas.py          # ExperimentConfig, ExperimentResult, ResearchSession
├── service.py          # AutoResearchService
├── routes.py           # API endpoints
├── executor.py         # Isolated execution environment
├── agent_loop.py       # Main experiment loop
└── templates/
    ├── program_gpt.md      # Template pour entraînement GPT
    ├── program_finetune.md # Template pour fine-tuning
    └── program_custom.md   # Template personnalisable
```

#### Fonctionnalités Clés

**Backend**:
- `POST /api/auto-research/sessions` - Créer une session de recherche
- `GET /api/auto-research/sessions/{id}` - Statut de la session
- `GET /api/auto-research/sessions/{id}/experiments` - Liste des expériences
- `GET /api/auto-research/sessions/{id}/results.tsv` - Export TSV des résultats
- `POST /api/auto-research/sessions/{id}/stop` - Arrêter la session
- `GET /api/auto-research/templates` - Templates program.md disponibles

**Configuration**:
```python
class ResearchSessionConfig(BaseModel):
    name: str
    template: str  # "gpt", "finetune", "custom"
    program_md: Optional[str]  # Custom program.md
    time_budget_seconds: int = 300  # 5 minutes par défaut
    max_experiments: Optional[int] = None  # Illimité par défaut
    base_code: str  # Code Python de base (train.py)
    evaluation_metric: str = "val_bpb"
    gpu_required: bool = True
    workspace_id: Optional[int] = None
```

**Exécution**:
- Utiliser **Celery** pour les tâches longues
- Isolation via **Docker containers** (sécurité)
- Monitoring en temps réel via **WebSocket** ou **SSE**
- Sauvegarde automatique des checkpoints

#### Intégration avec Modules Existants

1. **`fine_tuning`** - Utiliser AutoResearch pour optimiser automatiquement les hyperparamètres de fine-tuning
2. **`ai_workflows`** - Action "AutoResearch" dans les workflows DAG
3. **`agents`** - Agent "Research Optimizer" qui lance des sessions AutoResearch
4. **`workspaces`** - Sessions partagées entre membres d'un workspace
5. **`billing`** - Quotas GPU/compute pour les plans Pro/Enterprise
6. **`ai_monitoring`** - Tracking des expériences et métriques

#### Sécurité

- **Sandbox Docker** : Exécution isolée du code agent
- **Resource limits** : CPU, RAM, GPU, temps max
- **Code review** : Option pour valider manuellement les changements avant exécution
- **Whitelist imports** : Limiter les packages Python autorisés
- **Audit trail** : Logger tous les changements de code

#### Frontend

```
mvp/frontend/src/features/auto-research/
├── types.ts
├── api.ts
├── hooks/
│   ├── useResearchSessions.ts
│   ├── useExperiments.ts
│   └── useSessionMonitoring.ts
└── components/
    ├── SessionCreator.tsx
    ├── SessionMonitor.tsx
    ├── ExperimentList.tsx
    ├── CodeDiffViewer.tsx
    └── MetricsChart.tsx

mvp/frontend/src/app/(dashboard)/auto-research/
├── page.tsx              # Liste des sessions
├── new/page.tsx          # Créer une session
└── [id]/page.tsx         # Détails session + monitoring temps réel
```

**UI Features**:
- **Live monitoring** : Graphique temps réel des métriques (val_bpb, VRAM, MFU)
- **Code diff viewer** : Visualiser les changements entre expériences
- **Experiment timeline** : Chronologie des expériences (keep/discard/crash)
- **Best model download** : Télécharger le meilleur modèle trouvé
- **Resume session** : Reprendre une session interrompue

---

### 2. **Extension du Module `fine_tuning`** ⭐⭐⭐⭐

**Priorité**: P1  
**Effort**: 4-6 jours  
**Impact**: Élevé - Améliore un module existant

#### Description
Intégrer la logique AutoResearch dans le module `fine_tuning` existant pour optimiser automatiquement les hyperparamètres.

#### Nouvelles Fonctionnalités

**Auto-tuning des hyperparamètres**:
```python
# Dans fine_tuning/service.py
class FineTuningService:
    async def auto_optimize_hyperparameters(
        self,
        dataset_id: int,
        base_model: str,
        optimization_budget_hours: int = 8,
        user_id: int
    ) -> AutoOptimizationResult:
        """
        Lance une session AutoResearch pour trouver les meilleurs hyperparamètres.
        
        Optimise:
        - Learning rate
        - Batch size
        - LoRA rank et alpha
        - Warmup steps
        - Weight decay
        """
        pass
```

**Endpoints**:
- `POST /api/fine-tuning/auto-optimize` - Lancer l'optimisation auto
- `GET /api/fine-tuning/auto-optimize/{id}/status` - Statut de l'optimisation

**Bénéfices**:
- Utilisateurs non-experts peuvent obtenir de bons résultats
- Économie de temps et de ressources GPU
- Meilleurs modèles finaux

---

### 3. **Module `model_playground` - Expérimentation Interactive** ⭐⭐⭐⭐

**Priorité**: P1  
**Effort**: 6-8 jours  
**Impact**: Élevé - Nouvelle expérience utilisateur

#### Description
Créer un "playground" interactif où les utilisateurs peuvent expérimenter avec des architectures de modèles, inspiré par AutoResearch mais avec contrôle manuel.

#### Fonctionnalités

**Interface No-Code/Low-Code**:
- **Architecture Builder** : Drag & drop pour construire des architectures (nombre de layers, attention heads, etc.)
- **Hyperparameter Tuner** : Sliders pour ajuster les hyperparamètres
- **Quick Experiments** : Lancer des entraînements courts (1-5 min) pour tester rapidement
- **Compare Runs** : Comparer plusieurs configurations côte à côte

**Intégration AutoResearch**:
- Bouton "Auto-Optimize" qui lance une session AutoResearch sur la config actuelle
- Suggestions basées sur les expériences précédentes

**Use Cases**:
- Éducation : Apprendre comment les hyperparamètres affectent les performances
- Prototypage rapide : Tester des idées avant un entraînement complet
- Recherche : Explorer l'espace des hyperparamètres

---

### 4. **Module `ai_lab` - Laboratoire de Recherche IA** ⭐⭐⭐⭐⭐

**Priorité**: P0 (Vision Long Terme)  
**Effort**: 15-20 jours  
**Impact**: Très élevé - Plateforme de recherche complète

#### Description
Créer un environnement de recherche IA complet, inspiré par AutoResearch mais étendu à d'autres types d'expériences.

#### Composants

**1. Experiment Manager**
- Gestion de multiples types d'expériences (entraînement, fine-tuning, prompt engineering, etc.)
- Versioning automatique du code et des données
- Reproductibilité garantie

**2. Autonomous Agents**
- **Research Agent** : Basé sur AutoResearch, optimise les modèles
- **Prompt Engineer Agent** : Optimise les prompts automatiquement
- **Data Curator Agent** : Améliore les datasets (nettoyage, augmentation)
- **Architecture Search Agent** : Neural Architecture Search (NAS)

**3. Collaboration Tools**
- Notebooks partagés (Jupyter intégré)
- Code review des expériences
- Discussion threads sur les résultats
- Publication de "research papers" internes

**4. MLOps Integration**
- CI/CD pour les modèles
- A/B testing automatique
- Deployment pipelines
- Model registry

**5. Compute Management**
- Pool de GPUs partagés
- Queue de jobs avec priorités
- Cost tracking par expérience
- Spot instances pour réduire les coûts

#### Architecture

```
mvp/backend/app/modules/ai_lab/
├── manifest.json
├── experiments/
│   ├── base.py           # Base Experiment class
│   ├── training.py       # Training experiments (AutoResearch)
│   ├── prompt.py         # Prompt optimization
│   ├── data.py           # Data curation
│   └── nas.py            # Architecture search
├── agents/
│   ├── research_agent.py
│   ├── prompt_agent.py
│   ├── data_agent.py
│   └── nas_agent.py
├── compute/
│   ├── scheduler.py      # Job scheduling
│   ├── gpu_pool.py       # GPU management
│   └── docker_runner.py  # Isolated execution
├── collaboration/
│   ├── notebooks.py      # Jupyter integration
│   ├── reviews.py        # Code review
│   └── discussions.py    # Threads
└── mlops/
    ├── registry.py       # Model registry
    ├── deployment.py     # Deploy pipelines
    └── monitoring.py     # Production monitoring
```

---

### 5. **Extension du Module `agents`** ⭐⭐⭐

**Priorité**: P2  
**Effort**: 3-4 jours  
**Impact**: Moyen - Enrichit un module existant

#### Description
Ajouter un nouveau type d'agent "Research Optimizer" qui utilise la logique AutoResearch.

#### Nouvelle Action Agent

```python
# Dans agents/executor.py
class AgentExecutor:
    async def execute_auto_research(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Action: auto_research
        
        Params:
        - base_code: Code Python de base
        - program_md: Instructions pour l'agent
        - time_budget: Budget de temps (secondes)
        - max_experiments: Nombre max d'expériences
        
        Returns:
        - best_experiment: Meilleure expérience trouvée
        - results_tsv: Résultats complets
        - improvements: Liste des améliorations
        """
        pass
```

**Use Case**:
Un agent qui optimise automatiquement un modèle pour une tâche spécifique :
1. Utilisateur : "Optimise un modèle pour résumer mes documents"
2. Agent analyse les documents
3. Agent lance une session AutoResearch avec un code de base adapté
4. Agent retourne le meilleur modèle trouvé

---

### 6. **Extension du Module `ai_workflows`** ⭐⭐⭐

**Priorité**: P2  
**Effort**: 2-3 jours  
**Impact**: Moyen - Ajoute une action workflow puissante

#### Description
Ajouter une action "AutoResearch" dans les workflows DAG.

#### Nouvelle Action Workflow

```python
# Dans ai_workflows/actions.py
class AutoResearchAction(WorkflowAction):
    """
    Action: auto_research
    
    Inputs:
    - base_code: Code Python (peut venir d'une action précédente)
    - program_md: Instructions agent
    - time_budget: Budget temps
    
    Outputs:
    - best_model_path: Chemin vers le meilleur modèle
    - metrics: Métriques finales
    - experiments_count: Nombre d'expériences
    """
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Lance une session AutoResearch
        # Attend la fin
        # Retourne les résultats
        pass
```

**Use Case - Workflow Complet**:
```yaml
name: "Optimize Custom Model"
steps:
  - id: load_data
    action: load_dataset
    params:
      dataset_id: 123
  
  - id: generate_base_code
    action: ai_generate
    params:
      prompt: "Generate training code for this dataset"
      context: ${load_data.output}
  
  - id: auto_optimize
    action: auto_research
    params:
      base_code: ${generate_base_code.output}
      time_budget: 3600  # 1 heure
  
  - id: deploy_model
    action: deploy_model
    params:
      model_path: ${auto_optimize.best_model_path}
```

---

### 7. **Module `prompt_optimizer` - Optimisation Automatique de Prompts** ⭐⭐⭐⭐

**Priorité**: P1  
**Effort**: 5-7 jours  
**Impact**: Élevé - Application directe du concept AutoResearch

#### Description
Adapter le concept AutoResearch pour l'optimisation de prompts au lieu de modèles.

#### Concept

Au lieu d'optimiser du code Python, l'agent optimise des prompts :
- **Métrique** : Qualité des réponses (score automatique ou humain)
- **Modifications** : Reformulation, ajout d'exemples, changement de structure
- **Évaluation** : Test sur un dataset de validation

#### Fonctionnalités

**Backend**:
```python
class PromptOptimizationSession:
    task_description: str
    initial_prompt: str
    evaluation_dataset: List[Dict]  # Questions + réponses attendues
    optimization_budget: int  # Nombre d'itérations
    evaluation_metric: str  # "accuracy", "similarity", "custom"
```

**Processus**:
1. Agent reçoit le prompt initial et la description de la tâche
2. Agent génère des variantes du prompt
3. Chaque variante est testée sur le dataset de validation
4. Les meilleures variantes sont gardées et améliorées
5. Retour du meilleur prompt trouvé

**Use Cases**:
- Optimiser un prompt pour un chatbot
- Trouver le meilleur prompt pour une tâche de classification
- A/B testing automatique de prompts

---

## 🔧 Aspects Techniques Communs

### Exécution Isolée

**Option 1 : Docker Containers** (Recommandé)
```python
# executor.py
import docker

class DockerExecutor:
    async def run_experiment(
        self,
        code: str,
        time_budget: int,
        gpu: bool = True
    ) -> ExperimentResult:
        client = docker.from_env()
        
        # Créer un container isolé
        container = client.containers.run(
            image="pytorch/pytorch:2.0.1-cuda11.8-cudnn8-runtime",
            command=f"python train.py",
            volumes={
                '/tmp/experiment': {'bind': '/workspace', 'mode': 'rw'}
            },
            device_requests=[
                docker.types.DeviceRequest(count=1, capabilities=[['gpu']])
            ] if gpu else None,
            mem_limit="16g",
            cpu_quota=100000,  # 1 CPU
            detach=True,
            remove=True
        )
        
        # Attendre avec timeout
        try:
            result = container.wait(timeout=time_budget + 60)
            logs = container.logs().decode('utf-8')
            return self._parse_result(logs)
        except Exception as e:
            container.kill()
            raise
```

**Option 2 : Subprocess avec Limites** (Plus simple, moins sécurisé)
```python
import asyncio
import resource

async def run_with_limits(code: str, time_budget: int):
    # Limiter les ressources
    def set_limits():
        resource.setrlimit(resource.RLIMIT_CPU, (time_budget, time_budget))
        resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    
    proc = await asyncio.create_subprocess_exec(
        'python', 'train.py',
        preexec_fn=set_limits,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=time_budget + 60
        )
        return stdout.decode('utf-8')
    except asyncio.TimeoutError:
        proc.kill()
        raise
```

### Monitoring Temps Réel

**WebSocket pour le streaming des logs**:
```python
# routes.py
from fastapi import WebSocket

@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(
    websocket: WebSocket,
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    await websocket.accept()
    
    # Stream les logs en temps réel
    async for log_line in session_log_stream(session_id):
        await websocket.send_json({
            "type": "log",
            "data": log_line
        })
    
    await websocket.close()
```

**Frontend**:
```typescript
// useSessionMonitoring.ts
export function useSessionMonitoring(sessionId: number) {
  const [logs, setLogs] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8004/api/auto-research/ws/sessions/${sessionId}`
    );
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'log') {
        setLogs(prev => [...prev, data.data]);
      } else if (data.type === 'metrics') {
        setMetrics(data.data);
      }
    };
    
    return () => ws.close();
  }, [sessionId]);
  
  return { logs, metrics };
}
```

### Sauvegarde et Versioning

**Git pour le versioning du code**:
```python
import git

class ExperimentVersioning:
    def __init__(self, session_id: int):
        self.repo_path = f"/tmp/autoresearch/{session_id}"
        self.repo = git.Repo.init(self.repo_path)
    
    def commit_experiment(
        self,
        code: str,
        metrics: Dict[str, float],
        status: str
    ) -> str:
        # Écrire le code
        with open(f"{self.repo_path}/train.py", "w") as f:
            f.write(code)
        
        # Commit
        self.repo.index.add(["train.py"])
        commit = self.repo.index.commit(
            f"{status}: val_bpb={metrics.get('val_bpb', 0):.6f}"
        )
        
        return commit.hexsha[:7]
    
    def get_best_experiment(self) -> Tuple[str, str]:
        # Parcourir l'historique pour trouver le meilleur
        best_commit = None
        best_metric = float('inf')
        
        for commit in self.repo.iter_commits():
            # Parser le message pour extraire la métrique
            match = re.search(r'val_bpb=([\d.]+)', commit.message)
            if match:
                metric = float(match.group(1))
                if metric < best_metric:
                    best_metric = metric
                    best_commit = commit
        
        if best_commit:
            code = best_commit.tree['train.py'].data_stream.read().decode('utf-8')
            return code, best_commit.hexsha[:7]
        
        return None, None
```

---

## 📊 Comparaison des Opportunités

| Opportunité | Priorité | Effort | Impact | Innovation | Complexité Technique |
|-------------|----------|--------|--------|------------|---------------------|
| Module `auto_research` | P0 | 8-12j | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Élevée |
| Extension `fine_tuning` | P1 | 4-6j | ⭐⭐⭐⭐ | ⭐⭐⭐ | Moyenne |
| Module `model_playground` | P1 | 6-8j | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Moyenne |
| Module `ai_lab` | P0 | 15-20j | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Très élevée |
| Extension `agents` | P2 | 3-4j | ⭐⭐⭐ | ⭐⭐⭐ | Faible |
| Extension `ai_workflows` | P2 | 2-3j | ⭐⭐⭐ | ⭐⭐⭐ | Faible |
| Module `prompt_optimizer` | P1 | 5-7j | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Moyenne |

---

## 🚀 Plan d'Implémentation Recommandé

### Phase 1 : Proof of Concept (2 semaines)

**Objectif** : Valider la faisabilité technique

1. **Semaine 1** : Module `auto_research` minimal
   - Structure de base (manifest, schemas, routes)
   - Exécution isolée simple (subprocess)
   - 1 template program.md (GPT training)
   - API de base (create, status, stop)

2. **Semaine 2** : Frontend minimal + tests
   - Page création de session
   - Monitoring temps réel (polling simple)
   - Liste des expériences
   - Tests d'intégration

**Livrable** : Démo fonctionnelle d'une session AutoResearch

### Phase 2 : Production-Ready (3 semaines)

**Objectif** : Version stable et sécurisée

1. **Semaine 3** : Sécurité et isolation
   - Migration vers Docker containers
   - Resource limits (CPU, RAM, GPU, temps)
   - Whitelist imports Python
   - Audit trail complet

2. **Semaine 4** : Intégrations
   - Celery pour les tâches longues
   - WebSocket pour monitoring temps réel
   - Intégration avec `workspaces`
   - Intégration avec `billing` (quotas GPU)

3. **Semaine 5** : Polish et documentation
   - UI/UX amélioré (graphiques, diff viewer)
   - Templates program.md supplémentaires
   - Documentation complète
   - Tests end-to-end

**Livrable** : Module production-ready

### Phase 3 : Extensions (4 semaines)

**Objectif** : Enrichir l'écosystème

1. **Semaine 6-7** : Extension `fine_tuning`
   - Auto-optimisation des hyperparamètres
   - Intégration avec AutoResearch
   - Tests sur datasets réels

2. **Semaine 8** : Extension `agents` et `ai_workflows`
   - Action "auto_research" dans les agents
   - Action "auto_research" dans les workflows
   - Exemples et templates

3. **Semaine 9** : Module `prompt_optimizer`
   - Adaptation du concept pour les prompts
   - UI dédiée
   - Intégration avec `conversation`

**Livrable** : Écosystème complet AutoResearch

### Phase 4 : Vision Long Terme (8+ semaines)

**Objectif** : Plateforme de recherche IA complète

- Module `ai_lab` complet
- Collaboration tools (notebooks, reviews)
- MLOps integration (registry, deployment)
- Compute management (GPU pool, scheduling)

---

## 💡 Cas d'Usage Concrets

### Use Case 1 : Startup IA sans ML Engineer

**Problème** : Une startup veut fine-tuner un modèle mais n'a pas d'expertise en ML.

**Solution** :
1. Upload leur dataset dans `knowledge` ou `fine_tuning`
2. Lancer une session AutoResearch avec le template "finetune"
3. L'agent optimise automatiquement les hyperparamètres pendant la nuit
4. Le matin, le meilleur modèle est prêt à déployer

**Valeur** : Démocratisation du ML, pas besoin d'expert

### Use Case 2 : Chercheur en IA

**Problème** : Un chercheur veut explorer rapidement différentes architectures de modèles.

**Solution** :
1. Utiliser `model_playground` pour prototyper des architectures
2. Lancer des sessions AutoResearch sur les configs prometteuses
3. Comparer les résultats dans `ai_monitoring`
4. Publier les findings dans `ai_lab` (research papers internes)

**Valeur** : Accélération de la recherche, reproductibilité

### Use Case 3 : Entreprise avec Beaucoup de Données

**Problème** : Une entreprise a des données propriétaires et veut un modèle custom optimal.

**Solution** :
1. Upload les données dans `knowledge`
2. Créer un workflow `ai_workflows` :
   - Prétraitement des données
   - AutoResearch pour trouver la meilleure architecture
   - Fine-tuning avec les meilleurs hyperparamètres
   - Déploiement automatique
3. Le workflow tourne en arrière-plan

**Valeur** : Automatisation complète, modèles sur-mesure

### Use Case 4 : Optimisation de Chatbot

**Problème** : Un chatbot ne performe pas bien, le prompt doit être amélioré.

**Solution** :
1. Utiliser `prompt_optimizer` avec un dataset de conversations
2. L'agent génère et teste des variantes de prompts
3. Le meilleur prompt est automatiquement déployé dans `conversation`

**Valeur** : Amélioration continue automatique

---

## 🔐 Considérations de Sécurité

### Risques Identifiés

1. **Exécution de code arbitraire**
   - **Mitigation** : Docker containers isolés, pas d'accès réseau, resource limits

2. **Consommation excessive de ressources**
   - **Mitigation** : Quotas par utilisateur, timeouts stricts, monitoring

3. **Accès aux données sensibles**
   - **Mitigation** : Isolation des données, pas d'accès au filesystem hôte

4. **Injection de code malveillant**
   - **Mitigation** : Whitelist imports, code review optionnel, audit trail

5. **Déni de service**
   - **Mitigation** : Rate limiting, queue de jobs, priorités

### Best Practices

- **Principe du moindre privilège** : Containers sans privilèges root
- **Defense in depth** : Multiples couches de sécurité
- **Audit complet** : Logger toutes les actions
- **Validation stricte** : Valider tous les inputs
- **Timeouts partout** : Aucune opération sans timeout

---

## 💰 Modèle de Monétisation

### Plans Billing

**Free** :
- 10 expériences/mois
- 5 minutes par expérience
- CPU seulement
- 1 session simultanée

**Pro** ($49/mois) :
- 100 expériences/mois
- 30 minutes par expérience
- GPU T4 (16GB)
- 3 sessions simultanées
- Templates avancés

**Enterprise** ($299/mois) :
- Expériences illimitées
- Temps illimité par expérience
- GPU A100 (40GB)
- 10 sessions simultanées
- Templates custom
- Support prioritaire
- Compute pool dédié

### Coûts Estimés

**GPU Cloud** (AWS/GCP) :
- T4 : ~$0.35/heure
- A100 : ~$2.50/heure

**Marge** :
- Free : Loss leader (acquisition)
- Pro : ~70% marge (après coûts GPU)
- Enterprise : ~80% marge (volume)

---

## 📈 Métriques de Succès

### Métriques Produit

- **Adoption** : Nombre de sessions créées/mois
- **Engagement** : Durée moyenne des sessions
- **Rétention** : % d'utilisateurs qui reviennent
- **Conversion** : Free → Pro → Enterprise

### Métriques Techniques

- **Fiabilité** : % de sessions qui se terminent avec succès
- **Performance** : Temps moyen par expérience
- **Efficacité** : % d'expériences qui améliorent la métrique
- **Utilisation GPU** : % d'utilisation des ressources

### Métriques Business

- **Revenue** : MRR (Monthly Recurring Revenue)
- **CAC** : Coût d'acquisition client
- **LTV** : Lifetime Value
- **Churn** : Taux de désabonnement

---

## 🎓 Ressources et Références

### Documentation AutoResearch

- **Repo GitHub** : https://github.com/karpathy/autoresearch
- **Tweet Karpathy** : https://x.com/karpathy/status/2029701092347630069
- **Dummy's Guide** : https://x.com/hooeem/status/2030720614752039185

### Technologies Clés

- **PyTorch** : Framework de deep learning
- **Flash Attention 3** : Kernels optimisés pour l'attention
- **Muon Optimizer** : Optimiseur avancé pour les matrices
- **BPE Tokenizer** : Tokenization efficace
- **Docker** : Isolation et déploiement
- **Celery** : Tâches asynchrones

### Concepts ML

- **Bits Per Byte (BPB)** : Métrique indépendante du vocabulaire
- **Model Flops Utilization (MFU)** : Efficacité GPU
- **Rotary Embeddings** : Encodage positionnel
- **Sliding Window Attention** : Attention avec fenêtre glissante
- **Value Embeddings** : Embeddings pour les valeurs d'attention

---

## 🤔 Questions Ouvertes

### Techniques

1. **Quelle plateforme GPU** : AWS, GCP, Azure, ou on-premise ?
2. **Quelle stratégie de scaling** : Kubernetes, Docker Swarm, ou simple ?
3. **Quel niveau d'isolation** : Containers, VMs, ou bare metal ?
4. **Quelle stratégie de cache** : Redis, filesystem, ou S3 ?

### Produit

1. **Quel niveau de contrôle** : Full autonomie ou validation manuelle ?
2. **Quels templates** : GPT, BERT, ViT, ou custom ?
3. **Quelle UI** : Simple ou avancée (notebooks intégrés) ?
4. **Quelle collaboration** : Sessions partagées ou individuelles ?

### Business

1. **Quel pricing** : Usage-based ou flat fee ?
2. **Quel GTM** : Self-service ou sales-assisted ?
3. **Quel segment** : Startups, entreprises, ou chercheurs ?
4. **Quel positionnement** : Low-code ML ou research platform ?

---

## ✅ Recommandations Finales

### Top 3 Priorités

1. **Module `auto_research`** (P0)
   - Feature la plus innovante et différenciante
   - Valeur immédiate pour les utilisateurs
   - Fondation pour les autres extensions

2. **Module `prompt_optimizer`** (P1)
   - Application directe du concept AutoResearch
   - Cas d'usage très concret (chatbots)
   - Moins complexe techniquement

3. **Extension `fine_tuning`** (P1)
   - Améliore un module existant
   - Synergies évidentes
   - Quick win

### Approche Recommandée

**Itérative et Incrémentale** :
1. Commencer par un POC minimal (2 semaines)
2. Valider avec des early adopters
3. Itérer sur le feedback
4. Étendre progressivement

**Focus sur la Valeur** :
- Résoudre un problème réel (optimisation difficile)
- Démocratiser le ML (pas besoin d'expert)
- Automatiser les tâches répétitives

**Maintenir la Qualité** :
- Tests exhaustifs
- Documentation complète
- Sécurité en priorité
- Performance optimale

---

## �️ Pré-requis Hardware et Software

### Hardware (HW) - Configuration Requise

#### GPU NVIDIA (Obligatoire pour version originale)

**Configuration Officielle** :
- **Minimum** : 1 GPU NVIDIA avec support CUDA
- **Testé sur** : H100 (80GB VRAM)
- **Recommandé pour production** :
  - H100 (80GB) - Performance optimale
  - A100 (40GB/80GB) - Excellent
  - RTX 4090 (24GB) - Bon pour modèles plus petits
  - RTX 3090 (24GB) - Acceptable avec ajustements

**VRAM Requis** :
- Configuration par défaut : ~45GB VRAM
- Configuration minimale ajustée : ~12-16GB VRAM
- Ajustable via : `DEPTH`, `DEVICE_BATCH_SIZE`, `TOTAL_BATCH_SIZE`, `MAX_SEQ_LEN`

**Autres Composants** :
- **CPU** : Multi-core moderne (pour data loading parallèle)
- **RAM** : 32GB+ recommandé (dataset en cache)
- **Stockage** : ~50GB libre pour cache (`~/.cache/autoresearch/`)
  - Training shards : ~40GB (10 shards par défaut)
  - Validation shard : ~4GB
  - Tokenizer : <100MB

#### Plateformes Alternatives

**Windows** : Fork [jsegov/autoresearch-win-rtx](https://github.com/jsegov/autoresearch-win-rtx)  
**macOS** : Forks [miolini/autoresearch-macos](https://github.com/miolini/autoresearch-macos) ou [trevin-creator/autoresearch-mlx](https://github.com/trevin-creator/autoresearch-mlx)  
**AMD GPU** : Fork [andyluo7/autoresearch](https://github.com/andyluo7/autoresearch)

### Software (SW) - Dépendances

#### Système d'Exploitation
- **Linux** : Recommandé (Ubuntu 20.04+)
- **Windows** : Supporté via fork
- **macOS** : Supporté via forks MLX

#### Python et Gestionnaire de Paquets
- **Python** : 3.10+ (testé avec 3.10, 3.11, 3.12, 3.13)
- **Gestionnaire** : [uv](https://docs.astral.sh/uv/) (recommandé) ou pip

#### CUDA
- **Version** : CUDA 12.8 (via PyTorch)
- **Drivers** : NVIDIA drivers compatibles CUDA 12.8+

#### Dépendances Python

```toml
[project]
requires-python = ">=3.10"
dependencies = [
    "kernels>=0.11.7",        # Flash Attention 3 kernels
    "matplotlib>=3.10.8",     # Visualisation
    "numpy>=2.2.6",           # Calculs numériques
    "pandas>=2.3.3",          # Manipulation données
    "pyarrow>=21.0.0",        # Lecture Parquet
    "requests>=2.32.0",       # Download datasets
    "rustbpe>=0.1.0",         # BPE tokenizer (Rust)
    "tiktoken>=0.11.0",       # Tokenizer OpenAI
    "torch==2.9.1",           # PyTorch avec CUDA 12.8
]
```

#### Installation Rapide

```bash
# 1. Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Cloner et installer
git clone https://github.com/karpathy/autoresearch.git
cd autoresearch
uv sync

# 3. Préparer données et tokenizer (~2 min)
uv run prepare.py

# 4. Test (~5 min)
uv run train.py
```

---

## 💰 Options d'Accès et Coûts

### Option 1 : GPU Cloud ⭐ **RECOMMANDÉ pour Démarrer**

#### Services Cloud Payants

| Service | GPU | VRAM | Coût/heure | Coût/session (5min) | Idéal pour |
|---------|-----|------|------------|---------------------|------------|
| **RunPod** | RTX 4090 | 24GB | $0.69 | $0.06 | POC/Production |
| **RunPod** | A100 | 40GB | $1.89 | $0.16 | Production |
| **Paperspace** | RTX 4000 | 8GB | $0.51 | $0.04 | Tests |
| **AWS EC2 P3** | V100 | 16GB | $3.06 | $0.26 | Enterprise |
| **AWS EC2 P4** | A100 | 40GB | $5.00 | $0.42 | Enterprise |
| **Google Colab Pro** | T4/A100 | 16-40GB | $10/mois | Illimité* | POC |

*Avec limitations de sessions

#### Services Cloud GRATUITS 🎁

| Service | GPU | VRAM | Limitations | Viable pour |
|---------|-----|------|-------------|-------------|
| **Google Colab Free** | T4 | 15GB | Sessions 12h, quotas GPU | ✅ Tests et apprentissage |
| **Kaggle Notebooks** | P100/T4 | 16GB | 30h GPU/semaine, sessions 12h | ✅ Tests et POC |
| **Lightning AI Free** | T4 | 16GB | 22 GPU-heures/mois | ✅ Tests limités |

**Configuration Allégée pour GPU Gratuits** :
```python
# Dans train.py - pour T4 (15GB)
DEPTH = 4              # au lieu de 8
DEVICE_BATCH_SIZE = 32 # au lieu de 128
TOTAL_BATCH_SIZE = 2**16  # au lieu de 2**19
WINDOW_PATTERN = "L"   # au lieu de "SSSL"

# Dans prepare.py
MAX_SEQ_LEN = 1024     # au lieu de 2048
```

**Résultats Attendus (Colab/Kaggle Gratuit)** :
- ✅ 10-15 expériences par session (1-2h)
- ✅ Comprendre le concept AutoResearch
- ✅ Valider l'intérêt pour votre projet
- ⚠️ Pas viable pour recherche intensive (100+ expériences)

### Option 2 : GPU Local (Achat Matériel)

#### Budget et Recommandations

**Entrée de Gamme** (~€400-600) :
- **RTX 3060** (12GB) : ~€350-450
  - ⚠️ Nécessite configuration très allégée
  - Viable pour apprentissage uniquement

**Milieu de Gamme** (~€800-1400) :
- **RTX 4070 Ti** (12GB) : ~€800-900
- **RTX 4080** (16GB) : ~€1200-1400
  - ✅ Bon compromis performance/prix
  - ✅ Peut gérer configs moyennes

**Haut de Gamme** (~€1800-2200) :
- **RTX 4090** (24GB) : ~€1800-2200
  - ✅ Excellent pour AutoResearch
  - ✅ Gère les configs par défaut
  - ✅ Viable pour production

**Considérations Supplémentaires** :
- Alimentation : 750W+ (RTX 4090)
- Refroidissement adéquat
- Compatibilité carte mère (PCIe 4.0)
- Électricité : ~€20-30/mois (24/7)

#### Analyse Coût Cloud vs Local

**Seuil de Rentabilité** :

```
GPU RTX 4090 : €2000 one-time
Amortissement 2 ans : €83/mois
Électricité : €25/mois
Total mensuel : €108/mois

VS

Cloud RunPod (RTX 4090) : $0.69/heure
1000 sessions/mois × 10min = 167h
Coût mensuel : $115 (~€108)

→ Rentable si > 1000 sessions/mois
```

### Option 3 : Version CPU (Non Recommandé)

**Faisabilité** :
- ⚠️ Extrêmement lent (heures au lieu de minutes)
- Uniquement pour lire et comprendre le code
- Pas viable pour expériences réelles
- Utiliser uniquement pour exploration du code source

---

## 🚀 Guide de Démarrage selon Votre Situation

### Scénario A : Vous N'avez PAS de GPU NVIDIA

#### Étape 1 : Test Gratuit (Aujourd'hui - 1h)

**Google Colab Gratuit** :
1. Aller sur https://colab.research.google.com/
2. Créer nouveau notebook
3. Runtime → Change runtime type → GPU (T4)
4. Exécuter :

```python
!git clone https://github.com/karpathy/autoresearch.git
%cd autoresearch
!pip install uv
!uv sync
!uv run prepare.py --num-shards 2
!uv run train.py
```

**Résultat** : 1 expérience en 5 min, comprendre le concept

#### Étape 2 : POC (Cette Semaine)

**Kaggle ou Colab** :
- Lancer 10-15 expériences
- Observer l'amélioration du modèle
- Décider si ça vaut l'investissement

#### Étape 3 : Décision (Après Tests)

**Si convaincu** :
- Option A : Colab Pro ($10/mois) pour POC SaaS-IA
- Option B : RunPod pay-as-you-go pour intégration
- Option C : Achat GPU si volume > 1000 sessions/mois

**Si pas convaincu** :
- Coût total : €0
- Temps investi : 2-3h
- Connaissance acquise : Concept AutoResearch

### Scénario B : Vous Avez un GPU NVIDIA

#### Vérifier Compatibilité

```bash
# Vérifier GPU
nvidia-smi

# Vérifier CUDA
nvcc --version

# Vérifier VRAM disponible
nvidia-smi --query-gpu=memory.total --format=csv
```

**Si VRAM ≥ 16GB** :
- ✅ Configuration standard possible (avec ajustements)
- Suivre installation officielle

**Si VRAM < 16GB** :
- ⚠️ Configuration très allégée nécessaire
- Ou utiliser cloud pour tests sérieux

### Scénario C : Intégration dans SaaS-IA

#### Architecture Hybride Recommandée

```
SaaS-IA Backend (Local)
    ↓ API orchestration
GPU Cloud (RunPod/Paperspace)
    ↓ Résultats expériences
SaaS-IA Backend
    ↓ Stockage
PostgreSQL + Redis
```

**Avantages** :
- ✅ Pas d'investissement matériel initial
- ✅ Scalable selon demande
- ✅ Pay-as-you-go
- ✅ Maintenance GPU externalisée

**Coûts Estimés** :
- POC (100 sessions) : ~$10-20
- Production (1000 sessions/mois) : ~$100-150/mois
- Enterprise (5000 sessions/mois) : ~$500-750/mois

---

## 📋 Checklist de Compatibilité

### Pré-requis Minimum (Tests Gratuits)

- [ ] Compte Google/Kaggle (gratuit)
- [ ] Connexion internet stable
- [ ] 2-3h de temps disponible
- [ ] Compréhension basique Python

### Pré-requis Production (GPU Local)

- [ ] GPU NVIDIA avec CUDA support
- [ ] VRAM ≥ 16GB (24GB+ recommandé)
- [ ] Python 3.10+
- [ ] CUDA 12.8+ drivers
- [ ] 50GB+ espace disque libre
- [ ] 32GB+ RAM système
- [ ] Alimentation adéquate (750W+)

### Pré-requis Production (GPU Cloud)

- [ ] Budget cloud ($50-500/mois selon usage)
- [ ] Compte RunPod/Paperspace/AWS
- [ ] API integration dans SaaS-IA
- [ ] Monitoring et cost tracking

---

## 💡 Recommandations Finales - Accès

### Pour Découvrir AutoResearch (0-2 semaines)

**Utilisez Google Colab/Kaggle GRATUIT** :
- ✅ Coût : €0
- ✅ Temps : 2-3h
- ✅ Objectif : Comprendre et valider le concept
- ✅ Livrable : Décision go/no-go

### Pour POC SaaS-IA (2-8 semaines)

**Utilisez Colab Pro ou RunPod** :
- ✅ Coût : $10-50/mois
- ✅ Temps : 2-4 semaines dev
- ✅ Objectif : Module `auto_research` fonctionnel
- ✅ Livrable : Démo avec early adopters

### Pour Production (3+ mois)

**Décision Cloud vs Local** :
- Si < 1000 sessions/mois : **Cloud** (RunPod/AWS)
- Si > 1000 sessions/mois : **GPU Local** (RTX 4090)
- Si > 5000 sessions/mois : **GPU Pool Local** ou **Cloud dédié**

---

## �📝 Conclusion

AutoResearch représente une **opportunité majeure** pour SaaS-IA :

✅ **Innovation** : Concept unique et avant-gardiste  
✅ **Différenciation** : Feature que peu de concurrents ont  
✅ **Valeur** : Résout un vrai problème (optimisation ML)  
✅ **Scalabilité** : Architecture modulaire et extensible  
✅ **Monétisation** : Modèle de pricing clair (GPU usage)  

Le concept s'intègre **parfaitement** dans l'architecture existante de SaaS-IA :
- Pattern modulaire respecté
- Intégrations avec modules existants
- Réutilisation de l'infrastructure (Celery, Docker, etc.)
- Cohérence avec la vision "plateforme d'orchestration IA"

**Recommandation** : Commencer par le **module `auto_research`** en version POC, valider le concept, puis étendre progressivement vers `prompt_optimizer` et `ai_lab`.

---

**Prochaines Étapes** :

1. ✅ Valider l'intérêt business (ce document)
2. 🔲 Créer un POC technique (2 semaines)
3. 🔲 Tester avec des early adopters
4. 🔲 Décider du go/no-go pour la production
5. 🔲 Planifier le développement complet

---

*Document créé le 2026-04-08 par l'équipe SaaS-IA*
