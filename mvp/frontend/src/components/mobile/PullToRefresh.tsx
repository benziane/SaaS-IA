'use client';

import { useCallback, useRef, useState, type ReactNode } from 'react';
import { Spinner } from '@/components/ui/spinner';

import { useIsMobile } from '@/hooks/useMobile';

interface PullToRefreshProps {
  children: ReactNode;
  onRefresh: () => Promise<void>;
  /** Pull distance threshold in pixels to trigger refresh (default: 80) */
  threshold?: number;
  /** Maximum pull distance in pixels (default: 120) */
  maxPull?: number;
}

export default function PullToRefresh({
  children,
  onRefresh,
  threshold = 80,
  maxPull = 120,
}: PullToRefreshProps) {
  const isMobile = useIsMobile();
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const startYRef = useRef(0);
  const isPullingRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (!containerRef.current || isRefreshing) return;
    // Only allow pull-to-refresh when scrolled to top
    if (containerRef.current.scrollTop > 0) return;
    startYRef.current = e.touches[0]!.clientY;
    isPullingRef.current = true;
  }, [isRefreshing]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isPullingRef.current || isRefreshing) return;
    const currentY = e.touches[0]!.clientY;
    const diff = currentY - startYRef.current;

    if (diff > 0) {
      // Apply resistance: the further you pull, the harder it gets
      const distance = Math.min(diff * 0.5, maxPull);
      setPullDistance(distance);
    }
  }, [isRefreshing, maxPull]);

  const handleTouchEnd = useCallback(async () => {
    if (!isPullingRef.current || isRefreshing) return;
    isPullingRef.current = false;

    if (pullDistance >= threshold) {
      setIsRefreshing(true);
      setPullDistance(threshold * 0.5);
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }
  }, [pullDistance, threshold, isRefreshing, onRefresh]);

  if (!isMobile) {
    return <>{children}</>;
  }

  const progress = Math.min((pullDistance / threshold) * 100, 100);

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className="relative overflow-auto h-full"
    >
      {/* Pull indicator */}
      <div
        className="absolute top-0 left-0 right-0 flex flex-col items-center justify-center overflow-hidden z-10"
        style={{
          height: pullDistance,
          transition: isPullingRef.current ? 'none' : 'height 0.2s ease',
        }}
      >
        {isRefreshing ? (
          <Spinner size={24} />
        ) : (
          <>
            <svg
              className="animate-spin text-[var(--accent)]"
              width={24}
              height={24}
              viewBox="0 0 24 24"
              fill="none"
              style={{
                transition: 'none',
                transform: `rotate(${progress * 3.6}deg)`,
              }}
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                strokeDasharray={`${progress} 100`}
              />
            </svg>
            {pullDistance >= threshold && (
              <span className="mt-1 text-xs text-[var(--text-low)]">
                Release to refresh
              </span>
            )}
          </>
        )}
      </div>

      {/* Content shifted down by pull distance */}
      <div
        style={{
          transform: `translateY(${pullDistance}px)`,
          transition: isPullingRef.current ? 'none' : 'transform 0.2s ease',
        }}
      >
        {children}
      </div>
    </div>
  );
}
