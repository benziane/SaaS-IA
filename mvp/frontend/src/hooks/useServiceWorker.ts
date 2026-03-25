'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface UseServiceWorkerReturn {
  /** Whether a new service worker version is available */
  updateAvailable: boolean;
  /** Whether the service worker is registered and active */
  isRegistered: boolean;
  /** Whether push notifications are supported and permission is granted */
  pushPermission: NotificationPermission | 'unsupported';
  /** Activate the waiting service worker (apply update) */
  update: () => void;
  /** Request push notification permission */
  requestPushPermission: () => Promise<NotificationPermission>;
  /** The active service worker registration */
  registration: ServiceWorkerRegistration | null;
}

export function useServiceWorker(): UseServiceWorkerReturn {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [isRegistered, setIsRegistered] = useState(false);
  const [pushPermission, setPushPermission] = useState<NotificationPermission | 'unsupported'>('unsupported');
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null);
  const waitingWorkerRef = useRef<ServiceWorker | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
      return;
    }

    // Check initial notification permission
    if ('Notification' in window) {
      setPushPermission(Notification.permission);
    }

    let updateIntervalId: ReturnType<typeof setInterval> | undefined;

    const registerSW = async () => {
      try {
        const reg = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
          updateViaCache: 'none',
        });

        setRegistration(reg);
        setIsRegistered(true);

        // Check if an update is already waiting
        if (reg.waiting) {
          waitingWorkerRef.current = reg.waiting;
          setUpdateAvailable(true);
        }

        // Listen for new service worker installing
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          if (!newWorker) return;

          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New version available
              waitingWorkerRef.current = newWorker;
              setUpdateAvailable(true);
            }
          });
        });

        // Check for updates periodically (every 60 minutes)
        updateIntervalId = setInterval(() => {
          reg.update().catch(() => {});
        }, 60 * 60 * 1000);

        // Store last sync time
        localStorage.setItem('saas-ia-last-sync', new Date().toISOString());
      } catch (err) {
        console.warn('[PWA] Service worker registration failed:', err);
      }
    };

    // Handle controller change (new SW activated)
    const onControllerChange = () => {
      window.location.reload();
    };

    navigator.serviceWorker.addEventListener('controllerchange', onControllerChange);
    registerSW();

    return () => {
      navigator.serviceWorker.removeEventListener('controllerchange', onControllerChange);
      if (updateIntervalId) clearInterval(updateIntervalId);
    };
  }, []);

  const update = useCallback(() => {
    const waitingWorker = waitingWorkerRef.current;
    if (!waitingWorker) return;

    waitingWorker.postMessage({ type: 'SKIP_WAITING' });
    setUpdateAvailable(false);
  }, []);

  const requestPushPermission = useCallback(async (): Promise<NotificationPermission> => {
    if (!('Notification' in window)) {
      return 'denied';
    }

    const permission = await Notification.requestPermission();
    setPushPermission(permission);
    return permission;
  }, []);

  return {
    updateAvailable,
    isRegistered,
    pushPermission,
    update,
    requestPushPermission,
    registration,
  };
}
