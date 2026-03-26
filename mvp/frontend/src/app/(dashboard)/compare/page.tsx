'use client';

import { useState } from 'react';
import { Loader2, Star } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Checkbox } from '@/components/ui/checkbox';

import { useRunComparison, useVoteComparison, useCompareStats } from '@/features/compare/hooks/useCompare';
import type { CompareResponse, ProviderResult } from '@/features/compare/types';

const AVAILABLE_PROVIDERS = [
  { id: 'gemini', label: 'Gemini Flash' },
  { id: 'claude', label: 'Claude Sonnet' },
  { id: 'groq', label: 'Groq Llama 70B' },
];

function StarRating({
  onChange,
  disabled,
}: {
  onChange: (value: number) => void;
  disabled: boolean;
}) {
  const [hover, setHover] = useState(0);
  const [selected, setSelected] = useState(0);

  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={disabled}
          title={`Rate ${star} star${star > 1 ? 's' : ''}`}
          aria-label={`Rate ${star} star${star > 1 ? 's' : ''}`}
          className="p-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
          onMouseEnter={() => !disabled && setHover(star)}
          onMouseLeave={() => !disabled && setHover(0)}
          onClick={() => {
            if (disabled) return;
            setSelected(star);
            onChange(star);
          }}
        >
          <Star
            className={`h-4 w-4 ${
              star <= (hover || selected)
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-[var(--text-low)]'
            }`}
          />
        </button>
      ))}
    </div>
  );
}

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

  const timeBadgeVariant = result.response_time_ms < 2000
    ? 'success'
    : result.response_time_ms < 5000
      ? 'warning'
      : 'destructive';

  return (
    <Card className="h-full">
      <CardContent className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-high)]">{result.provider}</h3>
          <Badge variant={timeBadgeVariant}>
            {result.response_time_ms}ms
          </Badge>
        </div>

        {result.error ? (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{result.error}</AlertDescription>
          </Alert>
        ) : (
          <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap max-h-[300px] overflow-auto mb-4 p-2 bg-[var(--bg-elevated)] rounded-[var(--radius-md,6px)]">
            {result.response}
          </p>
        )}

        <div className="flex items-center gap-2">
          <span className="text-sm text-[var(--text-mid)]">Rate:</span>
          <StarRating
            onChange={(value) => handleVote(value)}
            disabled={voted || !!result.error}
          />
          {voted && (
            <span className="text-xs text-green-400">Voted</span>
          )}
        </div>

        <span className="text-xs text-[var(--text-mid)] mt-2 block">
          Model: {result.model}
        </span>
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
    <div className="p-6">
      <h1 className="text-2xl font-bold text-[var(--text-high)] mb-6">
        Compare AI Models
      </h1>

      {/* Input Section */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <Textarea
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Write a prompt to compare across AI models..."
            className="mb-4"
          />

          <div className="flex justify-between items-center">
            <div className="flex gap-4">
              {AVAILABLE_PROVIDERS.map((provider) => (
                <label
                  key={provider.id}
                  className="flex items-center gap-2 text-sm text-[var(--text-high)] cursor-pointer"
                >
                  <Checkbox
                    checked={selectedProviders.includes(provider.id)}
                    onCheckedChange={() => handleToggleProvider(provider.id)}
                  />
                  {provider.label}
                </label>
              ))}
            </div>

            <Button
              onClick={handleCompare}
              disabled={runMutation.isPending || !prompt.trim() || selectedProviders.length === 0}
            >
              {runMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Comparing...
                </>
              ) : (
                'Compare'
              )}
            </Button>
          </div>

          {runMutation.isError && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>
                {runMutation.error?.message || 'Comparison failed'}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results Section */}
      {comparison && (
        <>
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">
            Results
          </h2>
          <div
            className="grid gap-6 mb-8"
            style={{
              gridTemplateColumns: `repeat(${Math.min(comparison.results.length, 3)}, minmax(0, 1fr))`,
            }}
          >
            {comparison.results.map((result, idx) => (
              <ResultCard
                key={idx}
                result={result}
                comparisonId={comparison.id}
                onVoted={() => {}}
              />
            ))}
          </div>
        </>
      )}

      {/* Stats Section */}
      {stats && stats.length > 0 && (
        <>
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">
            Provider Statistics
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {stats.map((stat) => (
              <Card key={stat.provider}>
                <CardContent className="p-6">
                  <h3 className="text-base font-semibold text-[var(--text-high)]">
                    {stat.provider}
                  </h3>
                  <p className="text-sm text-[var(--text-mid)]">
                    Avg Score: {stat.avg_score}/5
                  </p>
                  <p className="text-sm text-[var(--text-mid)]">
                    Total Votes: {stat.total_votes}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
