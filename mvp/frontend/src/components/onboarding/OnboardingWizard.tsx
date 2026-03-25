'use client';

import { useMemo } from 'react';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Checkbox,
  Chip,
  Dialog,
  DialogContent,
  Fade,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { useOnboarding } from '@/hooks/useOnboarding';

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const STEPS = ['Bienvenue', 'Cas d\'usage', 'Tour rapide', 'Providers IA', 'Pret !'];

interface UseCaseOption {
  id: string;
  label: string;
  description: string;
  icon: string;
  color: string;
  modules: string[];
}

const USE_CASE_OPTIONS: UseCaseOption[] = [
  {
    id: 'content',
    label: 'Creation de contenu',
    description: 'Content Studio, Image Gen, Video Gen, Presentations',
    icon: 'tabler-brush',
    color: '#667eea',
    modules: ['content-studio', 'images', 'presentations', 'social'],
  },
  {
    id: 'analysis',
    label: 'Analyse de donnees',
    description: 'Data Analyst, PDF Processor, Repo Analyzer',
    icon: 'tabler-chart-bar',
    color: '#28c76f',
    modules: ['data', 'pdf', 'repo-analyzer'],
  },
  {
    id: 'automation',
    label: 'Automatisation',
    description: 'Pipelines, Workflows, Agents IA',
    icon: 'tabler-robot',
    color: '#ff9f43',
    modules: ['pipelines', 'agents', 'pipeline-builder'],
  },
  {
    id: 'communication',
    label: 'Communication',
    description: 'Conversation IA, Voice Clone, Social Publisher',
    icon: 'tabler-message-chatbot',
    color: '#00cfe8',
    modules: ['chat', 'audio-studio', 'social'],
  },
  {
    id: 'development',
    label: 'Developpement',
    description: 'Code Sandbox, Chatbot Builder, API Keys',
    icon: 'tabler-code',
    color: '#ea5455',
    modules: ['sandbox', 'chatbots', 'api-docs'],
  },
];

interface FeatureCard {
  title: string;
  description: string;
  icon: string;
  color: string;
  href: string;
  useCases: string[];
}

const FEATURE_CARDS: FeatureCard[] = [
  {
    title: 'Transcription IA',
    description: 'Transcrivez des videos YouTube, fichiers audio ou enregistrements en texte avec Whisper.',
    icon: 'tabler-microphone',
    color: '#667eea',
    href: '/transcription',
    useCases: ['content', 'communication'],
  },
  {
    title: 'Content Studio',
    description: 'Generez des articles, posts LinkedIn, threads Twitter et plus avec 10 formats differents.',
    icon: 'tabler-brush',
    color: '#7367f0',
    href: '/content-studio',
    useCases: ['content'],
  },
  {
    title: 'Agents IA Multi-Roles',
    description: 'Creez des equipes d\'agents IA collaboratifs avec 9 roles specialises.',
    icon: 'tabler-users-group',
    color: '#28c76f',
    href: '/crews',
    useCases: ['automation', 'development'],
  },
  {
    title: 'Data Analyst',
    description: 'Analysez vos donnees avec DuckDB, profiling automatique et requetes en langage naturel.',
    icon: 'tabler-chart-dots-3',
    color: '#ff9f43',
    href: '/data',
    useCases: ['analysis'],
  },
  {
    title: 'Pipeline Builder',
    description: 'Construisez des pipelines de traitement chaines avec 15 types d\'etapes.',
    icon: 'tabler-git-branch',
    color: '#ea5455',
    href: '/pipeline-builder',
    useCases: ['automation'],
  },
  {
    title: 'Chatbot Builder',
    description: 'Creez et deployez des chatbots personnalises alimentes par votre base de connaissances.',
    icon: 'tabler-message-chatbot',
    color: '#00cfe8',
    href: '/chatbots',
    useCases: ['communication', 'development'],
  },
  {
    title: 'Knowledge Base',
    description: 'Importez vos documents et interrogez-les avec la recherche hybride pgvector + TF-IDF.',
    icon: 'tabler-books',
    color: '#ffd93d',
    href: '/knowledge',
    useCases: ['analysis', 'content'],
  },
  {
    title: 'Code Sandbox',
    description: 'Executez du code Python, JavaScript et plus dans un environnement securise.',
    icon: 'tabler-code',
    color: '#ff6b6b',
    href: '/sandbox',
    useCases: ['development'],
  },
  {
    title: 'Image Generation',
    description: 'Generez des images IA avec 10 styles artistiques et upscaling Real-ESRGAN.',
    icon: 'tabler-photo-ai',
    color: '#764ba2',
    href: '/images',
    useCases: ['content'],
  },
  {
    title: 'Voice Clone',
    description: 'Clonez des voix et generez de la synthese vocale avec Coqui TTS et OpenAI.',
    icon: 'tabler-volume',
    color: '#e91e63',
    href: '/audio-studio',
    useCases: ['communication', 'content'],
  },
  {
    title: 'Security Guardian',
    description: 'Detection PII avec Presidio, protection injection et audit de securite.',
    icon: 'tabler-shield-check',
    color: '#4caf50',
    href: '/security',
    useCases: ['development'],
  },
  {
    title: 'Repo Analyzer',
    description: 'Analysez des repositories GitHub : architecture, qualite et metriques.',
    icon: 'tabler-git-merge',
    color: '#795548',
    href: '/repo-analyzer',
    useCases: ['analysis', 'development'],
  },
];

interface ProviderInfo {
  name: string;
  icon: string;
  color: string;
  free: boolean;
  description: string;
  keyPlaceholder?: string;
}

const PROVIDERS: ProviderInfo[] = [
  {
    name: 'Gemini',
    icon: 'tabler-diamond',
    color: '#4285f4',
    free: true,
    description: 'Gemini 2.0 Flash - rapide et gratuit pour commencer.',
  },
  {
    name: 'Claude',
    icon: 'tabler-brain',
    color: '#d97706',
    free: false,
    description: 'Claude Sonnet - excellent pour l\'analyse et la redaction.',
    keyPlaceholder: 'sk-ant-...',
  },
  {
    name: 'Groq',
    icon: 'tabler-bolt',
    color: '#f97316',
    free: true,
    description: 'Groq Llama 3.3 70B - inference ultra-rapide.',
  },
];

/* ========================================================================
   SUB-COMPONENTS
   ======================================================================== */

function StepWelcome({ userName }: { userName: string }) {
  return (
    <Fade in timeout={500}>
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 3,
          }}
        >
          <i className="tabler-sparkles" style={{ fontSize: 36, color: '#fff' }} />
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Bienvenue sur SaaS-IA !
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
          {userName && `Bonjour ${userName},`}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 480, mx: 'auto', lineHeight: 1.7 }}>
          Votre plateforme d&apos;IA modulaire avec 37 modules. Transcription, generation de contenu,
          analyse de donnees, automatisation et bien plus — tout en un seul endroit.
        </Typography>
      </Box>
    </Fade>
  );
}

function StepUseCases({
  selectedUseCases,
  onToggle,
}: {
  selectedUseCases: string[];
  onToggle: (id: string) => void;
}) {
  const theme = useTheme();

  return (
    <Fade in timeout={500}>
      <Box sx={{ py: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, textAlign: 'center' }}>
          Quel est votre cas d&apos;usage ?
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
          Selectionnez un ou plusieurs domaines pour personnaliser votre experience.
        </Typography>
        <Grid container spacing={2}>
          {USE_CASE_OPTIONS.map((option) => {
            const isSelected = selectedUseCases.includes(option.id);
            return (
              <Grid item xs={12} sm={6} key={option.id}>
                <Card
                  sx={{
                    border: 2,
                    borderColor: isSelected ? option.color : 'divider',
                    bgcolor: isSelected ? alpha(option.color, 0.06) : 'background.paper',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      borderColor: option.color,
                      transform: 'translateY(-2px)',
                      boxShadow: theme.shadows[4],
                    },
                  }}
                >
                  <CardActionArea onClick={() => onToggle(option.id)} sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                      <Avatar
                        sx={{
                          bgcolor: alpha(option.color, 0.15),
                          color: option.color,
                          width: 48,
                          height: 48,
                        }}
                      >
                        <i className={option.icon} style={{ fontSize: 24 }} />
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {option.label}
                          </Typography>
                          <Checkbox
                            checked={isSelected}
                            sx={{ color: option.color, '&.Mui-checked': { color: option.color } }}
                            tabIndex={-1}
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {option.description}
                        </Typography>
                      </Box>
                    </Box>
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </Box>
    </Fade>
  );
}

function StepQuickTour({ selectedUseCases }: { selectedUseCases: string[] }) {
  const theme = useTheme();

  const relevantFeatures = useMemo(() => {
    if (selectedUseCases.length === 0) {
      return FEATURE_CARDS.slice(0, 4);
    }
    const matched = FEATURE_CARDS.filter((f) =>
      f.useCases.some((uc) => selectedUseCases.includes(uc))
    );
    // Return up to 4 unique features, supplementing with defaults if needed
    const result = matched.slice(0, 4);
    if (result.length < 4) {
      const remaining = FEATURE_CARDS.filter((f) => !result.includes(f));
      result.push(...remaining.slice(0, 4 - result.length));
    }
    return result;
  }, [selectedUseCases]);

  return (
    <Fade in timeout={500}>
      <Box sx={{ py: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, textAlign: 'center' }}>
          Tour rapide
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
          Voici les fonctionnalites recommandees pour vous.
        </Typography>
        <Grid container spacing={2}>
          {relevantFeatures.map((feature, index) => (
            <Grid item xs={12} sm={6} key={feature.title}>
              <Fade in timeout={300 + index * 150}>
                <Card
                  sx={{
                    height: '100%',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: theme.shadows[6],
                    },
                  }}
                >
                  <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <Avatar
                      sx={{
                        bgcolor: alpha(feature.color, 0.15),
                        color: feature.color,
                        width: 44,
                        height: 44,
                        mb: 1.5,
                      }}
                    >
                      <i className={feature.icon} style={{ fontSize: 22 }} />
                    </Avatar>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, flex: 1 }}>
                      {feature.description}
                    </Typography>
                    <Button
                      variant="outlined"
                      size="small"
                      href={feature.href}
                      sx={{
                        borderColor: feature.color,
                        color: feature.color,
                        alignSelf: 'flex-start',
                        '&:hover': {
                          borderColor: feature.color,
                          bgcolor: alpha(feature.color, 0.08),
                        },
                      }}
                    >
                      Essayer
                    </Button>
                  </CardContent>
                </Card>
              </Fade>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Fade>
  );
}

function StepProviders() {
  const theme = useTheme();
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});

  return (
    <Fade in timeout={500}>
      <Box sx={{ py: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, textAlign: 'center' }}>
          Connectez vos providers IA
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1, textAlign: 'center' }}>
          Vous pouvez commencer avec Gemini gratuitement.
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mb: 3, textAlign: 'center', display: 'block' }}>
          Les cles API sont stockees de maniere securisee et ne sont jamais partagees.
        </Typography>
        <Stack spacing={2}>
          {PROVIDERS.map((provider) => (
            <Card
              key={provider.name}
              sx={{
                border: 1,
                borderColor: 'divider',
                transition: 'all 0.2s ease',
                '&:hover': { boxShadow: theme.shadows[3] },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: provider.keyPlaceholder ? 1.5 : 0 }}>
                  <Avatar
                    sx={{
                      bgcolor: alpha(provider.color, 0.15),
                      color: provider.color,
                      width: 44,
                      height: 44,
                    }}
                  >
                    <i className={provider.icon} style={{ fontSize: 22 }} />
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {provider.name}
                      </Typography>
                      {provider.free && (
                        <Chip label="Gratuit" size="small" color="success" sx={{ height: 20, fontSize: '0.7rem' }} />
                      )}
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {provider.description}
                    </Typography>
                  </Box>
                  {!provider.keyPlaceholder && (
                    <Chip
                      label="Configure"
                      size="small"
                      variant="outlined"
                      color="success"
                      icon={<i className="tabler-check" style={{ fontSize: 14 }} />}
                    />
                  )}
                </Box>
                {provider.keyPlaceholder && (
                  <TextField
                    fullWidth
                    size="small"
                    placeholder={provider.keyPlaceholder}
                    type="password"
                    value={apiKeys[provider.name] || ''}
                    onChange={(e) => setApiKeys((prev) => ({ ...prev, [provider.name]: e.target.value }))}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <i className="tabler-key" style={{ fontSize: 16 }} />
                        </InputAdornment>
                      ),
                    }}
                    sx={{ mt: 0.5 }}
                  />
                )}
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Box>
    </Fade>
  );
}

function StepReady({ onComplete }: { onComplete: () => void }) {
  const router = useRouter();
  const [dontShowAgain, setDontShowAgain] = useState(true);

  const quickActions = [
    { label: 'Transcrire une video', href: '/transcription', icon: 'tabler-microphone', color: '#667eea' },
    { label: 'Creer du contenu', href: '/content-studio', icon: 'tabler-brush', color: '#7367f0' },
    { label: 'Analyser des donnees', href: '/data', icon: 'tabler-chart-bar', color: '#28c76f' },
  ];

  const handleExplore = () => {
    if (dontShowAgain) {
      onComplete();
    }
    router.push('/dashboard');
  };

  return (
    <Fade in timeout={500}>
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #28c76f 0%, #48dbfb 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 3,
          }}
        >
          <i className="tabler-rocket" style={{ fontSize: 36, color: '#fff' }} />
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Votre plateforme est prete !
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 440, mx: 'auto' }}>
          Commencez par une action rapide ou explorez le dashboard complet.
        </Typography>
        <Grid container spacing={2} sx={{ mb: 4, maxWidth: 560, mx: 'auto' }}>
          {quickActions.map((action) => (
            <Grid item xs={12} sm={4} key={action.label}>
              <Button
                variant="outlined"
                href={action.href}
                fullWidth
                onClick={onComplete}
                sx={{
                  py: 2,
                  flexDirection: 'column',
                  gap: 1,
                  borderColor: 'divider',
                  '&:hover': {
                    borderColor: action.color,
                    bgcolor: alpha(action.color, 0.06),
                  },
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: alpha(action.color, 0.15),
                    color: action.color,
                    width: 40,
                    height: 40,
                  }}
                >
                  <i className={action.icon} style={{ fontSize: 20 }} />
                </Avatar>
                <Typography variant="caption" sx={{ fontWeight: 600, textTransform: 'none' }}>
                  {action.label}
                </Typography>
              </Button>
            </Grid>
          ))}
        </Grid>
        <Button
          variant="contained"
          size="large"
          onClick={handleExplore}
          sx={{
            px: 5,
            py: 1.5,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            fontWeight: 600,
            mb: 2,
          }}
        >
          Explorer le dashboard
        </Button>
        <Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                size="small"
              />
            }
            label={
              <Typography variant="caption" color="text.secondary">
                Ne plus afficher ce guide
              </Typography>
            }
          />
        </Box>
      </Box>
    </Fade>
  );
}

/* ========================================================================
   MAIN COMPONENT
   ======================================================================== */

interface OnboardingWizardProps {
  userName?: string;
}

export default function OnboardingWizard({ userName = '' }: OnboardingWizardProps) {
  const {
    shouldShowWizard,
    currentStep,
    selectedUseCases,
    setCurrentStep,
    toggleUseCase,
    completeOnboarding,
  } = useOnboarding();

  const theme = useTheme();

  if (!shouldShowWizard) {
    return null;
  }

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <StepWelcome userName={userName} />;
      case 1:
        return <StepUseCases selectedUseCases={selectedUseCases} onToggle={toggleUseCase} />;
      case 2:
        return <StepQuickTour selectedUseCases={selectedUseCases} />;
      case 3:
        return <StepProviders />;
      case 4:
        return <StepReady onComplete={completeOnboarding} />;
      default:
        return null;
    }
  };

  const isLastStep = currentStep === STEPS.length - 1;

  return (
    <Dialog
      open={shouldShowWizard}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          maxHeight: '90vh',
          overflow: 'hidden',
        },
      }}
    >
      <DialogContent sx={{ p: 0, overflow: 'auto' }}>
        {/* Header with stepper */}
        <Box
          sx={{
            px: { xs: 2, sm: 4 },
            pt: 3,
            pb: 2,
            borderBottom: 1,
            borderColor: 'divider',
            position: 'sticky',
            top: 0,
            bgcolor: 'background.paper',
            zIndex: 1,
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: 1.5,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <i className="tabler-sparkles" style={{ fontSize: 18, color: '#fff' }} />
              </Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                SaaS-IA
              </Typography>
            </Box>
            {!isLastStep && (
              <Button
                size="small"
                color="inherit"
                onClick={completeOnboarding}
                sx={{ color: 'text.secondary', textTransform: 'none' }}
              >
                Passer l&apos;intro
              </Button>
            )}
          </Box>
          <Stepper
            activeStep={currentStep}
            alternativeLabel
            sx={{
              '& .MuiStepLabel-label': { fontSize: { xs: '0.65rem', sm: '0.75rem' } },
            }}
          >
            {STEPS.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        {/* Content */}
        <Box sx={{ px: { xs: 2, sm: 4 }, py: 2, minHeight: 320 }}>
          {renderStep()}
        </Box>

        {/* Footer navigation */}
        {!isLastStep && (
          <Box
            sx={{
              px: { xs: 2, sm: 4 },
              py: 2,
              borderTop: 1,
              borderColor: 'divider',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              position: 'sticky',
              bottom: 0,
              bgcolor: 'background.paper',
              zIndex: 1,
            }}
          >
            <Button
              onClick={handleBack}
              disabled={currentStep === 0}
              sx={{ textTransform: 'none' }}
            >
              Retour
            </Button>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {currentStep === 3 && (
                <Button
                  onClick={handleSkip}
                  sx={{ textTransform: 'none', color: 'text.secondary' }}
                >
                  Passer
                </Button>
              )}
              <Button
                variant="contained"
                onClick={handleNext}
                sx={{
                  px: 4,
                  textTransform: 'none',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  fontWeight: 600,
                }}
              >
                {currentStep === 0 ? 'Commencer' : 'Suivant'}
              </Button>
            </Box>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}
