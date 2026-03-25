'use client';

import { useSyncExternalStore } from 'react';

/* ========================================================================
   useIsMobile - Viewport < 768px detection
   ======================================================================== */

function subscribeMobile(callback: () => void): () => void {
  const mql = window.matchMedia('(max-width: 767px)');
  mql.addEventListener('change', callback);
  return () => mql.removeEventListener('change', callback);
}

function getIsMobileSnapshot(): boolean {
  return window.matchMedia('(max-width: 767px)').matches;
}

function getIsMobileServerSnapshot(): boolean {
  return false;
}

export function useIsMobile(): boolean {
  return useSyncExternalStore(
    subscribeMobile,
    getIsMobileSnapshot,
    getIsMobileServerSnapshot,
  );
}

/* ========================================================================
   useIsInstalled - PWA standalone mode detection
   ======================================================================== */

function subscribeInstalled(callback: () => void): () => void {
  const mql = window.matchMedia('(display-mode: standalone)');
  mql.addEventListener('change', callback);
  return () => mql.removeEventListener('change', callback);
}

function getIsInstalledSnapshot(): boolean {
  if (typeof window === 'undefined') return false;
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as unknown as { standalone?: boolean }).standalone === true
  );
}

function getIsInstalledServerSnapshot(): boolean {
  return false;
}

export function useIsInstalled(): boolean {
  return useSyncExternalStore(
    subscribeInstalled,
    getIsInstalledSnapshot,
    getIsInstalledServerSnapshot,
  );
}

/* ========================================================================
   useOnlineStatus - Online/offline detection
   ======================================================================== */

function subscribeOnline(callback: () => void): () => void {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

function getOnlineSnapshot(): boolean {
  return navigator.onLine;
}

function getOnlineServerSnapshot(): boolean {
  return true;
}

export function useOnlineStatus(): boolean {
  return useSyncExternalStore(
    subscribeOnline,
    getOnlineSnapshot,
    getOnlineServerSnapshot,
  );
}
