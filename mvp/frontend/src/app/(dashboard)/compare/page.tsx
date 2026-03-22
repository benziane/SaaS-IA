'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  FormGroup,
  Grid,
  Rating,
  TextField,
  Typography,
} from '@mui/material';

import { useRunComparison, useVoteComparison, useCompareStats } from '@/features/compare/hooks/useCompare';
import type { CompareResponse, ProviderResult } from '@/features/compare/types';

const AVAILABLE_PROVIDERS = [
  { id: 'gemini', label: 'Gemini Flash' },
  { id: 'claude', label: 'Claude Sonnet' },
  { id: 'groq', label: 'Groq Llama 70B' },
];

function ResultCard({
  result,
  comparisonId,
  onVoted,
}: {
  result: ProviderResult;
  comparisonId: string;
  onVoted: () => void;
}) {
  const voteMutation = useVoteComparison();
  const [voted, setVoted] = useState(false);

  const handleVote = (score: number | null) => {
    if (!score) return;
    voteMutation.mutate(
      { comparisonId, providerName: result.provider, qualityScore: score },
      {
        onSuccess: () => {
          setVoted(true);
          onVoted();
        },
      }
    );
  };

  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{result.provider}</Typography>
          <Chip
            label={`${result.response_time_ms}ms`}
            size="small"
            color={result.response_time_ms < 2000 ? 'success' : result.response_time_ms < 5000 ? 'warning' : 'error'}
            variant="outlined"
          />
        </Box>

        {result.error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {result.error}
          </Alert>
        ) : (
          <Typography
            variant="body2"
            sx={{
              whiteSpace: 'pre-wrap',
              maxHeight: 300,
              overflow: 'auto',
              mb: 2,
              p: 1,
              bgcolor: 'grey.50',
              borderRadius: 1,
            }}
          >
            {result.response}
          </Typography>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Rate:
          </Typography>
          <Rating
            value={0}
            onChange={(_, value) => handleVote(value)}
            disabled={voted || !!result.error}
            size="small"
          />
          {voted && (
            <Typography variant="caption" color="success.main">
              Voted
            </Typography>
          )}
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Model: {result.model}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function ComparePage() {
  const [prompt, setPrompt] = useState('');
  const [selectedProviders, setSelectedProviders] = useState<string[]>(['gemini', 'claude', 'groq']);
  const [comparison, setComparison] = useState<CompareResponse | null>(null);

  const runMutation = useRunComparison();
  const { data: stats } = useCompareStats();

  const handleToggleProvider = (providerId: string) => {
    setSelectedProviders((prev) =>
      prev.includes(providerId)
        ? prev.filter((p) => p !== providerId)
        : [...prev, providerId]
    );
  };

  const handleCompare = () => {
    if (!prompt.trim() || selectedProviders.length === 0) return;
    runMutation.mutate(
      { prompt: prompt.trim(), providers: selectedProviders },
      {
        onSuccess: (data) => setComparison(data),
      }
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Compare AI Models
      </Typography>

      {/* Input Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Enter your prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Write a prompt to compare across AI models..."
            sx={{ mb: 2 }}
          />

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <FormGroup row>
              {AVAILABLE_PROVIDERS.map((provider) => (
                <FormControlLabel
                  key={provider.id}
                  control={
                    <Checkbox
                      checked={selectedProviders.includes(provider.id)}
                      onChange={() => handleToggleProvider(provider.id)}
                    />
                  }
                  label={provider.label}
                />
              ))}
            </FormGroup>

            <Button
              variant="contained"
              onClick={handleCompare}
              disabled={runMutation.isPending || !prompt.trim() || selectedProviders.length === 0}
            >
              {runMutation.isPending ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />
                  Comparing...
                </>
              ) : (
                'Compare'
              )}
            </Button>
          </Box>

          {runMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {runMutation.error?.message || 'Comparison failed'}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results Section */}
      {comparison && (
        <>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Results
          </Typography>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {comparison.results.map((result, idx) => (
              <Grid item xs={12} md={12 / Math.min(comparison.results.length, 3)} key={idx}>
                <ResultCard
                  result={result}
                  comparisonId={comparison.id}
                  onVoted={() => {}}
                />
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {/* Stats Section */}
      {stats && stats.length > 0 && (
        <>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Provider Statistics
          </Typography>
          <Grid container spacing={2}>
            {stats.map((stat) => (
              <Grid item xs={12} sm={4} key={stat.provider}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {stat.provider}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Score: {stat.avg_score}/5
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Votes: {stat.total_votes}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Box>
  );
}
