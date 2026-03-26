'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Card, CardContent } from '@/lib/design-hub/components/Card';
import { Button } from '@/lib/design-hub/components/Button';
import { Badge } from '@/lib/design-hub/components/Badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Input } from '@/lib/design-hub/components/Input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Checkbox } from '@/components/ui/checkbox';

import { useIndexUrl, useScrape, useScrapeWithVision } from '@/features/crawler/hooks/useCrawler';
import type { ImageData } from '@/features/crawler/types';

function ImageCard({ image }: { image: ImageData }) {
  return (
    <Card className="h-full overflow-hidden">
      <img
        src={image.src}
        alt={image.alt}
        className="w-full h-40 object-cover"
        onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
      <CardContent className="p-3">
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
      </CardContent>
    </Card>
  );
}

export default function CrawlerPage() {
  const [url, setUrl] = useState('');
  const [tab, setTab] = useState('scrape');
  const [crawlSubpages, setCrawlSubpages] = useState(false);

  const scrape = useScrape();
  const scrapeVision = useScrapeWithVision();
  const indexMutation = useIndexUrl();

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

  const isLoading = scrape.isPending || scrapeVision.isPending || indexMutation.isPending;
  const scrapeData = scrape.data;
  const visionData = scrapeVision.data;
  const indexData = indexMutation.data;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-[var(--text-high)] mb-6">Web Crawler</h1>

      <Card className="mb-6">
        <CardContent className="p-6">
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
          </Tabs>

          {(scrape.isError || scrapeVision.isError || indexMutation.isError) && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>
                {(scrape.error ?? scrapeVision.error ?? indexMutation.error)?.message}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Scrape Results */}
      {scrapeData?.success && (
        <div>
          <Card className="mb-6">
            <CardContent className="p-6">
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
            </CardContent>
          </Card>

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
        <div>
          <Card className="mb-6">
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">{visionData.title || 'Vision Analysis'}</h2>
              <Badge variant="secondary" className="mb-4">Provider: {visionData.vision_provider}</Badge>
              <div className="max-h-[300px] overflow-auto bg-[var(--bg-elevated)] p-4 rounded-md">
                <pre className="text-sm text-[var(--text-high)] whitespace-pre-wrap font-mono text-[0.85rem]">
                  {visionData.markdown.substring(0, 3000)}
                </pre>
              </div>
            </CardContent>
          </Card>

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
    </div>
  );
}
