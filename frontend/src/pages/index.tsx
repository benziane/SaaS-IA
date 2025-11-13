/**
 * Main page for transcription creation and monitoring
 */
import React, { useState } from 'react';
import Head from 'next/head';
import {
  Container,
  Box,
  Typography,
  Grid,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  History,
  YouTube,
  Settings,
} from '@mui/icons-material';
import TranscriptionForm from '@/components/TranscriptionForm';
import TranscriptionStatus from '@/components/TranscriptionStatus';
import TranscriptionResult from '@/components/TranscriptionResult';
import { useTranscription } from '@/hooks/useTranscription';

export default function Home() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentTranscriptionId, setCurrentTranscriptionId] = useState<number | null>(null);

  const { transcription, mutate } = useTranscription(
    currentTranscriptionId,
    currentTranscriptionId !== null && transcription?.status !== 'completed' && transcription?.status !== 'failed'
  );

  const handleTranscriptionCreated = (newTranscription: any) => {
    setCurrentTranscriptionId(newTranscription.id);
    mutate();
  };

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <>
      <Head>
        <title>YouTube Transcription SaaS - Accueil</title>
        <meta name="description" content="Transcrivez vos vidéos YouTube automatiquement avec IA" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        {/* App Bar */}
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <IconButton
              color="inherit"
              edge="start"
              onClick={toggleDrawer}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <YouTube sx={{ mr: 2 }} />
            <Typography variant="h6" component="h1" sx={{ flexGrow: 1 }}>
              YouTube Transcription SaaS
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Sidebar Drawer */}
        <Drawer
          anchor="left"
          open={drawerOpen}
          onClose={toggleDrawer}
          sx={{
            '& .MuiDrawer-paper': {
              width: 260,
              boxSizing: 'border-box',
            },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              <ListItemButton selected>
                <ListItemIcon>
                  <Dashboard />
                </ListItemIcon>
                <ListItemText primary="Tableau de bord" />
              </ListItemButton>
              <ListItemButton>
                <ListItemIcon>
                  <History />
                </ListItemIcon>
                <ListItemText primary="Historique" />
              </ListItemButton>
              <ListItemButton>
                <ListItemIcon>
                  <Settings />
                </ListItemIcon>
                <ListItemText primary="Paramètres" />
              </ListItemButton>
            </List>
          </Box>
        </Drawer>

        {/* Main Content */}
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Toolbar />

          <Container maxWidth="lg">
            <Box my={4}>
              <Typography variant="h4" component="h2" gutterBottom fontWeight="bold">
                Transcription automatique de vidéos YouTube
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Transformez vos vidéos YouTube en texte avec notre intelligence artificielle
                multilingue de pointe. Correction automatique et formatage inclus.
              </Typography>
            </Box>

            <Grid container spacing={3}>
              {/* Transcription Form */}
              <Grid item xs={12} md={currentTranscriptionId ? 6 : 12}>
                <TranscriptionForm onSuccess={handleTranscriptionCreated} />
              </Grid>

              {/* Transcription Status */}
              {transcription && (
                <Grid item xs={12} md={6}>
                  <TranscriptionStatus transcription={transcription} />
                </Grid>
              )}

              {/* Transcription Result */}
              {transcription && transcription.status === 'completed' && (
                <Grid item xs={12}>
                  <TranscriptionResult transcription={transcription} />
                </Grid>
              )}
            </Grid>

            {/* Features Section */}
            {!currentTranscriptionId && (
              <Box my={8}>
                <Typography variant="h5" component="h3" gutterBottom fontWeight="bold" mb={4}>
                  Fonctionnalités
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center" p={3}>
                      <Typography variant="h6" gutterBottom>
                        🌍 Multilingue
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Support de plus de 90 langues incluant le français, l'anglais et l'arabe
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center" p={3}>
                      <Typography variant="h6" gutterBottom>
                        ✨ Correction IA
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Correction automatique de la ponctuation, grammaire et formatage
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center" p={3}>
                      <Typography variant="h6" gutterBottom>
                        ⚡ Ultra rapide
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Transcription en quelques minutes grâce à nos serveurs optimisés
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Container>
        </Box>
      </Box>
    </>
  );
}
