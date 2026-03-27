'use client';

import { useState } from 'react';
import { Loader2, TrendingUp, SmilePlus, AlignLeft } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Textarea } from '@/lib/design-hub/components/Textarea';

import { useAnalyzeSentiment } from '@/features/agents/hooks/useAgents';
import type { SentimentResponse } from '@/features/agents/types';

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#4caf50',
  negative: '#f44336',
  neutral: '#9e9e9e',
};

const EMOTION_BADGE_VARIANTS: Record<string, 'default' | 'success' | 'destructive' | 'warning' | 'outline' | 'secondary'> = {
  joy: 'success',
  anger: 'destructive',
  sadness: 'outline',
  fear: 'warning',
  surprise: 'default',
  trust: 'success',
  anticipation: 'default',
  disgust: 'destructive',
};

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="relative h-2 w-full overflow-hidden rounded-full bg-[var(--bg-base)]">
      <div
        className="h-full transition-all duration-300 ease-in-out rounded-full"
        style={{ width: `${Math.max(0, Math.min(100, value))}%`, backgroundColor: color }}
      />
    </div>
  );
}

function SentimentResult({ data }: { data: SentimentResponse }) {
  return (
    <div className="space-y-4 animate-enter">
      <div className="grid grid-cols-1 md:grid-cols-[1fr_2fr] gap-4">
        {/* Overall verdict */}
        <div className="surface-card p-6 flex flex-col items-center justify-center text-center">
          <h2
            className="text-3xl font-bold mb-1"
            style={{ color: SENTIMENT_COLORS[data.overall_sentiment] }}
          >
            {data.overall_sentiment.toUpperCase()}
          </h2>
          <p className="text-sm text-[var(--text-mid)]">
            Score: {data.overall_score.toFixed(2)}
          </p>
        </div>

        {/* Distribution */}
        <div className="surface-card p-5">
          <h3 className="text-sm font-semibold text-[var(--text-high)] flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-[var(--accent)]" />
            Distribution
          </h3>
          <div className="mb-3">
            <div className="flex justify-between mb-1">
              <span className="text-sm text-[var(--text-high)]">Positive</span>
              <span className="text-sm text-[var(--text-high)]">{data.positive_percent}%</span>
            </div>
            <ProgressBar value={data.positive_percent} color="var(--accent)" />
          </div>
          <div className="mb-3">
            <div className="flex justify-between mb-1">
              <span className="text-sm text-[var(--text-high)]">Negative</span>
              <span className="text-sm text-[var(--text-high)]">{data.negative_percent}%</span>
            </div>
            <ProgressBar value={data.negative_percent} color="var(--error)" />
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-[var(--text-high)]">Neutral</span>
              <span className="text-sm text-[var(--text-high)]">{data.neutral_percent}%</span>
            </div>
            <ProgressBar value={data.neutral_percent} color="var(--text-low)" />
          </div>
        </div>
      </div>

      {/* Emotions */}
      {Object.keys(data.emotion_summary).length > 0 && (
        <div className="surface-card p-5">
          <h3 className="text-sm font-semibold text-[var(--text-high)] flex items-center gap-2 mb-3">
            <SmilePlus className="h-4 w-4 text-[var(--accent)]" />
            Emotions Detected
          </h3>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(data.emotion_summary)
              .sort(([, a], [, b]) => b - a)
              .map(([emotion, count]) => (
                <Badge
                  key={emotion}
                  variant={EMOTION_BADGE_VARIANTS[emotion] || 'outline'}
                >
                  {emotion} ({count})
                </Badge>
              ))}
          </div>
        </div>
      )}

      {/* Segment Analysis */}
      <div className="surface-card p-5">
        <h3 className="text-sm font-semibold text-[var(--text-high)] flex items-center gap-2 mb-4">
          <AlignLeft className="h-4 w-4 text-[var(--accent)]" />
          Segment Analysis
        </h3>
        <div className="space-y-3">
          {data.segments.map((seg, i) => (
            <div
              key={i}
              className="p-3 bg-[var(--bg-elevated)] rounded-[var(--radius-md,6px)]"
              style={{ borderLeft: `4px solid ${SENTIMENT_COLORS[seg.sentiment]}` }}
            >
              <p className="text-sm text-[var(--text-high)]">{seg.text}</p>
              <div className="flex gap-2 mt-1.5 items-center">
                <Badge
                  className="text-white"
                  style={{ backgroundColor: SENTIMENT_COLORS[seg.sentiment] }}
                >
                  {seg.sentiment}
                </Badge>
                <span className="text-xs text-[var(--text-mid)]">Score: {seg.score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function SentimentPage() {
  const [text, setText] = useState('');
  const mutation = useAnalyzeSentiment();

  return (
    <div className="p-5 space-y-5 animate-enter">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <TrendingUp className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Sentiment Analysis</h1>
          <p className="text-xs text-[var(--text-mid)]">Analyze tone, emotions, and sentiment distribution in any text</p>
        </div>
      </div>

      {/* Input Section */}
      <div className="surface-card p-5">
        <Textarea
          rows={5}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste text to analyze sentiment..."
          className="mb-4"
        />
        <Button
          onClick={() => mutation.mutate(text)}
          disabled={!text.trim() || mutation.isPending}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            'Analyze Sentiment'
          )}
        </Button>
        {mutation.isError && (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>{mutation.error?.message}</AlertDescription>
          </Alert>
        )}
      </div>

      {/* Results */}
      {mutation.data && <SentimentResult data={mutation.data} />}
    </div>
  );
}
