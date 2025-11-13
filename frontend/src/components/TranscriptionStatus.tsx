/**
 * Component for displaying transcription status and progress
 */
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Alert,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  HourglassEmpty,
  CloudDownload,
  Translate,
  AutoFixHigh,
} from '@mui/icons-material';
import { Transcription, TranscriptionStatus as Status } from '@/types/transcription';

interface TranscriptionStatusProps {
  transcription: Transcription;
}

const statusConfig: Record<Status, { label: string; color: any; icon: React.ReactNode }> = {
  pending: {
    label: 'En attente',
    color: 'default',
    icon: <HourglassEmpty />,
  },
  downloading: {
    label: 'Téléchargement',
    color: 'info',
    icon: <CloudDownload />,
  },
  extracting: {
    label: 'Extraction audio',
    color: 'info',
    icon: <CloudDownload />,
  },
  transcribing: {
    label: 'Transcription',
    color: 'primary',
    icon: <Translate />,
  },
  post_processing: {
    label: 'Correction',
    color: 'secondary',
    icon: <AutoFixHigh />,
  },
  completed: {
    label: 'Terminé',
    color: 'success',
    icon: <CheckCircle />,
  },
  failed: {
    label: 'Échec',
    color: 'error',
    icon: <Error />,
  },
};

const TranscriptionStatus: React.FC<TranscriptionStatusProps> = ({ transcription }) => {
  const config = statusConfig[transcription.status];

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card elevation={2}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" component="h3">
            Statut de la transcription
          </Typography>
          <Chip
            icon={config.icon}
            label={config.label}
            color={config.color}
            variant="filled"
          />
        </Box>

        {transcription.video_title && (
          <>
            <Typography variant="subtitle1" gutterBottom>
              {transcription.video_title}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Chaîne : {transcription.channel_name || 'Inconnue'}
            </Typography>
          </>
        )}

        <Box my={3}>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2" color="text.secondary">
              Progression
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {transcription.progress}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={transcription.progress}
            color={config.color}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Durée vidéo
            </Typography>
            <Typography variant="body2">
              {formatDuration(transcription.video_duration)}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Langue
            </Typography>
            <Typography variant="body2">
              {transcription.detected_language || transcription.language || 'Auto'}
            </Typography>
          </Box>
          {transcription.processing_time && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Temps de traitement
              </Typography>
              <Typography variant="body2">
                {transcription.processing_time.toFixed(1)}s
              </Typography>
            </Box>
          )}
          {transcription.confidence_score && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Confiance
              </Typography>
              <Typography variant="body2">
                {(transcription.confidence_score * 100).toFixed(1)}%
              </Typography>
            </Box>
          )}
        </Box>

        {transcription.error_message && (
          <Box mt={2}>
            <Alert severity="error">
              <Typography variant="body2">{transcription.error_message}</Typography>
            </Alert>
          </Box>
        )}

        {transcription.status === 'completed' && transcription.word_count && (
          <Box mt={2}>
            <Alert severity="success">
              Transcription terminée avec succès ! {transcription.word_count} mots générés.
            </Alert>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default TranscriptionStatus;
