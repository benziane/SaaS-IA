/**
 * Form component for creating new transcription
 */
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { PlayArrow, Youtube } from '@mui/icons-material';
import { useCreateTranscription } from '@/hooks/useTranscription';
import { LanguageCode } from '@/types/transcription';

interface TranscriptionFormProps {
  onSuccess?: (transcription: any) => void;
}

const TranscriptionForm: React.FC<TranscriptionFormProps> = ({ onSuccess }) => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [language, setLanguage] = useState<LanguageCode>('auto');
  const { create, isLoading, error } = useCreateTranscription();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const transcription = await create(youtubeUrl, language);
      setYoutubeUrl('');

      if (onSuccess) {
        onSuccess(transcription);
      }
    } catch (err) {
      // Error is handled by the hook
    }
  };

  return (
    <Card elevation={3}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={3}>
          <Youtube color="error" sx={{ fontSize: 40, mr: 2 }} />
          <Typography variant="h5" component="h2">
            Nouvelle Transcription YouTube
          </Typography>
        </Box>

        <form onSubmit={handleSubmit}>
          <Box mb={3}>
            <TextField
              fullWidth
              label="URL de la vidéo YouTube"
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              required
              disabled={isLoading}
              variant="outlined"
              helperText="Collez l'URL complète de la vidéo YouTube à transcrire"
            />
          </Box>

          <Box mb={3}>
            <FormControl fullWidth>
              <InputLabel>Langue</InputLabel>
              <Select
                value={language}
                label="Langue"
                onChange={(e) => setLanguage(e.target.value as LanguageCode)}
                disabled={isLoading}
              >
                <MenuItem value="auto">Détection automatique</MenuItem>
                <MenuItem value="fr">Français</MenuItem>
                <MenuItem value="en">Anglais</MenuItem>
                <MenuItem value="ar">Arabe</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {error && (
            <Box mb={3}>
              <Alert severity="error">{error}</Alert>
            </Box>
          )}

          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            fullWidth
            disabled={isLoading || !youtubeUrl}
            startIcon={isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {isLoading ? 'Lancement en cours...' : 'Lancer la transcription'}
          </Button>
        </form>

        <Box mt={3}>
          <Typography variant="caption" color="text.secondary">
            Formats supportés : Toutes les vidéos YouTube publiques
            <br />
            Langues supportées : Français, Anglais, Arabe et 90+ autres langues
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TranscriptionForm;
