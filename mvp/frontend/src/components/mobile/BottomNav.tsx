'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useMemo } from 'react';

import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import Paper from '@mui/material/Paper';

import DashboardIcon from '@mui/icons-material/Dashboard';
import ChatIcon from '@mui/icons-material/Chat';
import MicIcon from '@mui/icons-material/Mic';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';

import { useIsMobile, useIsInstalled } from '@/hooks/useMobile';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { label: 'Chat', icon: <ChatIcon />, path: '/chat' },
  { label: 'Transcription', icon: <MicIcon />, path: '/transcription' },
  { label: 'Knowledge', icon: <MenuBookIcon />, path: '/knowledge' },
  { label: 'More', icon: <MoreHorizIcon />, path: '/more' },
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
    <Paper
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1300,
        borderTop: '1px solid',
        borderColor: 'divider',
        // Safe area inset for notched devices
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}
      elevation={8}
    >
      <BottomNavigation
        value={currentIndex}
        onChange={(_, newValue) => {
          const item = NAV_ITEMS[newValue as number];
          if (item) router.push(item.path);
        }}
        showLabels
        sx={{
          height: 64,
          '& .MuiBottomNavigationAction-root': {
            minWidth: 'auto',
            padding: '6px 0',
            '&.Mui-selected': {
              color: 'primary.main',
            },
          },
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.65rem',
            '&.Mui-selected': {
              fontSize: '0.7rem',
            },
          },
        }}
      >
        {NAV_ITEMS.map((item) => (
          <BottomNavigationAction
            key={item.path}
            label={item.label}
            icon={item.icon}
          />
        ))}
      </BottomNavigation>
    </Paper>
  );
}
