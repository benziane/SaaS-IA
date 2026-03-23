'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  Grid,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';

import { useIndexUrl, useScrape, useScrapeWithVision } from '@/features/crawler/hooks/useCrawler';
import type { ImageData } from '@/features/crawler/types';

function ImageCard({ image }: { image: ImageData }) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardMedia
        component="img"
        height="160"
        image={image.src}
        alt={image.alt}
        sx={{ objectFit: 'cover' }}
        onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
      <CardContent sx={{ p: 1.5 }}>
        {image.alt && (
          <Typography variant="caption" color="text.secondary" display="block" noWrap>
            {image.alt}
          </Typography>
        )}
        {image.description && (
          <Typography variant="body2" sx={{ mt: 0.5, fontSize: '0.8rem' }}>
            {image.description}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export default function CrawlerPage() {
  const [url, setUrl] = useState('');
  const [tab, setTab] = useState(0);
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
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>Web Crawler</Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            label="URL to crawl"
            sx={{ mb: 2 }}
          />

          <Tabs value={tab} onChange={(_, v: number) => setTab(v)} sx={{ mb: 2 }}>
            <Tab label="Scrape" />
            <Tab label="Scrape + Vision AI" />
            <Tab label="Index to Knowledge Base" />
          </Tabs>

          {tab === 0 && (
            <Button variant="contained" onClick={handleScrape} disabled={!url.trim() || isLoading}>
              {scrape.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Scraping...</> : 'Scrape URL'}
            </Button>
          )}

          {tab === 1 && (
            <Button variant="contained" color="secondary" onClick={handleScrapeVision} disabled={!url.trim() || isLoading}>
              {scrapeVision.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Analyzing...</> : 'Scrape + Analyze Images'}
            </Button>
          )}

          {tab === 2 && (
            <Box>
              <FormControlLabel
                control={<Checkbox checked={crawlSubpages} onChange={(e) => setCrawlSubpages(e.target.checked)} />}
                label="Crawl subpages (up to 5)"
                sx={{ mb: 1 }}
              />
              <Box>
                <Button variant="contained" color="success" onClick={handleIndex} disabled={!url.trim() || isLoading}>
                  {indexMutation.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Indexing...</> : 'Index to Knowledge Base'}
                </Button>
              </Box>
            </Box>
          )}

          {(scrape.isError || scrapeVision.isError || indexMutation.isError) && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {(scrape.error ?? scrapeVision.error ?? indexMutation.error)?.message}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Scrape Results */}
      {scrapeData?.success && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>{scrapeData.title || 'Scraped Content'}</Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip label={`${String(scrapeData.text_length)} chars`} size="small" />
                <Chip label={`${String(scrapeData.image_count)} images`} size="small" color="primary" />
              </Box>
              <Box sx={{ maxHeight: 400, overflow: 'auto', bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                  {scrapeData.markdown.substring(0, 5000)}
                  {scrapeData.markdown.length > 5000 ? '\n\n... (truncated)' : ''}
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {scrapeData.images.length > 0 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>Images Found</Typography>
              <Grid container spacing={2}>
                {scrapeData.images.map((img, i) => (
                  <Grid item xs={6} sm={4} md={3} key={i}>
                    <ImageCard image={img} />
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
        </Box>
      )}

      {/* Vision Results */}
      {visionData?.success && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>{visionData.title || 'Vision Analysis'}</Typography>
              <Chip label={`Provider: ${visionData.vision_provider}`} size="small" color="secondary" sx={{ mb: 2 }} />
              <Box sx={{ maxHeight: 300, overflow: 'auto', bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                  {visionData.markdown.substring(0, 3000)}
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {visionData.images.length > 0 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>Images with AI Descriptions</Typography>
              <Grid container spacing={2}>
                {visionData.images.map((img, i) => (
                  <Grid item xs={12} sm={6} key={i}>
                    <ImageCard image={img} />
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
        </Box>
      )}

      {/* Index Results */}
      {indexData?.success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          Indexed successfully: {String(indexData.pages_crawled)} page(s) crawled,{' '}
          {String(indexData.chunks_indexed)} chunks indexed,{' '}
          {String(indexData.images_found)} images found.
        </Alert>
      )}

      {(scrapeData && !scrapeData.success) && (
        <Alert severity="error" sx={{ mt: 2 }}>{scrapeData.error}</Alert>
      )}
      {(visionData && !visionData.success) && (
        <Alert severity="error" sx={{ mt: 2 }}>{visionData.error}</Alert>
      )}
      {(indexData && !indexData.success) && (
        <Alert severity="error" sx={{ mt: 2 }}>{indexData.error}</Alert>
      )}
    </Box>
  );
}
