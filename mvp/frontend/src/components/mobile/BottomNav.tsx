'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useMemo } from 'react';
import { LayoutDashboard, MessageSquare, Mic, BookOpen, MoreHorizontal } from 'lucide-react';

import { useIsMobile, useIsInstalled } from '@/hooks/useMobile';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Chat', icon: MessageSquare, path: '/chat' },
  { label: 'Transcription', icon: Mic, path: '/transcription' },
  { label: 'Knowledge', icon: BookOpen, path: '/knowledge' },
  { label: 'More', icon: MoreHorizontal, path: '/more' },
] as const;

export default function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const isMobile = useIsMobile();
  const isInstalled = useIsInstalled();

  const currentIndex = useMemo(() => {
    const idx = NAV_ITEMS.findIndex((item) => pathname.startsWith(item.path));
    return idx >= 0 ? idx : 0;
  }, [pathname]);

  // Only show on mobile or when running as installed PWA
  if (!isMobile && !isInstalled) {
    return null;
  }

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-[1300] border-t border-[var(--border)] bg-[var(--bg-surface)] shadow-[0_-2px_10px_rgba(0,0,0,0.3)]"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      <nav className="flex h-16 items-center justify-around">
        {NAV_ITEMS.map((item, index) => {
          const Icon = item.icon;
          const isActive = index === currentIndex;
          return (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              className={`flex flex-col items-center justify-center min-w-0 flex-1 py-1.5 transition-colors ${
                isActive
                  ? 'text-[var(--accent)]'
                  : 'text-[var(--text-low)] hover:text-[var(--text-mid)]'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span
                className={`mt-0.5 ${
                  isActive ? 'text-[0.7rem] font-medium' : 'text-[0.65rem]'
                }`}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
