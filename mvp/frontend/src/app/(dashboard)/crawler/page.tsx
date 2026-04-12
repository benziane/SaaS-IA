'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Globe, Loader2 } from 'lucide-react';

import { Button } from '@/lib/design-hub/components/Button';
import { Badge } from '@/lib/design-hub/components/Badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Input } from '@/lib/design-hub/components/Input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Checkbox } from '@/components/ui/checkbox';

import { useIndexUrl, useScrape, useScrapeWithVision, useBatchScrape, useDeepCrawl, useExtractCss, useSeedUrls, useScrapeHttp, useAdaptiveCrawl, useScrapePdf, useExtractCosine, useHubCrawl } from '@/features/crawler/hooks/useCrawler';
import { extractXpath, extractRegex } from '@/features/crawler/api';
import type { ImageData, ExtractResponse } from '@/features/crawler/types';
import { AdvancedTab } from './AdvancedTab';

function ImageCard({ image }: { image: ImageData }) {
  return (
    <div className="surface-card h-full overflow-hidden">
      <img
        src={image.src}
        alt={image.alt}
        className="w-full h-40 object-cover"
        onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
      <div className="p-3">
        {image.alt && (
          <p className="text-xs text-[var(--text-mid)] truncate">
            {image.alt}
          </p>
        )}
        {image.description && (
          <p className="text-sm text-[var(--text-high)] mt-1 text-[0.8rem]">
            {image.description}
          </p>
        )}
      </div>
    </div>
  );
}

export default function CrawlerPage() {
  const [url, setUrl] = useState('');
  const [tab, setTab] = useState('scrape');
  const [crawlSubpages, setCrawlSubpages] = useState(false);
  const [batchUrls, setBatchUrls] = useState('');
  const [maxDepth, setMaxDepth] = useState(3);
  const [maxPages, setMaxPages] = useState(20);
  const [strategy, setStrategy] = useState<'bfs' | 'dfs' | 'bestfirst'>('bestfirst');

  const [extractMode, setExtractMode] = useState<'css' | 'xpath' | 'regex'>('css');
  const [selector, setSelector] = useState('');
  const [seedDomain, setSeedDomain] = useState('');
  const [seedSource, setSeedSource] = useState<'sitemap' | 'crawl'>('sitemap');

  // v6-v8 state
  const [adaptiveQuery, setAdaptiveQuery] = useState('');
  const [adaptiveStrategy, setAdaptiveStrategy] = useState<'statistical' | 'embedding'>('statistical');
  const [adaptiveConfidence, setAdaptiveConfidence] = useState(0.7);
  const [hubProfile, setHubProfile] = useState('wikipedia');
  const [cosineFilter, setCosineFilter] = useState('');
  const [cosineTopK, setCosineTopK] = useState(3);

  const scrape = useScrape();
  const scrapeVision = useScrapeWithVision();
  const indexMutation = useIndexUrl();
  const batchMutation = useBatchScrape();
  const deepCrawlMutation = useDeepCrawl();
  const extractMutation = useExtractCss();
  const extractXpathMutation = useMutation<ExtractResponse, Error, { url: string; xpath: string }>({
    mutationFn: ({ url, xpath }) => extractXpath(url, xpath),
  });
  const extractRegexMutation = useMutation<ExtractResponse, Error, { url: string; pattern: string }>({
    mutationFn: ({ url, pattern }) => extractRegex(url, pattern),
  });
  const seedMutation = useSeedUrls();
  const httpScrapeMutation = useScrapeHttp();
  const adaptiveMutation = useAdaptiveCrawl();
  const pdfScrapeMutation = useScrapePdf();
  const cosineMutation = useExtractCosine();
  const hubMutation = useHubCrawl();

  const handleScrape = () => {
    if (!url.trim()) return;
    scrape.mutate({ url: url.trim() });
  };

  const handleScrapeVision = () => {
    if (!url.trim()) return;
    scrapeVision.mutate({ url: url.trim() });
  };

  const handleIndex = () => {
    if (!url.trim()) return;
    indexMutation.mutate({ url: url.trim(), crawlSubpages });
  };

  const isLoading = scrape.isPending || scrapeVision.isPending || indexMutation.isPending || batchMutation.isPending || deepCrawlMutation.isPending || extractMutation.isPending || extractXpathMutation.isPending || extractRegexMutation.isPending || seedMutation.isPending || httpScrapeMutation.isPending || adaptiveMutation.isPending || pdfScrapeMutation.isPending || cosineMutation.isPending || hubMutation.isPending;
  const scrapeData = scrape.data;
  const visionData = scrapeVision.data;
  const indexData = indexMutation.data;
  const batchData = batchMutation.data;
  const deepCrawlData = deepCrawlMutation.data;
  const httpScrapeData = httpScrapeMutation.data;
  const adaptiveData = adaptiveMutation.data;
  const pdfScrapeData = pdfScrapeMutation.data;
  const cosineData = cosineMutation.data;
  const hubData = hubMutation.data;

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Globe className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Web Crawler</h1>
          <p className="text-xs text-[var(--text-mid)]">Scrape, analyze with vision AI, and index web pages to your knowledge base</p>
        </div>
      </div>

      <div className="surface-card p-5">
        <div className="mb-4">
          <label className="text-sm font-medium text-[var(--text-mid)] mb-1.5 block">
            URL to crawl
          </label>
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
          />
        </div>

        <Tabs value={tab} onValueChange={setTab} className="mb-4">
          <TabsList>
            <TabsTrigger value="scrape">Scrape</TabsTrigger>
            <TabsTrigger value="vision">Scrape + Vision AI</TabsTrigger>
            <TabsTrigger value="index">Index to Knowledge Base</TabsTrigger>
            <TabsTrigger value="batch">Batch Crawl</TabsTrigger>
            <TabsTrigger value="deep">Deep Crawl</TabsTrigger>
            <TabsTrigger value="extract">Extract</TabsTrigger>
            <TabsTrigger value="seed">Seed URLs</TabsTrigger>
            <TabsTrigger value="http-scrape">HTTP Scrape</TabsTrigger>
            <TabsTrigger value="adaptive">Adaptive Crawl</TabsTrigger>
            <TabsTrigger value="pdf-scrape">PDF Scrape</TabsTrigger>
            <TabsTrigger value="cosine">Cosine Extract</TabsTrigger>
            <TabsTrigger value="hub">Hub Crawl</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>

          <TabsContent value="scrape">
            <Button onClick={handleScrape} disabled={!url.trim() || isLoading}>
              {scrape.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Scraping...
                </>
              ) : (
                'Scrape URL'
              )}
            </Button>
          </TabsContent>

          <TabsContent value="vision">
            <Button variant="secondary" onClick={handleScrapeVision} disabled={!url.trim() || isLoading}>
              {scrapeVision.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Scrape + Analyze Images'
              )}
            </Button>
          </TabsContent>

          <TabsContent value="index">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="crawl-subpages"
                  checked={crawlSubpages}
                  onCheckedChange={(checked) => setCrawlSubpages(checked === true)}
                />
                <label htmlFor="crawl-subpages" className="text-sm text-[var(--text-high)] cursor-pointer">
                  Crawl subpages (up to 5)
                </label>
              </div>
              <Button
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={handleIndex}
                disabled={!url.trim() || isLoading}
              >
                {indexMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Indexing...
                  </>
                ) : (
                  'Index to Knowledge Base'
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="batch">
            <div className="surface-card rounded-xl p-5 space-y-4">
              <label className="text-sm font-medium text-[var(--text-secondary)]">URLs (one per line)</label>
              <textarea
                className="w-full h-32 rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-3 text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
                placeholder={"https://example.com\nhttps://another.com\nhttps://third.com"}
                value={batchUrls}
                onChange={(e) => setBatchUrls(e.target.value)}
              />
              <Button
                disabled={!batchUrls.trim() || batchMutation.isPending}
                onClick={() => {
                  const urls = batchUrls.split('\n').map(u => u.trim()).filter(u => u.startsWith('http'));
                  batchMutation.mutate({ urls });
                }}
              >
                {batchMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Crawling...
                  </>
                ) : (
                  `Crawl ${batchUrls.split('\n').filter(u => u.trim().startsWith('http')).length} URLs`
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="deep">
            <div className="surface-card rounded-xl p-5 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Strategy</label>
                  <select
                    className="mt-1 w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-2.5 text-sm focus:ring-2 focus:ring-[var(--accent)]"
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value as 'bfs' | 'dfs' | 'bestfirst')}
                  >
                    <option value="bestfirst">BestFirst (smart)</option>
                    <option value="bfs">BFS (breadth-first)</option>
                    <option value="dfs">DFS (depth-first)</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Max Depth: {maxDepth}</label>
                  <input type="range" min={1} max={5} value={maxDepth} onChange={(e) => setMaxDepth(+e.target.value)} className="mt-2 w-full accent-[var(--accent)]" />
                </div>
                <div>
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Max Pages: {maxPages}</label>
                  <input type="range" min={1} max={50} value={maxPages} onChange={(e) => setMaxPages(+e.target.value)} className="mt-2 w-full accent-[var(--accent)]" />
                </div>
              </div>
              <Button
                disabled={!url.trim() || deepCrawlMutation.isPending}
                onClick={() => deepCrawlMutation.mutate({ start_url: url, max_depth: maxDepth, max_pages: maxPages, strategy })}
              >
                {deepCrawlMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Crawling...
                  </>
                ) : (
                  'Start Deep Crawl'
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="extract" className="space-y-4">
            <div className="surface-card rounded-xl p-5 space-y-4">
              <div className="flex gap-2">
                {(['css', 'xpath', 'regex'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setExtractMode(mode)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                      extractMode === mode
                        ? 'bg-[var(--accent)] text-white'
                        : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    {mode === 'css' ? 'CSS Selector' : mode === 'xpath' ? 'XPath' : 'Regex'}
                  </button>
                ))}
              </div>
              <input
                type="text"
                className="w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
                placeholder={
                  extractMode === 'css' ? 'h1, .title, #main-content'
                    : extractMode === 'xpath' ? '//h1 | //div[@class="content"]'
                    : '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
                }
                value={selector}
                onChange={(e) => setSelector(e.target.value)}
              />
              <Button
                disabled={!url.trim() || !selector.trim() || extractMutation.isPending || extractXpathMutation.isPending || extractRegexMutation.isPending}
                onClick={() => {
                  if (extractMode === 'css') extractMutation.mutate({ url, selector });
                  else if (extractMode === 'xpath') extractXpathMutation.mutate({ url, xpath: selector });
                  else extractRegexMutation.mutate({ url, pattern: selector });
                }}
              >
                {(extractMutation.isPending || extractXpathMutation.isPending || extractRegexMutation.isPending)
                  ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Extracting...
                    </>
                  )
                  : 'Extract'}
              </Button>
            </div>

            {/* Extract Results */}
            {(() => {
              const data = extractMode === 'css' ? extractMutation.data
                : extractMode === 'xpath' ? extractXpathMutation.data
                : extractRegexMutation.data;
              if (!data?.results) return null;
              return (
                <div className="surface-card rounded-xl p-5 space-y-3">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--accent)]/10 text-[var(--accent)]">
                    {data.count} results
                  </span>
                  <div className="space-y-1 max-h-96 overflow-y-auto">
                    {data.results.map((r: string, i: number) => (
                      <pre key={i} className="p-2 rounded-lg bg-[var(--bg-surface)]/50 text-sm font-mono whitespace-pre-wrap break-all">
                        {r}
                      </pre>
                    ))}
                  </div>
                </div>
              );
            })()}
          </TabsContent>

          <TabsContent value="seed" className="space-y-4">
            <div className="surface-card rounded-xl p-5 space-y-4">
              <label className="text-sm font-medium text-[var(--text-secondary)]">Domain</label>
              <input
                type="text"
                className="w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
                placeholder="example.com"
                value={seedDomain}
                onChange={(e) => setSeedDomain(e.target.value)}
              />
              <div className="flex gap-2">
                <button
                  onClick={() => setSeedSource('sitemap')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                    seedSource === 'sitemap'
                      ? 'bg-[var(--accent)] text-white'
                      : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  Sitemap
                </button>
                <button
                  onClick={() => setSeedSource('crawl')}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                    seedSource === 'crawl'
                      ? 'bg-[var(--accent)] text-white'
                      : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  Crawl Discovery
                </button>
              </div>
              <button
                className="px-4 py-2 rounded-lg bg-[var(--accent)] text-white font-medium hover:opacity-90 transition disabled:opacity-50"
                disabled={!seedDomain.trim() || seedMutation.isPending}
                onClick={() => seedMutation.mutate({ domain: seedDomain, source: seedSource })}
              >
                {seedMutation.isPending ? 'Discovering...' : 'Discover URLs'}
              </button>
            </div>

            {seedMutation.data?.urls && (
              <div className="surface-card rounded-xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--accent)]/10 text-[var(--accent)]">
                    {seedMutation.data.total} URLs found via {seedMutation.data.source}
                  </span>
                </div>
                <div className="space-y-1 max-h-96 overflow-y-auto">
                  {seedMutation.data.urls.map((url: string, i: number) => (
                    <a
                      key={i}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-2 rounded-lg bg-[var(--bg-surface)]/50 text-sm text-[var(--accent)] hover:underline truncate"
                    >
                      {url}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="http-scrape">
            <div className="space-y-3">
              <p className="text-sm text-[var(--text-mid)]">
                Fast HTTP-only scrape — no browser, no JavaScript. 10-20x faster for static pages.
              </p>
              <Button
                onClick={() => httpScrapeMutation.mutate({ url: url.trim() })}
                disabled={!url.trim() || isLoading}
              >
                {httpScrapeMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Scraping...
                  </>
                ) : (
                  'HTTP Scrape'
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="adaptive" className="space-y-4">
            <div className="surface-card rounded-xl p-5 space-y-4">
              <p className="text-sm text-[var(--text-mid)]">
                Self-tuning crawl that learns relevance and stops when confident.
              </p>
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)]">Query</label>
                <input
                  type="text"
                  className="mt-1 w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
                  placeholder="Topic to search for..."
                  value={adaptiveQuery}
                  onChange={(e) => setAdaptiveQuery(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Strategy</label>
                  <select
                    className="mt-1 w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-2.5 text-sm focus:ring-2 focus:ring-[var(--accent)]"
                    value={adaptiveStrategy}
                    onChange={(e) => setAdaptiveStrategy(e.target.value as 'statistical' | 'embedding')}
                  >
                    <option value="statistical">Statistical (BM25/TF-IDF)</option>
                    <option value="embedding">Embedding (semantic)</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Confidence: {adaptiveConfidence}</label>
                  <input type="range" min={0.1} max={1.0} step={0.05} value={adaptiveConfidence} onChange={(e) => setAdaptiveConfidence(+e.target.value)} className="mt-2 w-full accent-[var(--accent)]" />
                </div>
              </div>
              <Button
                disabled={!url.trim() || !adaptiveQuery.trim() || adaptiveMutation.isPending}
                onClick={() => adaptiveMutation.mutate({ url: url.trim(), query: adaptiveQuery, strategy: adaptiveStrategy, confidence_threshold: adaptiveConfidence })}
              >
                {adaptiveMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Crawling...
                  </>
                ) : (
                  'Start Adaptive Crawl'
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="pdf-scrape">
            <div className="space-y-3">
              <p className="text-sm text-[var(--text-mid)]">
                Extract content from a PDF URL using crawl4ai's PDF strategy.
              </p>
              <Button
                onClick={() => pdfScrapeMutation.mutate({ url: url.trim() })}
                disabled={!url.trim() || isLoading}
              >
                {pdfScrapeMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Extracting...
                  </>
                ) : (
                  'Scrape PDF'
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="cosine" className="space-y-4">
            <div className="surface-card rounded-xl p-5 space-y-4">
              <p className="text-sm text-[var(--text-mid)]">
                Semantic clustering via CosineStrategy — groups related content blocks.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Semantic Filter (optional)</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
                    placeholder="Filter query..."
                    value={cosineFilter}
                    onChange={(e) => setCosineFilter(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-[var(--text-secondary)]">Top K Clusters: {cosineTopK}</label>
                  <input type="range" min={1} max={20} value={cosineTopK} onChange={(e) => setCosineTopK(+e.target.value)} className="mt-2 w-full accent-[var(--accent)]" />
                </div>
              </div>
              <Button
                disabled={!url.trim() || cosineMutation.isPending}
                onClick={() => cosineMutation.mutate({ url: url.trim(), top_k: cosineTopK, semantic_filter: cosineFilter || undefined })}
              >
                {cosineMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Clustering...
                  </>
                ) : (
                  'Extract Clusters'
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="hub" className="space-y-4">
            <div className="surface-card rounded-xl p-5 space-y-4">
              <p className="text-sm text-[var(--text-mid)]">
                Use pre-built site profiles for known sites (Wikipedia, Reddit, GitHub, arXiv, etc.).
              </p>
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)]">Site Profile</label>
                <select
                  className="mt-1 w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-2.5 text-sm focus:ring-2 focus:ring-[var(--accent)]"
                  value={hubProfile}
                  onChange={(e) => setHubProfile(e.target.value)}
                >
                  <option value="wikipedia">Wikipedia</option>
                  <option value="reddit">Reddit</option>
                  <option value="github">GitHub</option>
                  <option value="arxiv">arXiv</option>
                  <option value="stackoverflow">StackOverflow</option>
                  <option value="medium">Medium</option>
                </select>
              </div>
              <Button
                disabled={!url.trim() || hubMutation.isPending}
                onClick={() => hubMutation.mutate({ url: url.trim(), site_profile: hubProfile })}
              >
                {hubMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Crawling...
                  </>
                ) : (
                  `Crawl with ${hubProfile} profile`
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="advanced">
            <AdvancedTab />
          </TabsContent>
        </Tabs>

        {(scrape.isError || scrapeVision.isError || indexMutation.isError || batchMutation.isError || deepCrawlMutation.isError || extractMutation.isError || extractXpathMutation.isError || extractRegexMutation.isError || seedMutation.isError || httpScrapeMutation.isError || adaptiveMutation.isError || pdfScrapeMutation.isError || cosineMutation.isError || hubMutation.isError) && (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>
              {(scrape.error ?? scrapeVision.error ?? indexMutation.error ?? batchMutation.error ?? deepCrawlMutation.error ?? extractMutation.error ?? extractXpathMutation.error ?? extractRegexMutation.error ?? seedMutation.error ?? httpScrapeMutation.error ?? adaptiveMutation.error ?? pdfScrapeMutation.error ?? cosineMutation.error ?? hubMutation.error)?.message}
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* Scrape Results */}
      {scrapeData?.success && (
        <div className="space-y-5">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">{scrapeData.title || 'Scraped Content'}</h2>
            <div className="flex gap-2 mb-4">
              <Badge variant="secondary">{String(scrapeData.text_length)} chars</Badge>
              <Badge>{String(scrapeData.image_count)} images</Badge>
            </div>
            <div className="max-h-[400px] overflow-auto bg-[var(--bg-elevated)] p-4 rounded-md">
              <pre className="text-sm text-[var(--text-high)] whitespace-pre-wrap font-mono text-[0.85rem]">
                {scrapeData.markdown.substring(0, 5000)}
                {scrapeData.markdown.length > 5000 ? '\n\n... (truncated)' : ''}
              </pre>
            </div>
          </div>

          {scrapeData.images.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Images Found</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {scrapeData.images.map((img, i) => (
                  <ImageCard key={i} image={img} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Vision Results */}
      {visionData?.success && (
        <div className="space-y-5">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">{visionData.title || 'Vision Analysis'}</h2>
            <Badge variant="secondary" className="mb-4">Provider: {visionData.vision_provider}</Badge>
            <div className="max-h-[300px] overflow-auto bg-[var(--bg-elevated)] p-4 rounded-md">
              <pre className="text-sm text-[var(--text-high)] whitespace-pre-wrap font-mono text-[0.85rem]">
                {visionData.markdown.substring(0, 3000)}
              </pre>
            </div>
          </div>

          {visionData.images.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Images with AI Descriptions</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {visionData.images.map((img, i) => (
                  <ImageCard key={i} image={img} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Index Results */}
      {indexData?.success && (
        <Alert variant="success" className="mt-4">
          <AlertDescription>
            Indexed successfully: {String(indexData.pages_crawled)} page(s) crawled,{' '}
            {String(indexData.chunks_indexed)} chunks indexed,{' '}
            {String(indexData.images_found)} images found.
          </AlertDescription>
        </Alert>
      )}

      {/* Batch Crawl Results */}
      {batchData?.success && (
        <div className="surface-card rounded-xl p-5 space-y-3">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">Batch Crawl Results</h2>
          <div className="flex gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400">
              {batchData.successes} succeeded
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400">
              {batchData.total - batchData.successes} failed
            </span>
          </div>
          <div className="space-y-2">
            {batchData.results.map((r, i) => (
              <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-surface)]/50 text-sm">
                <span className={r.success ? 'text-green-400' : 'text-red-400'}>{r.success ? '\u2713' : '\u2717'}</span>
                <span className="truncate flex-1">{r.title || r.url}</span>
                <span className="text-[var(--text-muted)] text-xs">{r.text_length?.toLocaleString()} chars</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Deep Crawl Results */}
      {deepCrawlData?.success && deepCrawlData.results && (
        <div className="surface-card rounded-xl p-5 space-y-3">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">Deep Crawl Results</h2>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--accent)]/10 text-[var(--accent)]">
            {deepCrawlData.results.length} pages found
          </span>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {deepCrawlData.results.map((r, i) => (
              <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-surface)]/50 text-sm">
                <span className={r.success ? 'text-green-400' : 'text-red-400'}>{r.success ? '\u2713' : '\u2717'}</span>
                <span className="truncate flex-1">{r.title || r.url}</span>
                <span className="text-[var(--text-muted)] text-xs">{r.text_length?.toLocaleString()} chars</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* HTTP Scrape Results */}
      {httpScrapeData?.success && (
        <div className="surface-card p-5">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">{httpScrapeData.title || 'HTTP Scrape Result'}</h2>
          <div className="flex gap-2 mb-4">
            <Badge variant="secondary">{String(httpScrapeData.text_length)} chars</Badge>
            <Badge>{httpScrapeData.scraper}</Badge>
            {httpScrapeData.status_code && <Badge variant="secondary">HTTP {String(httpScrapeData.status_code)}</Badge>}
          </div>
          <div className="max-h-[400px] overflow-auto bg-[var(--bg-elevated)] p-4 rounded-md">
            <pre className="text-sm text-[var(--text-high)] whitespace-pre-wrap font-mono text-[0.85rem]">
              {httpScrapeData.markdown.substring(0, 5000)}
              {httpScrapeData.markdown.length > 5000 ? '\n\n... (truncated)' : ''}
            </pre>
          </div>
        </div>
      )}

      {/* Adaptive Crawl Results */}
      {adaptiveData?.success && adaptiveData.pages && (
        <div className="surface-card rounded-xl p-5 space-y-3">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">Adaptive Crawl Results</h2>
          <div className="flex gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--accent)]/10 text-[var(--accent)]">
              {adaptiveData.total_pages} pages
            </span>
            {adaptiveData.confidence != null && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400">
                Confidence: {(adaptiveData.confidence * 100).toFixed(0)}%
              </span>
            )}
            {adaptiveData.is_sufficient && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400">
                Sufficient
              </span>
            )}
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {adaptiveData.pages.map((r, i) => (
              <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-surface)]/50 text-sm">
                <span className={r.success ? 'text-green-400' : 'text-red-400'}>{r.success ? '\u2713' : '\u2717'}</span>
                <span className="truncate flex-1">{r.title || r.url}</span>
                {r.score != null && <span className="text-[var(--text-muted)] text-xs">score: {r.score.toFixed(2)}</span>}
                <span className="text-[var(--text-muted)] text-xs">d{r.depth}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PDF Scrape Results */}
      {pdfScrapeData?.success && (
        <div className="surface-card p-5">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">PDF Content</h2>
          <Badge variant="secondary" className="mb-4">{String(pdfScrapeData.text_length)} chars</Badge>
          <div className="max-h-[400px] overflow-auto bg-[var(--bg-elevated)] p-4 rounded-md">
            <pre className="text-sm text-[var(--text-high)] whitespace-pre-wrap font-mono text-[0.85rem]">
              {pdfScrapeData.markdown.substring(0, 5000)}
              {pdfScrapeData.markdown.length > 5000 ? '\n\n... (truncated)' : ''}
            </pre>
          </div>
        </div>
      )}

      {/* Cosine Extract Results */}
      {cosineData?.success && cosineData.clusters && (
        <div className="surface-card rounded-xl p-5 space-y-3">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">Semantic Clusters</h2>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--accent)]/10 text-[var(--accent)]">
            {cosineData.total_clusters} clusters
          </span>
          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {cosineData.clusters.map((cluster, i) => (
              <div key={i} className="p-3 rounded-lg bg-[var(--bg-surface)]/50 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-[var(--text-high)]">Cluster {cluster.index}</span>
                  {cluster.tags.map((tag, j) => (
                    <span key={j} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-[var(--accent)]/10 text-[var(--accent)]">
                      {tag}
                    </span>
                  ))}
                </div>
                <pre className="text-sm text-[var(--text-mid)] whitespace-pre-wrap font-mono text-[0.8rem]">
                  {cluster.content.substring(0, 500)}
                  {cluster.content.length > 500 ? '...' : ''}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hub Crawl Results */}
      {hubData?.success && (
        <div className="surface-card p-5">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">Hub Crawl Result</h2>
          <Badge variant="secondary" className="mb-4">Profile: {hubData.site_profile}</Badge>
          <div className="max-h-[400px] overflow-auto bg-[var(--bg-elevated)] p-4 rounded-md">
            <pre className="text-sm text-[var(--text-high)] whitespace-pre-wrap font-mono text-[0.85rem]">
              {JSON.stringify(hubData.data, null, 2)?.substring(0, 5000)}
            </pre>
          </div>
        </div>
      )}

      {(scrapeData && !scrapeData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{scrapeData.error}</AlertDescription>
        </Alert>
      )}
      {(visionData && !visionData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{visionData.error}</AlertDescription>
        </Alert>
      )}
      {(indexData && !indexData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{indexData.error}</AlertDescription>
        </Alert>
      )}
      {(batchData && !batchData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{batchData.error}</AlertDescription>
        </Alert>
      )}
      {(deepCrawlData && !deepCrawlData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{deepCrawlData.error}</AlertDescription>
        </Alert>
      )}
      {(httpScrapeData && !httpScrapeData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{httpScrapeData.error}</AlertDescription>
        </Alert>
      )}
      {(adaptiveData && !adaptiveData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{adaptiveData.error}</AlertDescription>
        </Alert>
      )}
      {(pdfScrapeData && !pdfScrapeData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{pdfScrapeData.error}</AlertDescription>
        </Alert>
      )}
      {(cosineData && !cosineData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{cosineData.error}</AlertDescription>
        </Alert>
      )}
      {(hubData && !hubData.success) && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{hubData.error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
