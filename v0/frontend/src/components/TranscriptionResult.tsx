/**
 * Component for displaying transcription result
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  IconButton,
  Snackbar,
  Alert,
} from '@mui/material';
import { ContentCopy, Download } from '@mui/icons-material';
import { Transcription } from '@/types/transcription';

interface TranscriptionResultProps {
  transcription: Transcription;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`transcription-tabpanel-${index}`}
      aria-labelledby={`transcription-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const TranscriptionResult: React.FC<TranscriptionResultProps> = ({ transcription }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setSnackbarOpen(true);
  };

  const handleDownload = (text: string, filename: string) => {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const hasRawTranscript = !!transcription.raw_transcript;
  const hasCorrectedTranscript = !!transcription.corrected_transcript;

  if (!hasRawTranscript && !hasCorrectedTranscript) {
    return null;
  }

  return (
    <>
      <Card elevation={2}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" component="h3">
              Résultat de la transcription
            </Typography>
            <Box>
              {hasCorrectedTranscript && (
                <>
                  <IconButton
                    onClick={() => handleCopy(transcription.corrected_transcript!)}
                    title="Copier"
                  >
                    <ContentCopy />
                  </IconButton>
                  <IconButton
                    onClick={() =>
                      handleDownload(
                        transcription.corrected_transcript!,
                        `transcription_${transcription.video_id}.txt`
                      )
                    }
                    title="Télécharger"
                  >
                    <Download />
                  </IconButton>
                </>
              )}
            </Box>
          </Box>

          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            {hasCorrectedTranscript && (
              <Tab label="Transcription corrigée" id="transcription-tab-0" />
            )}
            {hasRawTranscript && (
              <Tab
                label="Transcription brute"
                id={`transcription-tab-${hasCorrectedTranscript ? 1 : 0}`}
              />
            )}
          </Tabs>

          {hasCorrectedTranscript && (
            <TabPanel value={activeTab} index={0}>
              <Box
                sx={{
                  maxHeight: '500px',
                  overflowY: 'auto',
                  backgroundColor: 'background.default',
                  p: 2,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                <Typography variant="body1" component="pre" sx={{ margin: 0 }}>
                  {transcription.corrected_transcript}
                </Typography>
              </Box>
            </TabPanel>
          )}

          {hasRawTranscript && (
            <TabPanel value={activeTab} index={hasCorrectedTranscript ? 1 : 0}>
              <Box
                sx={{
                  maxHeight: '500px',
                  overflowY: 'auto',
                  backgroundColor: 'background.default',
                  p: 2,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                <Typography variant="body1" component="pre" sx={{ margin: 0 }}>
                  {transcription.raw_transcript}
                </Typography>
              </Box>
            </TabPanel>
          )}
        </CardContent>
      </Card>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbarOpen(false)} severity="success">
          Texte copié dans le presse-papiers !
        </Alert>
      </Snackbar>
    </>
  );
};

export default TranscriptionResult;
