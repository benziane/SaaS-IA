'use client';

import { useState, useMemo } from 'react';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Grid,
  InputAdornment,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import Link from 'next/link';

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
  { name: 'Transcription', description: 'Transcription audio/video avec Whisper et AssemblyAI.', icon: 'tabler-microphone', color: '#667eea', href: '/transcription', category: 'core', badge: 'popular' },
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
  { name: 'Image Generation', description: 'Generation d\'images IA avec 10 styles et upscaling Real-ESRGAN.', icon: 'tabler-photo-ai', color: '#764ba2', href: '/images', category: 'content', badge: 'new' },
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
  const theme = useTheme();
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
    new: { bg: '#667eea', text: '#fff' },
    popular: { bg: '#ff9f43', text: '#fff' },
  };

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <i className="tabler-apps" style={{ fontSize: 20, color: '#fff' }} />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              Decouvrir les modules
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {MODULES.length} modules disponibles
            </Typography>
          </Box>
        </Box>

        {/* Search */}
        <TextField
          fullWidth
          size="small"
          placeholder="Rechercher un module..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <i className="tabler-search" style={{ fontSize: 18 }} />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        {/* Category Tabs */}
        <Tabs
          value={selectedCategory}
          onChange={(_, value) => setSelectedCategory(value)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            mb: 2,
            minHeight: 36,
            '& .MuiTab-root': {
              minHeight: 36,
              py: 0.5,
              px: 1.5,
              fontSize: '0.8rem',
              textTransform: 'none',
              fontWeight: 500,
            },
          }}
        >
          {CATEGORIES.map((cat) => (
            <Tab key={cat.id} value={cat.id} label={cat.label} />
          ))}
        </Tabs>

        {/* Module Grid */}
        {filteredModules.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Aucun module trouve pour &quot;{searchQuery}&quot;
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {filteredModules.map((module) => (
              <Grid item xs={12} sm={6} md={4} key={module.name}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    position: 'relative',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      borderColor: module.color,
                      transform: 'translateY(-2px)',
                      boxShadow: theme.shadows[4],
                    },
                  }}
                >
                  <CardActionArea
                    component={Link}
                    href={module.href}
                    sx={{
                      p: 2,
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      justifyContent: 'flex-start',
                    }}
                  >
                    {/* Badge */}
                    {module.badge && (
                      <Chip
                        label={module.badge === 'new' ? 'Nouveau' : 'Populaire'}
                        size="small"
                        sx={{
                          position: 'absolute',
                          top: 8,
                          right: 8,
                          height: 20,
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          bgcolor: badgeColors[module.badge].bg,
                          color: badgeColors[module.badge].text,
                        }}
                      />
                    )}

                    <Avatar
                      sx={{
                        bgcolor: alpha(module.color, 0.12),
                        color: module.color,
                        width: 40,
                        height: 40,
                        mb: 1.5,
                      }}
                    >
                      <i className={module.icon} style={{ fontSize: 20 }} />
                    </Avatar>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {module.name}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ fontSize: '0.78rem', lineHeight: 1.5 }}
                    >
                      {module.description}
                    </Typography>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Footer count */}
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {filteredModules.length} module{filteredModules.length !== 1 ? 's' : ''} affiche{filteredModules.length !== 1 ? 's' : ''}
            {selectedCategory !== 'all' && ` dans ${CATEGORIES.find((c) => c.id === selectedCategory)?.label}`}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}
