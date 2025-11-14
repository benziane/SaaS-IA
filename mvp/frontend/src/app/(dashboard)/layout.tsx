/**
 * Dashboard Layout - Grade S++
 * Main dashboard layout with sidebar and navigation
 */

'use client';

import {
  AppBar,
  Avatar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Logout,
  Menu as MenuIcon,
  Person,
  Transcribe,
} from '@mui/icons-material';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { useState } from 'react';

import { useLogout } from '@/features/auth/hooks';
import { useAuthStore } from '@/lib/store';

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const DRAWER_WIDTH = 260;

const NAVIGATION_ITEMS = [
  {
    title: 'Dashboard',
    path: '/dashboard',
    icon: <DashboardIcon />,
  },
  {
    title: 'Transcriptions',
    path: '/transcription',
    icon: <Transcribe />,
  },
] as const;

/* ========================================================================
   TYPES
   ======================================================================== */

interface DashboardLayoutProps {
  children: ReactNode;
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function DashboardLayout({ children }: DashboardLayoutProps): JSX.Element {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const pathname = usePathname();
  
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  
  const user = useAuthStore(state => state.user);
  const logoutMutation = useLogout();
  
  /* Handlers */
  const handleDrawerToggle = (): void => {
    setMobileOpen(!mobileOpen);
  };
  
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>): void => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = (): void => {
    setAnchorEl(null);
  };
  
  const handleLogout = async (): Promise<void> => {
    handleMenuClose();
    await logoutMutation.mutateAsync();
  };
  
  /* Drawer Content */
  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo */}
      <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h5" component="h1" sx={{ fontWeight: 700, color: 'primary.main' }}>
          SaaS-IA
        </Typography>
        <Typography variant="caption" color="text.secondary">
          AI Platform
        </Typography>
      </Box>
      
      {/* Navigation */}
      <List sx={{ flex: 1, pt: 2 }}>
        {NAVIGATION_ITEMS.map(item => {
          const isActive = pathname === item.path;
          
          return (
            <ListItem key={item.path} disablePadding sx={{ px: 2, mb: 0.5 }}>
              <ListItemButton
                component={Link}
                href={item.path}
                selected={isActive}
                sx={{
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                  },
                }}
                aria-current={isActive ? 'page' : undefined}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.title} />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      
      {/* Footer */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary">
          Version 1.0.0
        </Typography>
      </Box>
    </Box>
  );
  
  /* ========================================================================
     RENDER
     ======================================================================== */
  
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Skip to main content - Accessibility S++ */}
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>
      
      {/* AppBar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          backgroundColor: 'background.paper',
          color: 'text.primary',
          boxShadow: 1,
        }}
      >
        <Toolbar>
          {/* Mobile Menu Button */}
          <IconButton
            color="inherit"
            aria-label="Open navigation menu"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          {/* Page Title */}
          <Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
            {NAVIGATION_ITEMS.find(item => item.path === pathname)?.title || 'Dashboard'}
          </Typography>
          
          {/* User Menu */}
          <IconButton
            onClick={handleMenuOpen}
            aria-label="User menu"
            aria-controls="user-menu"
            aria-haspopup="true"
            aria-expanded={Boolean(anchorEl)}
          >
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              {user?.email.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>
          
          <Menu
            id="user-menu"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            MenuListProps={{
              'aria-labelledby': 'user-menu',
            }}
          >
            <MenuItem disabled>
              <ListItemIcon>
                <Person fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={user?.email}
                secondary={user?.role}
                primaryTypographyProps={{ variant: 'body2' }}
                secondaryTypographyProps={{ variant: 'caption' }}
              />
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Logout" />
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      
      {/* Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
        aria-label="Main navigation"
      >
        {/* Mobile Drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
        >
          {drawer}
        </Drawer>
        
        {/* Desktop Drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      
      {/* Main Content */}
      <Box
        component="main"
        id="main-content"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: 8,
        }}
        role="main"
      >
        {children}
      </Box>
    </Box>
  );
}

