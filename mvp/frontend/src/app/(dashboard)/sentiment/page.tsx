'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  LinearProgress,
  TextField,
  Typography,
} from '@mui/material';

import { useAnalyzeSentiment } from '@/features/agents/hooks/useAgents';
import type { SentimentResponse } from '@/features/agents/types';

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#4caf50',
  negative: '#f44336',
  neutral: '#9e9e9e',
};

const EMOTION_COLORS: Record<string, 'primary' | 'success' | 'error' | 'warning' | 'info' | 'default'> = {
  joy: 'success',
  anger: 'error',
  sadness: 'info',
  fear: 'warning',
  surprise: 'primary',
  trust: 'success',
  anticipation: 'primary',
  disgust: 'error',
};

function SentimentResult({ data }: { data: SentimentResponse }) {
  return (
    <Box>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" sx={{ color: SENTIMENT_COLORS[data.overall_sentiment], fontWeight: 700 }}>
                {data.overall_sentiment.toUpperCase()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Score: {data.overall_score.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Distribution</Typography>
              <Box sx={{ mb: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Positive</Typography>
                  <Typography variant="body2">{data.positive_percent}%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={data.positive_percent} color="success" sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              <Box sx={{ mb: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Negative</Typography>
                  <Typography variant="body2">{data.negative_percent}%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={data.negative_percent} color="error" sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Neutral</Typography>
                  <Typography variant="body2">{data.neutral_percent}%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={data.neutral_percent} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {Object.keys(data.emotion_summary).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Emotions Detected</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.entries(data.emotion_summary)
                .sort(([, a], [, b]) => b - a)
                .map(([emotion, count]) => (
                  <Chip key={emotion} label={`${emotion} (${count})`} color={EMOTION_COLORS[emotion] || 'default'} variant="outlined" />
                ))}
            </Box>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Typography variant="subtitle2" sx={{ mb: 2 }}>Segment Analysis</Typography>
          {data.segments.map((seg, i) => (
            <Box key={i} sx={{ mb: 1.5, p: 1, borderLeft: `4px solid ${SENTIMENT_COLORS[seg.sentiment]}`, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2">{seg.text}</Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                <Chip label={seg.sentiment} size="small" sx={{ bgcolor: SENTIMENT_COLORS[seg.sentiment], color: 'white' }} />
                <Typography variant="caption" color="text.secondary">Score: {seg.score.toFixed(2)}</Typography>
              </Box>
            </Box>
          ))}
        </CardContent>
      </Card>
    </Box>
  );
}

export default function SentimentPage() {
  const [text, setText] = useState('');
  const mutation = useAnalyzeSentiment();

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>Sentiment Analysis</Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            multiline
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste text to analyze sentiment..."
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            onClick={() => mutation.mutate(text)}
            disabled={!text.trim() || mutation.isPending}
          >
            {mutation.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Analyzing...</> : 'Analyze Sentiment'}
          </Button>
          {mutation.isError && <Alert severity="error" sx={{ mt: 2 }}>{mutation.error?.message}</Alert>}
        </CardContent>
      </Card>

      {mutation.data && <SentimentResult data={mutation.data} />}
    </Box>
  );
}
