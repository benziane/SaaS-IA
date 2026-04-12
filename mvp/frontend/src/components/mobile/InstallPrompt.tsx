'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { X, Download } from 'lucide-react';
import { Button } from '@/lib/design-hub/components/Button';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';

import { useIsInstalled, useIsMobile } from '@/hooks/useMobile';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

const DISMISS_KEY = 'saas-ia-pwa-install-dismissed';
const DISMISS_DURATION_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

export default function InstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const deferredPromptRef = useRef<BeforeInstallPromptEvent | null>(null);
  const isInstalled = useIsInstalled();
  const isMobile = useIsMobile();

  useEffect(() => {
    if (isInstalled) return;

    // Check if user dismissed recently
    const dismissed = localStorage.getItem(DISMISS_KEY);
    if (dismissed) {
      const dismissedAt = parseInt(dismissed, 10);
      if (Date.now() - dismissedAt < DISMISS_DURATION_MS) {
        return;
      }
    }

    const handler = (e: Event) => {
      e.preventDefault();
      deferredPromptRef.current = e as BeforeInstallPromptEvent;
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, [isInstalled]);

  const handleInstall = useCallback(async () => {
    const prompt = deferredPromptRef.current;
    if (!prompt) return;

    await prompt.prompt();
    const { outcome } = await prompt.userChoice;

    if (outcome === 'accepted') {
      setShowPrompt(false);
    }

    deferredPromptRef.current = null;
  }, []);

  const handleDismiss = useCallback(() => {
    setShowPrompt(false);
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
    deferredPromptRef.current = null;
  }, []);

  if (!showPrompt || isInstalled) {
    return null;
  }

  return (
    <div
      className={`fixed z-[1400] transition-all duration-300 ${
        showPrompt ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0'
      } ${
        isMobile
          ? 'bottom-20 left-3 right-3'
          : 'bottom-6 right-6 max-w-[400px]'
      }`}
    >
      <Alert
        variant="info"
        className="relative rounded-xl shadow-[0_8px_32px_var(--shadow-overlay,rgba(0,0,0,0.3))] bg-[var(--accent)] text-[var(--accent-foreground)] border-[var(--accent)]"
      >
        <Download className="h-5 w-5" />
        <button
          onClick={handleDismiss}
          aria-label="Dismiss install prompt"
          className="absolute right-3 top-3 text-[var(--accent-foreground)] opacity-80 hover:opacity-100 transition-opacity focus-visible:ring-2 focus-visible:ring-[var(--accent-foreground)] focus-visible:outline-none rounded"
        >
          <X className="h-4 w-4" />
        </button>
        <AlertTitle className="font-bold text-white">
          Install SaaS-IA
        </AlertTitle>
        <AlertDescription className="text-white/90">
          <p className="text-sm mb-3">
            Add to your home screen for faster access and offline support.
          </p>
          <Button
            size="sm"
            onClick={handleInstall}
            className="bg-white/20 text-white hover:bg-white/30 border-0 font-semibold gap-2"
          >
            <Download className="h-4 w-4" />
            Install App
          </Button>
        </AlertDescription>
      </Alert>
    </div>
  );
}
