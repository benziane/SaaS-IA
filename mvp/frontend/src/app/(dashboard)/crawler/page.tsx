'use client';

import { useState } from 'react';
import { Globe, Loader2 } from 'lucide-react';

import { Button } from '@/lib/design-hub/components/Button';
import { Badge } from '@/lib/design-hub/components/Badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Input } from '@/lib/design-hub/components/Input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Checkbox } from '@/components/ui/checkbox';

import { useIndexUrl, useScrape, useScrapeWithVision, useBatchScrape, useDeepCrawl } from '@/features/crawler/hooks/useCrawler';
import type { ImageData, BatchScrapeRequest, DeepCrawlRequest } from '@/features/crawler/types';

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

  const scrape = useScrape();
  const scrapeVision = useScrapeWithVision();
  const indexMutation = useIndexUrl();
  const batchMutation = useBatchScrape();
  const deepCrawlMutation = useDeepCrawl();

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

  const isLoading = scrape.isPending || scrapeVision.isPending || indexMutation.isPending || batchMutation.isPending || deepCrawlMutation.isPending;
  const scrapeData = scrape.data;
  const visionData = scrapeVision.data;
  const indexData = indexMutation.data;
  const batchData = batchMutation.data;
  const deepCrawlData = deepCrawlMutation.data;

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <Globe className="h-5 w-5 text-white" />
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
        </Tabs>

        {(scrape.isError || scrapeVision.isError || indexMutation.isError || batchMutation.isError || deepCrawlMutation.isError) && (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>
              {(scrape.error ?? scrapeVision.error ?? indexMutation.error ?? batchMutation.error ?? deepCrawlMutation.error)?.message}
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
    </div>
  );
}
