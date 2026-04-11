'use client';

import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';

/* ========================================================================
   TYPES
   ======================================================================== */

interface QuickAction {
  title: string;
  description: string;
  icon: string;
  color: string;
  href: string;
}

/* ========================================================================
   DATA
   ======================================================================== */

const QUICK_ACTIONS: QuickAction[] = [
  {
    title: 'Transcrire',
    description: 'Transcrivez des videos YouTube ou des fichiers audio en texte.',
    icon: 'tabler-microphone',
    color: 'var(--accent)',
    href: '/transcription',
  },
  {
    title: 'Generer du contenu',
    description: 'Creez des articles, posts LinkedIn, newsletters et plus.',
    icon: 'tabler-brush',
    color: '#7367f0',
    href: '/content-studio',
  },
  {
    title: 'Analyser des donnees',
    description: 'Importez des fichiers CSV/Excel et analysez avec l\'IA.',
    icon: 'tabler-chart-bar',
    color: '#28c76f',
    href: '/data',
  },
  {
    title: 'Creer un pipeline',
    description: 'Automatisez des taches avec des pipelines chaines.',
    icon: 'tabler-git-branch',
    color: '#ff9f43',
    href: '/pipelines',
  },
  {
    title: 'Deployer un chatbot',
    description: 'Construisez un chatbot IA personnalise en quelques minutes.',
    icon: 'tabler-message-chatbot',
    color: '#00cfe8',
    href: '/chatbots',
  },
  {
    title: 'Explorer le marketplace',
    description: 'Decouvrez des templates, prompts et workflows partages.',
    icon: 'tabler-shopping-cart',
    color: '#ea5455',
    href: '/marketplace',
  },
];

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function QuickActionsPanel() {
  return (
    <Card className="mb-6">
      <CardContent className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: 'var(--accent)', color: 'var(--bg-app)' }}
          >
            <i className="tabler-rocket" style={{ fontSize: 20, color: '#fff' }} />
          </div>
          <div>
            <h3 className="text-lg font-bold leading-tight text-[var(--text-high)]">
              Actions rapides
            </h3>
            <p className="text-xs text-[var(--text-low)]">
              Commencez par une de ces actions courantes
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {QUICK_ACTIONS.map((action) => (
            <Card
              key={action.title}
              className="h-full border border-[var(--border)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
              style={{ '--hover-border': action.color } as React.CSSProperties}
            >
              <Link
                href={action.href}
                className="p-4 h-full flex flex-col items-start justify-start"
              >
                <div
                  className="w-11 h-11 rounded-full flex items-center justify-center mb-3"
                  style={{ backgroundColor: `${action.color}1f`, color: action.color }}
                >
                  <i className={action.icon} style={{ fontSize: 22 }} />
                </div>
                <h4 className="text-sm font-semibold mb-1 text-[var(--text-high)]">
                  {action.title}
                </h4>
                <p className="text-xs text-[var(--text-mid)] leading-relaxed">
                  {action.description}
                </p>
              </Link>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
