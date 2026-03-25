'use client';

import { useCallback, useRef, useState, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';

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
    <Box
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      sx={{ position: 'relative', overflow: 'auto', height: '100%' }}
    >
      {/* Pull indicator */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: pullDistance,
          overflow: 'hidden',
          transition: isPullingRef.current ? 'none' : 'height 0.2s ease',
          zIndex: 10,
        }}
      >
        {isRefreshing ? (
          <CircularProgress size={24} />
        ) : (
          <>
            <CircularProgress
              variant="determinate"
              value={progress}
              size={24}
              sx={{
                transition: 'none',
                transform: `rotate(${progress * 3.6}deg)`,
              }}
            />
            {pullDistance >= threshold && (
              <Typography variant="caption" sx={{ mt: 0.5, color: 'text.secondary' }}>
                Release to refresh
              </Typography>
            )}
          </>
        )}
      </Box>

      {/* Content shifted down by pull distance */}
      <Box
        sx={{
          transform: `translateY(${pullDistance}px)`,
          transition: isPullingRef.current ? 'none' : 'transform 0.2s ease',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
