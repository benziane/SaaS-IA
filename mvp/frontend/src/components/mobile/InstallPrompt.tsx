'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Slide from '@mui/material/Slide';
import Typography from '@mui/material/Typography';

import CloseIcon from '@mui/icons-material/Close';
import GetAppIcon from '@mui/icons-material/GetApp';

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
    <Slide direction="up" in={showPrompt} mountOnEnter unmountOnExit>
      <Box
        sx={{
          position: 'fixed',
          bottom: isMobile ? 80 : 24,
          left: isMobile ? 12 : 'auto',
          right: isMobile ? 12 : 24,
          zIndex: 1400,
          maxWidth: isMobile ? 'none' : 400,
        }}
      >
        <Alert
          severity="info"
          variant="filled"
          icon={<GetAppIcon />}
          action={
            <IconButton
              size="small"
              color="inherit"
              onClick={handleDismiss}
              aria-label="Dismiss install prompt"
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          }
          sx={{
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
            '& .MuiAlert-message': { width: '100%' },
          }}
        >
          <Typography variant="subtitle2" fontWeight={700} gutterBottom>
            Install SaaS-IA
          </Typography>
          <Typography variant="body2" sx={{ mb: 1.5, opacity: 0.9 }}>
            Add to your home screen for faster access and offline support.
          </Typography>
          <Button
            variant="contained"
            size="small"
            onClick={handleInstall}
            startIcon={<GetAppIcon />}
            sx={{
              bgcolor: 'rgba(255,255,255,0.2)',
              color: 'inherit',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
              textTransform: 'none',
              fontWeight: 600,
            }}
          >
            Install App
          </Button>
        </Alert>
      </Box>
    </Slide>
  );
}
