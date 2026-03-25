'use client';

import {
  Avatar,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Grid,
  Typography,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import Link from 'next/link';

/* ========================================================================
   TYPES
   ======================================================================== */

interface QuickAction {
  title: string;
  description: string;
  icon: string;
  color: string;
  href: string;
}

/* ========================================================================
   DATA
   ======================================================================== */

const QUICK_ACTIONS: QuickAction[] = [
  {
    title: 'Transcrire',
    description: 'Transcrivez des videos YouTube ou des fichiers audio en texte.',
    icon: 'tabler-microphone',
    color: '#667eea',
    href: '/transcription',
  },
  {
    title: 'Generer du contenu',
    description: 'Creez des articles, posts LinkedIn, newsletters et plus.',
    icon: 'tabler-brush',
    color: '#7367f0',
    href: '/content-studio',
  },
  {
    title: 'Analyser des donnees',
    description: 'Importez des fichiers CSV/Excel et analysez avec l\'IA.',
    icon: 'tabler-chart-bar',
    color: '#28c76f',
    href: '/data',
  },
  {
    title: 'Creer un pipeline',
    description: 'Automatisez des taches avec des pipelines chaines.',
    icon: 'tabler-git-branch',
    color: '#ff9f43',
    href: '/pipelines',
  },
  {
    title: 'Deployer un chatbot',
    description: 'Construisez un chatbot IA personnalise en quelques minutes.',
    icon: 'tabler-message-chatbot',
    color: '#00cfe8',
    href: '/chatbots',
  },
  {
    title: 'Explorer le marketplace',
    description: 'Decouvrez des templates, prompts et workflows partages.',
    icon: 'tabler-shopping-cart',
    color: '#ea5455',
    href: '/marketplace',
  },
];

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function QuickActionsPanel() {
  const theme = useTheme();

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <i className="tabler-rocket" style={{ fontSize: 20, color: '#fff' }} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              Actions rapides
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Commencez par une de ces actions courantes
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {QUICK_ACTIONS.map((action) => (
            <Grid item xs={12} sm={6} md={4} key={action.title}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    borderColor: action.color,
                    transform: 'translateY(-2px)',
                    boxShadow: theme.shadows[4],
                  },
                }}
              >
                <CardActionArea
                  component={Link}
                  href={action.href}
                  sx={{
                    p: 2,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    justifyContent: 'flex-start',
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: alpha(action.color, 0.12),
                      color: action.color,
                      width: 44,
                      height: 44,
                      mb: 1.5,
                    }}
                  >
                    <i className={action.icon} style={{ fontSize: 22 }} />
                  </Avatar>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                    {action.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                    {action.description}
                  </Typography>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
}
