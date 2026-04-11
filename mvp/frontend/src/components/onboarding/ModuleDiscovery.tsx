'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/lib/design-hub/components/Input';
import { Tabs, TabsList, TabsTrigger } from '@/lib/design-hub/components/Tabs';

/* ========================================================================
   TYPES
   ======================================================================== */

interface ModuleInfo {
  name: string;
  description: string;
  icon: string;
  color: string;
  href: string;
  category: string;
  badge?: 'new' | 'popular';
}

/* ========================================================================
   DATA - 37 MODULES
   ======================================================================== */

const CATEGORIES = [
  { id: 'all', label: 'Tous' },
  { id: 'core', label: 'Core' },
  { id: 'content', label: 'Contenu' },
  { id: 'analysis', label: 'Analyse' },
  { id: 'automation', label: 'Automatisation' },
  { id: 'communication', label: 'Communication' },
  { id: 'development', label: 'Developpement' },
  { id: 'platform', label: 'Plateforme' },
];

const MODULES: ModuleInfo[] = [
  // Core (12)
  { name: 'Transcription', description: 'Transcription audio/video avec Whisper et AssemblyAI.', icon: 'tabler-microphone', color: 'var(--accent)', href: '/transcription', category: 'core', badge: 'popular' },
  { name: 'Conversation', description: 'Chat IA multi-provider avec historique et contexte.', icon: 'tabler-message-chatbot', color: '#28c76f', href: '/chat', category: 'core', badge: 'popular' },
  { name: 'Knowledge Base', description: 'Base de connaissances avec recherche hybride pgvector + TF-IDF.', icon: 'tabler-books', color: '#ffd93d', href: '/knowledge', category: 'core' },
  { name: 'Compare', description: 'Comparez les reponses de plusieurs providers IA en parallele.', icon: 'tabler-arrows-diff', color: '#ff9f43', href: '/compare', category: 'core' },
  { name: 'Pipelines', description: 'Pipelines de traitement chaines avec 15 types d\'etapes.', icon: 'tabler-git-branch', color: '#ea5455', href: '/pipelines', category: 'core' },
  { name: 'Agents', description: 'Agents IA autonomes avec 23 actions disponibles.', icon: 'tabler-robot', color: '#ff6b6b', href: '/agents', category: 'core' },
  { name: 'Sentiment', description: 'Analyse de sentiment avec RoBERTa et LLM.', icon: 'tabler-mood-happy', color: '#ffd93d', href: '/sentiment', category: 'core' },
  { name: 'Web Crawler', description: 'Crawling web intelligent avec Jina Reader API.', icon: 'tabler-world-download', color: '#7367f0', href: '/crawler', category: 'core' },
  { name: 'Workspaces', description: 'Espaces de travail collaboratifs multi-tenant.', icon: 'tabler-layout-dashboard', color: '#00cfe8', href: '/tenants', category: 'core' },
  { name: 'Billing', description: 'Gestion des abonnements et facturation.', icon: 'tabler-credit-card', color: '#28c76f', href: '/billing', category: 'core' },
  { name: 'API Keys', description: 'Gestion des cles API pour l\'acces programmatique.', icon: 'tabler-key', color: '#795548', href: '/api-docs', category: 'core' },
  { name: 'Cost Tracker', description: 'Suivi des couts par provider et par module.', icon: 'tabler-currency-dollar', color: '#4caf50', href: '/costs', category: 'core' },

  // Content (4)
  { name: 'Content Studio', description: 'Generation de contenu IA avec 10 formats differents.', icon: 'tabler-brush', color: '#7367f0', href: '/content-studio', category: 'content', badge: 'popular' },
  { name: 'Image Generation', description: 'Generation d\'images IA avec 10 styles et upscaling Real-ESRGAN.', icon: 'tabler-photo-ai', color: 'var(--accent)', href: '/images', category: 'content', badge: 'new' },
  { name: 'Video Generation', description: 'Generation de videos IA avec 6 types de contenus.', icon: 'tabler-video', color: '#e91e63', href: '/forms', category: 'content', badge: 'new' },
  { name: 'Presentations', description: 'Generation de presentations professionnelles avec l\'IA.', icon: 'tabler-presentation', color: '#ff5722', href: '/presentations', category: 'content', badge: 'new' },

  // Analysis (3)
  { name: 'Data Analyst', description: 'Analyse de donnees avec DuckDB, profiling et requetes NL.', icon: 'tabler-chart-dots-3', color: '#ff9f43', href: '/data', category: 'analysis', badge: 'popular' },
  { name: 'PDF Processor', description: 'Extraction et analyse de documents PDF.', icon: 'tabler-file-type-pdf', color: '#ea5455', href: '/pdf', category: 'analysis' },
  { name: 'Repo Analyzer', description: 'Analyse de repositories GitHub : architecture et metriques.', icon: 'tabler-git-merge', color: '#795548', href: '/repo-analyzer', category: 'analysis' },

  // Automation (3)
  { name: 'AI Workflows', description: 'Moteur DAG avec 19 actions, branches paralleles et templates.', icon: 'tabler-topology-star-3', color: '#00bcd4', href: '/pipeline-builder', category: 'automation', badge: 'new' },
  { name: 'Multi-Agent Crew', description: 'Equipes d\'agents IA collaboratifs avec 9 roles specialises.', icon: 'tabler-users-group', color: '#4caf50', href: '/crews', category: 'automation' },
  { name: 'Fine-Tuning', description: 'Entrainement de modeles personnalises avec LoRA et evaluation.', icon: 'tabler-adjustments', color: '#9c27b0', href: '/fine-tuning', category: 'automation', badge: 'new' },

  // Communication (4)
  { name: 'Voice Clone', description: 'Synthese vocale et clonage de voix avec Coqui TTS.', icon: 'tabler-volume', color: '#e91e63', href: '/audio-studio', category: 'communication' },
  { name: 'Realtime AI', description: 'Sessions voix/vision/meeting en temps reel avec LiveKit.', icon: 'tabler-broadcast', color: '#ff5722', href: '/realtime', category: 'communication', badge: 'new' },
  { name: 'Social Publisher', description: 'Publication automatisee sur les reseaux sociaux.', icon: 'tabler-share', color: '#1da1f2', href: '/social', category: 'communication' },
  { name: 'Chatbot Builder', description: 'Creez et deployez des chatbots personnalises.', icon: 'tabler-message-chatbot', color: '#00cfe8', href: '/chatbots', category: 'communication', badge: 'popular' },

  // Development (3)
  { name: 'Code Sandbox', description: 'Environnement d\'execution de code securise multi-langage.', icon: 'tabler-code', color: '#ff6b6b', href: '/sandbox', category: 'development' },
  { name: 'API Documentation', description: 'Documentation interactive de l\'API REST.', icon: 'tabler-file-code', color: '#607d8b', href: '/api-docs', category: 'development' },
  { name: 'Integrations', description: 'Connectez des services tiers et webhooks.', icon: 'tabler-plug', color: '#9e9e9e', href: '/integrations', category: 'development' },

  // Platform (6)
  { name: 'AI Monitoring', description: 'Observabilite LLM, traces et comparaison de providers.', icon: 'tabler-activity', color: '#f44336', href: '/monitoring', category: 'platform' },
  { name: 'Unified Search', description: 'Recherche cross-module avec RAG augmente.', icon: 'tabler-search', color: '#2196f3', href: '/search', category: 'platform' },
  { name: 'AI Memory', description: 'Memoire persistante et injection de contexte.', icon: 'tabler-brain', color: '#673ab7', href: '/memory', category: 'platform', badge: 'new' },
  { name: 'Security Guardian', description: 'Detection PII, protection injection, audit securite.', icon: 'tabler-shield-check', color: '#4caf50', href: '/security', category: 'platform' },
  { name: 'Marketplace', description: 'Templates, prompts et workflows partages par la communaute.', icon: 'tabler-shopping-cart', color: '#ff9800', href: '/marketplace', category: 'platform' },
  { name: 'Skill Seekers', description: 'Decouverte et partage de competences IA.', icon: 'tabler-target', color: '#3f51b5', href: '/skill-seekers', category: 'platform' },
  { name: 'Profile', description: 'Gestion du profil utilisateur et preferences.', icon: 'tabler-user', color: '#607d8b', href: '/profile', category: 'platform' },
];

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function ModuleDiscovery() {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredModules = useMemo(() => {
    let result = MODULES;

    if (selectedCategory !== 'all') {
      result = result.filter((m) => m.category === selectedCategory);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter(
        (m) =>
          m.name.toLowerCase().includes(query) ||
          m.description.toLowerCase().includes(query) ||
          m.category.toLowerCase().includes(query)
      );
    }

    return result;
  }, [selectedCategory, searchQuery]);

  const badgeColors: Record<string, { bg: string; text: string }> = {
    new: { bg: 'var(--accent)', text: 'var(--bg-app)' },
    popular: { bg: '#ff9f43', text: '#fff' },
  };

  return (
    <Card>
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
          >
            <i className="tabler-apps" style={{ fontSize: 20, color: '#fff' }} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold leading-tight text-[var(--text-high)]">
              Decouvrir les modules
            </h3>
            <p className="text-xs text-[var(--text-low)]">
              {MODULES.length} modules disponibles
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-low)]" />
          <Input
            placeholder="Rechercher un module..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Category Tabs */}
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="mb-4">
          <TabsList className="flex-wrap h-auto gap-1">
            {CATEGORIES.map((cat) => (
              <TabsTrigger key={cat.id} value={cat.id} className="text-xs px-3 py-1">
                {cat.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {/* Module Grid */}
        {filteredModules.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-[var(--text-low)]">
              Aucun module trouve pour &quot;{searchQuery}&quot;
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {filteredModules.map((module) => (
              <Card
                key={module.name}
                className="h-full relative border border-[var(--border)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
              >
                <Link
                  href={module.href}
                  className="p-4 h-full flex flex-col items-start justify-start"
                >
                  {/* Badge */}
                  {module.badge && (
                    <Badge
                      className="absolute top-2 right-2 text-[0.65rem] font-bold"
                      style={{
                        backgroundColor: badgeColors[module.badge]?.bg,
                        color: badgeColors[module.badge]?.text,
                      }}
                    >
                      {module.badge === 'new' ? 'Nouveau' : 'Populaire'}
                    </Badge>
                  )}

                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center mb-3"
                    style={{ backgroundColor: `${module.color}1f`, color: module.color }}
                  >
                    <i className={module.icon} style={{ fontSize: 20 }} />
                  </div>
                  <h4 className="text-sm font-semibold mb-1 text-[var(--text-high)]">
                    {module.name}
                  </h4>
                  <p className="text-xs text-[var(--text-mid)] leading-relaxed">
                    {module.description}
                  </p>
                </Link>
              </Card>
            ))}
          </div>
        )}

        {/* Footer count */}
        <div className="mt-4 text-center">
          <p className="text-xs text-[var(--text-low)]">
            {filteredModules.length} module{filteredModules.length !== 1 ? 's' : ''} affiche{filteredModules.length !== 1 ? 's' : ''}
            {selectedCategory !== 'all' && ` dans ${CATEGORIES.find((c) => c.id === selectedCategory)?.label}`}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
