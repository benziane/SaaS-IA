'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Check } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
} from '@/lib/design-hub/components/Dialog';

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
    color: 'var(--accent)',
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
    color: 'var(--accent)',
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
    color: 'var(--accent)',
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
    <div className="text-center py-8 animate-in fade-in duration-500">
      <div
        className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6"
        style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
      >
        <i className="tabler-sparkles" style={{ fontSize: 36, color: 'var(--accent)' }} />
      </div>
      <h2 className="text-3xl font-bold mb-2 text-[var(--text-high)]">
        Bienvenue sur SaaS-IA !
      </h2>
      <h3 className="text-lg text-[var(--text-mid)] mb-4">
        {userName && `Bonjour ${userName},`}
      </h3>
      <p className="text-base text-[var(--text-mid)] max-w-[480px] mx-auto leading-relaxed">
        Votre plateforme d&apos;IA modulaire avec 37 modules. Transcription, generation de contenu,
        analyse de donnees, automatisation et bien plus — tout en un seul endroit.
      </p>
    </div>
  );
}

function StepUseCases({
  selectedUseCases,
  onToggle,
}: {
  selectedUseCases: string[];
  onToggle: (id: string) => void;
}) {
  return (
    <div className="py-4 animate-in fade-in duration-500">
      <h2 className="text-2xl font-bold mb-2 text-center text-[var(--text-high)]">
        Quel est votre cas d&apos;usage ?
      </h2>
      <p className="text-sm text-[var(--text-mid)] mb-6 text-center">
        Selectionnez un ou plusieurs domaines pour personnaliser votre experience.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {USE_CASE_OPTIONS.map((option) => {
          const isSelected = selectedUseCases.includes(option.id);
          return (
            <Card
              key={option.id}
              className={`cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg ${
                isSelected
                  ? 'border-2'
                  : 'border-2 border-[var(--border)]'
              }`}
              style={{
                borderColor: isSelected ? option.color : undefined,
                backgroundColor: isSelected ? `${option.color}0f` : undefined,
              }}
              onClick={() => onToggle(option.id)}
            >
              <div className="p-4">
                <div className="flex items-start gap-4">
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center shrink-0"
                    style={{ backgroundColor: `${option.color}26`, color: option.color }}
                  >
                    <i className={option.icon} style={{ fontSize: 24 }} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-base font-semibold text-[var(--text-high)]">
                        {option.label}
                      </h4>
                      <Checkbox
                        checked={isSelected}
                        tabIndex={-1}
                        className="pointer-events-none"
                        style={{ color: option.color } as React.CSSProperties}
                      />
                    </div>
                    <p className="text-sm text-[var(--text-mid)]">
                      {option.description}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function StepQuickTour({ selectedUseCases }: { selectedUseCases: string[] }) {
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
    <div className="py-4 animate-in fade-in duration-500">
      <h2 className="text-2xl font-bold mb-2 text-center text-[var(--text-high)]">
        Tour rapide
      </h2>
      <p className="text-sm text-[var(--text-mid)] mb-6 text-center">
        Voici les fonctionnalites recommandees pour vous.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {relevantFeatures.map((feature) => (
          <Card
            key={feature.title}
            className="h-full transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl animate-in fade-in duration-500"
          >
            <CardContent className="p-6 flex flex-col h-full">
              <div
                className="w-11 h-11 rounded-full flex items-center justify-center mb-3"
                style={{ backgroundColor: `${feature.color}26`, color: feature.color }}
              >
                <i className={feature.icon} style={{ fontSize: 22 }} />
              </div>
              <h4 className="text-base font-semibold mb-1 text-[var(--text-high)]">
                {feature.title}
              </h4>
              <p className="text-sm text-[var(--text-mid)] mb-4 flex-1">
                {feature.description}
              </p>
              <Button
                variant="outline"
                size="sm"
                asChild
                className="self-start"
                style={{ borderColor: feature.color, color: feature.color }}
              >
                <Link href={feature.href}>Essayer</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function StepProviders() {
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});

  return (
    <div className="py-4 animate-in fade-in duration-500">
      <h2 className="text-2xl font-bold mb-2 text-center text-[var(--text-high)]">
        Connectez vos providers IA
      </h2>
      <p className="text-sm text-[var(--text-mid)] mb-2 text-center">
        Vous pouvez commencer avec Gemini gratuitement.
      </p>
      <p className="text-xs text-[var(--text-low)] mb-6 text-center block">
        Les cles API sont stockees de maniere securisee et ne sont jamais partagees.
      </p>
      <div className="space-y-4">
        {PROVIDERS.map((provider) => (
          <Card
            key={provider.name}
            className="border border-[var(--border)] transition-all duration-200 hover:shadow-md"
          >
            <CardContent className="p-4">
              <div className={`flex items-center gap-4 ${provider.keyPlaceholder ? 'mb-3' : ''}`}>
                <div
                  className="w-11 h-11 rounded-full flex items-center justify-center shrink-0"
                  style={{ backgroundColor: `${provider.color}26`, color: provider.color }}
                >
                  <i className={provider.icon} style={{ fontSize: 22 }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-base font-semibold text-[var(--text-high)]">
                      {provider.name}
                    </h4>
                    {provider.free && (
                      <Badge variant="success" className="text-[0.7rem]">Gratuit</Badge>
                    )}
                  </div>
                  <p className="text-sm text-[var(--text-mid)]">
                    {provider.description}
                  </p>
                </div>
                {!provider.keyPlaceholder && (
                  <Badge variant="outline" className="gap-1 text-green-400 border-green-400/30">
                    <Check className="h-3 w-3" />
                    Configure
                  </Badge>
                )}
              </div>
              {provider.keyPlaceholder && (
                <div className="relative mt-1">
                  <i className="tabler-key absolute left-3 top-1/2 -translate-y-1/2" style={{ fontSize: 16, color: 'var(--text-low)' }} />
                  <Input
                    placeholder={provider.keyPlaceholder}
                    type="password"
                    value={apiKeys[provider.name] || ''}
                    onChange={(e) => setApiKeys((prev) => ({ ...prev, [provider.name]: e.target.value }))}
                    className="pl-9"
                  />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function StepReady({ onComplete }: { onComplete: () => void }) {
  const router = useRouter();
  const [dontShowAgain, setDontShowAgain] = useState(true);

  const quickActions = [
    { label: 'Transcrire une video', href: '/transcription', icon: 'tabler-microphone', color: 'var(--accent)' },
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
    <div className="text-center py-8 animate-in fade-in duration-500">
      <div
        className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6"
        style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
      >
        <i className="tabler-rocket" style={{ fontSize: 36, color: 'var(--success, #28c76f)' }} />
      </div>
      <h2 className="text-3xl font-bold mb-2 text-[var(--text-high)]">
        Votre plateforme est prete !
      </h2>
      <p className="text-base text-[var(--text-mid)] mb-8 max-w-[440px] mx-auto">
        Commencez par une action rapide ou explorez le dashboard complet.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 max-w-[560px] mx-auto">
        {quickActions.map((action) => (
          <Button
            key={action.label}
            variant="outline"
            asChild
            className="py-4 flex-col gap-2 h-auto border-[var(--border)] hover:border-current"
            onClick={onComplete}
          >
            <Link href={action.href}>
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${action.color}26`, color: action.color }}
              >
                <i className={action.icon} style={{ fontSize: 20 }} />
              </div>
              <span className="text-xs font-semibold normal-case">
                {action.label}
              </span>
            </Link>
          </Button>
        ))}
      </div>
      <Button
        size="lg"
        onClick={handleExplore}
        className="px-10 py-3 rounded-xl font-semibold mb-4 bg-[var(--accent)] text-[var(--bg-app)] hover:bg-[var(--accent-dim)]"
      >
        Explorer le dashboard
      </Button>
      <div className="flex items-center justify-center gap-2">
        <Checkbox
          id="dont-show"
          checked={dontShowAgain}
          onCheckedChange={(checked) => setDontShowAgain(checked === true)}
        />
        <label htmlFor="dont-show" className="text-xs text-[var(--text-low)] cursor-pointer">
          Ne plus afficher ce guide
        </label>
      </div>
    </div>
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
    <Dialog open={shouldShowWizard}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden p-0 gap-0">
        {/* Header with stepper */}
        <div className="px-4 sm:px-8 pt-6 pb-4 border-b border-[var(--border)] sticky top-0 bg-[var(--bg-surface)] z-10">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              <div
                className="w-8 h-8 rounded-md flex items-center justify-center"
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
              >
                <i className="tabler-sparkles" style={{ fontSize: 18, color: 'var(--accent)' }} />
              </div>
              <span className="text-base font-bold text-[var(--text-high)]">
                SaaS-IA
              </span>
            </div>
            {!isLastStep && (
              <Button
                variant="ghost"
                size="sm"
                onClick={completeOnboarding}
                className="text-[var(--text-low)]"
              >
                Passer l&apos;intro
              </Button>
            )}
          </div>
          {/* Step indicators */}
          <div className="flex items-center justify-between gap-2">
            {STEPS.map((label, index) => (
              <div key={label} className="flex flex-col items-center flex-1">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mb-1 transition-colors ${
                    index <= currentStep
                      ? 'bg-[var(--accent)] text-[var(--bg-app)]'
                      : 'bg-[var(--bg-elevated)] text-[var(--text-low)]'
                  }`}
                >
                  {index < currentStep ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                <span className="text-[0.65rem] sm:text-xs text-[var(--text-low)] text-center">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="px-4 sm:px-8 py-4 min-h-[320px] overflow-auto">
          {renderStep()}
        </div>

        {/* Footer navigation */}
        {!isLastStep && (
          <div className="px-4 sm:px-8 py-4 border-t border-[var(--border)] flex justify-between items-center sticky bottom-0 bg-[var(--bg-surface)] z-10">
            <Button
              variant="ghost"
              onClick={handleBack}
              disabled={currentStep === 0}
            >
              Retour
            </Button>
            <div className="flex gap-2">
              {currentStep === 3 && (
                <Button
                  variant="ghost"
                  onClick={handleSkip}
                  className="text-[var(--text-low)]"
                >
                  Passer
                </Button>
              )}
              <Button
                onClick={handleNext}
                className="px-8 font-semibold bg-[var(--accent)] text-[var(--bg-app)] hover:bg-[var(--accent-dim)]"
              >
                {currentStep === 0 ? 'Commencer' : 'Suivant'}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
