'use client';

import { useState } from 'react';
import { Search, Sparkles, Loader2 } from 'lucide-react';

import { Badge } from '@/lib/design-hub/components/Badge';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';

import apiClient from '@/lib/apiClient';

interface SearchResultItem {
  id: string; type: string; title: string; content: string;
  score: number; url: string; _module: string;
  [key: string]: unknown;
}

const MODULE_ICONS: Record<string, string> = {
  transcriptions: '\uD83C\uDFA4', knowledge: '\uD83D\uDCDA', content: '\u2728', conversations: '\uD83D\uDCAC',
};
const MODULE_COLORS: Record<string, string> = {
  transcriptions: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  knowledge: 'bg-green-500/10 text-green-400 border-green-500/30',
  content: 'bg-pink-500/10 text-pink-400 border-pink-500/30',
  conversations: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
};

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [facets, setFacets] = useState<Record<string, number>>({});
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true); setAnswer('');
    try {
      const resp = await apiClient.get('/api/search/', { params: { q: query } });
      setResults(resp.data.results || []);
      setFacets(resp.data.facets || {});
      setTotal(resp.data.total || 0);
    } catch { setResults([]); }
    setLoading(false);
  };

  const handleAskAnswer = async () => {
    if (!query.trim()) return;
    setAnswerLoading(true);
    try {
      const resp = await apiClient.get('/api/search/answer', { params: { q: query } });
      setAnswer(resp.data.answer || '');
      if (!results.length && resp.data.sources) {
        setResults(resp.data.sources);
        setFacets(resp.data.facets || {});
      }
    } catch { setAnswer('Failed to generate answer.'); }
    setAnswerLoading(false);
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <Search className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Universal Search</h1>
          <p className="text-xs text-[var(--text-mid)]">Search across all platform data: transcriptions, documents, content, conversations</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="surface-card p-5">
        <div className="flex gap-2">
          <Input
            className="flex-1"
            placeholder="Search across all your platform data..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
          />
          <Button
            onClick={handleSearch}
            disabled={!query.trim() || loading}
          >
            {loading
              ? <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              : <Search className="h-4 w-4 mr-1" />}
            Search
          </Button>
          <Button
            variant="outline"
            onClick={handleAskAnswer}
            disabled={!query.trim() || answerLoading}
          >
            {answerLoading
              ? <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              : <Sparkles className="h-4 w-4 mr-1" />}
            Ask AI
          </Button>
        </div>
      </div>

      {/* AI Answer */}
      {answer && (
        <div className="surface-card p-5 bg-[var(--bg-elevated)]">
          <h4 className="text-sm font-semibold mb-2 flex items-center gap-1">
            <Sparkles className="h-4 w-4 text-[var(--accent)]" /> AI Answer
          </h4>
          <p className="text-sm whitespace-pre-wrap">{answer}</p>
        </div>
      )}

      {/* Facets + Results */}
      {total > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {/* Facets */}
          <div className="md:col-span-1">
            <div className="surface-card p-5">
              <h4 className="text-sm font-semibold mb-2">Sources ({total} results)</h4>
              {Object.entries(facets).map(([module, count]) => (
                <div key={module} className="flex justify-between items-center mb-1.5">
                  <Badge
                    variant="outline"
                    className={MODULE_COLORS[module] || 'bg-[var(--bg-elevated)]'}
                  >
                    {MODULE_ICONS[module] || '\uD83D\uDCC4'} {module}
                  </Badge>
                  <span className="text-sm font-bold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Results */}
          <div className="md:col-span-3 space-y-2">
            {results.map((r, i) => (
              <div key={i} className="surface-card px-4 py-3">
                <div className="flex items-center gap-2 mb-1">
                  <Badge
                    variant="outline"
                    className={MODULE_COLORS[r._module] || 'bg-[var(--bg-elevated)]'}
                  >
                    {MODULE_ICONS[r._module] || '\uD83D\uDCC4'} {r._module}
                  </Badge>
                  <span className="text-sm font-semibold">{r.title}</span>
                  <Badge variant="outline" className="ml-auto">
                    {(r.score * 100).toFixed(0)}%
                  </Badge>
                </div>
                <p className="text-sm text-[var(--text-mid)] overflow-hidden text-ellipsis line-clamp-2">
                  {r.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && total === 0 && query && (
        <div className="text-center py-16">
          <Search className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
          <p className="text-[var(--text-mid)]">No results found. Try a different query.</p>
        </div>
      )}
    </div>
  );
}
