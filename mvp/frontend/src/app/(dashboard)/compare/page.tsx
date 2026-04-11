'use client';

import { useState } from 'react';
import { Loader2, Star, Scale, BarChart3, Zap } from 'lucide-react';
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

function SpeedDot({ ms }: { ms: number }) {
  const color =
    ms < 2000
      ? 'bg-green-400'
      : ms < 5000
        ? 'bg-yellow-400'
        : 'bg-red-400';
  return <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${color}`} title={`${ms}ms`} />;
}

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

  return (
    <div className="surface-card p-6 h-full flex flex-col animate-enter">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-base font-semibold text-[var(--text-high)]">{result.provider}</h3>
        <div className="flex items-center gap-2">
          <SpeedDot ms={result.response_time_ms} />
          <span className="text-xs text-[var(--text-mid)]">{result.response_time_ms}ms</span>
        </div>
      </div>

      {result.error ? (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{result.error}</AlertDescription>
        </Alert>
      ) : (
        <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap max-h-[300px] overflow-auto mb-4 p-3 bg-[var(--bg-elevated)] rounded-[var(--radius-md,6px)] flex-1">
          {result.response}
        </p>
      )}

      <div className="flex items-center gap-2 mt-auto">
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
    </div>
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
    <div className="p-5 space-y-5 animate-enter">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Scale className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Compare AI Models</h1>
          <p className="text-xs text-[var(--text-mid)]">Run the same prompt across providers and vote for the best response</p>
        </div>
      </div>

      {/* Input Section */}
      <div className="surface-card p-5">
        <Textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Write a prompt to compare across AI models..."
          className="mb-4"
        />

        <div className="flex flex-wrap justify-between items-center gap-4">
          <div className="flex gap-4 flex-wrap">
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
      </div>

      {/* Results Section */}
      {comparison && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-[var(--text-high)] flex items-center gap-2">
            <Zap className="h-4 w-4 text-[var(--accent)]" />
            Results
          </h2>
          <div
            className="grid gap-5"
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
        </div>
      )}

      {/* Stats Section */}
      {stats && stats.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-[var(--text-high)] flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-[var(--accent)]" />
            Provider Statistics
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {stats.map((stat) => (
              <div key={stat.provider} className="surface-card p-5">
                <h3 className="text-sm font-semibold text-[var(--text-high)] mb-2">{stat.provider}</h3>
                <p className="text-xs text-[var(--text-mid)]">Avg Score: <span className="text-[var(--text-high)] font-medium">{stat.avg_score}/5</span></p>
                <p className="text-xs text-[var(--text-mid)]">Total Votes: <span className="text-[var(--text-high)] font-medium">{stat.total_votes}</span></p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
