'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { useMutation } from '@tanstack/react-query';

import { autoChapter, getMetadata, smartTranscribe, transcribePlaylist, checkStreamStatus, captureStream, analyzeVideo } from '@/features/transcription/api';
import type { AutoChapterResponse, LiveStreamCapture, LiveStreamStatus, PlaylistTranscribeResponse, SmartTranscribeResponse, VideoAnalyzeResponse, YouTubeMetadata } from '@/features/transcription/types';

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatNumber(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}

function ProviderBadge({ provider }: { provider: string }) {
  const variants: Record<string, 'success' | 'default' | 'warning'> = {
    youtube_subtitles: 'success',
    whisper: 'default',
    assemblyai: 'warning',
  };
  const labels: Record<string, string> = {
    youtube_subtitles: 'YouTube Subs (Free)',
    whisper: 'Whisper (Local)',
    assemblyai: 'AssemblyAI (Paid)',
  };
  return <Badge variant={variants[provider] || 'outline'}>{labels[provider] || provider}</Badge>;
}

function MetadataCard({ data }: { data: YouTubeMetadata }) {
  return (
    <Card>
      <div className="grid grid-cols-1 md:grid-cols-[1fr_2fr]">
        {data.thumbnail && (
          <div className="relative min-h-[200px]">
            <img
              src={data.thumbnail}
              alt={data.title}
              className="w-full h-full object-cover rounded-l-[var(--radius-lg,8px)]"
            />
          </div>
        )}
        <CardContent className="p-6">
          <h3 className="text-lg font-bold text-[var(--text-high)] mb-2">{data.title}</h3>
          <div className="flex gap-1.5 flex-wrap mb-4">
            <Badge variant="outline">{data.uploader}</Badge>
            <Badge variant="secondary">{formatDuration(data.duration_seconds)}</Badge>
            <Badge variant="secondary">{formatNumber(data.view_count)} views</Badge>
            <Badge variant="secondary">{formatNumber(data.like_count)} likes</Badge>
            {data.is_live && <Badge variant="destructive">LIVE</Badge>}
          </div>
          {data.description && (
            <p className="text-sm text-[var(--text-mid)] mb-4 max-h-[100px] overflow-auto whitespace-pre-wrap">
              {data.description.substring(0, 500)}{data.description.length > 500 ? '...' : ''}
            </p>
          )}
          {data.tags.length > 0 && (
            <div className="flex gap-1 flex-wrap mb-2">
              {data.tags.slice(0, 10).map((tag) => (
                <Badge key={tag} variant="outline" className="text-[0.7rem]">{tag}</Badge>
              ))}
            </div>
          )}
          {data.chapters.length > 0 && (
            <div className="mt-2">
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-1">{data.chapters.length} Chapters</h4>
              {data.chapters.slice(0, 5).map((ch, i) => (
                <span key={i} className="block text-xs text-[var(--text-mid)]">
                  {formatDuration(Math.round(ch.start_time))} - {ch.title}
                </span>
              ))}
              {data.chapters.length > 5 && (
                <span className="text-xs text-[var(--text-mid)]">+{data.chapters.length - 5} more</span>
              )}
            </div>
          )}
        </CardContent>
      </div>
    </Card>
  );
}

export default function YouTubePage() {
  const [url, setUrl] = useState('');
  const [tab, setTab] = useState('smart');
  const [language, setLanguage] = useState('auto');

  const smartMutation = useMutation<SmartTranscribeResponse, Error, void>({
    mutationFn: () => smartTranscribe(url, language),
  });
  const metadataMutation = useMutation<YouTubeMetadata, Error, void>({
    mutationFn: () => getMetadata(url),
  });
  const playlistMutation = useMutation<PlaylistTranscribeResponse, Error, void>({
    mutationFn: () => transcribePlaylist(url, language),
  });
  const chapterMutation = useMutation<AutoChapterResponse, Error, void>({
    mutationFn: () => autoChapter(url),
  });
  const streamStatusMutation = useMutation<LiveStreamStatus, Error, void>({
    mutationFn: () => checkStreamStatus(url),
  });
  const captureMutation = useMutation<LiveStreamCapture, Error, void>({
    mutationFn: () => captureStream(url, 300),
  });
  const videoAnalyzeMutation = useMutation<VideoAnalyzeResponse, Error, void>({
    mutationFn: () => analyzeVideo(url),
  });

  const isLoading = smartMutation.isPending || metadataMutation.isPending || playlistMutation.isPending || chapterMutation.isPending || captureMutation.isPending || videoAnalyzeMutation.isPending;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-[var(--text-high)] mb-1">YouTube Studio</h1>
      <p className="text-sm text-[var(--text-mid)] mb-6">
        Smart transcription, metadata extraction, playlist processing, auto-chaptering, live stream capture, and video analysis
      </p>

      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-[2fr_1fr] gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">YouTube URL</label>
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=... or playlist URL"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Language</label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto-detect</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="ar">Arabic</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="mb-4">
              <TabsTrigger value="smart">Smart Transcribe</TabsTrigger>
              <TabsTrigger value="metadata">Metadata</TabsTrigger>
              <TabsTrigger value="playlist">Playlist Bulk</TabsTrigger>
              <TabsTrigger value="chapter">Auto-Chapter</TabsTrigger>
              <TabsTrigger value="stream">Live Stream</TabsTrigger>
              <TabsTrigger value="analysis">Video Analysis</TabsTrigger>
            </TabsList>

            <TabsContent value="smart">
              <p className="text-sm text-[var(--text-mid)] mb-4">
                Automatically uses the best provider: YouTube subtitles (free) &gt; Whisper (local) &gt; AssemblyAI
              </p>
              <Button onClick={() => smartMutation.mutate()} disabled={!url.trim() || isLoading}>
                {smartMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Transcribing...</> : 'Smart Transcribe'}
              </Button>
            </TabsContent>

            <TabsContent value="metadata">
              <Button onClick={() => metadataMutation.mutate()} disabled={!url.trim() || isLoading}>
                {metadataMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Extracting...</> : 'Extract Metadata'}
              </Button>
            </TabsContent>

            <TabsContent value="playlist">
              <p className="text-sm text-[var(--text-mid)] mb-4">
                Transcribe all videos in a playlist or channel (max 100 videos)
              </p>
              <Button variant="secondary" onClick={() => playlistMutation.mutate()} disabled={!url.trim() || isLoading}>
                {playlistMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Processing...</> : 'Transcribe Playlist'}
              </Button>
            </TabsContent>

            <TabsContent value="chapter">
              <p className="text-sm text-[var(--text-mid)] mb-4">
                Combine YouTube chapters with AI summaries for each section
              </p>
              <Button onClick={() => chapterMutation.mutate()} disabled={!url.trim() || isLoading}>
                {chapterMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Analyzing...</> : 'Auto-Chapter'}
              </Button>
            </TabsContent>

            <TabsContent value="stream">
              <p className="text-sm text-[var(--text-mid)] mb-4">
                Capture a segment of a live stream (YouTube Live, Twitch) and auto-transcribe it
              </p>
              <div className="flex gap-4">
                <Button variant="outline" onClick={() => streamStatusMutation.mutate()} disabled={!url.trim() || isLoading}>
                  {streamStatusMutation.isPending ? 'Checking...' : 'Check Status'}
                </Button>
                <Button variant="destructive" onClick={() => captureMutation.mutate()} disabled={!url.trim() || isLoading}>
                  {captureMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Recording 5 min...</> : 'Capture Stream (5 min)'}
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="analysis">
              <p className="text-sm text-[var(--text-mid)] mb-4">
                Download video, extract frames, and analyze each with AI Vision
              </p>
              <Button onClick={() => videoAnalyzeMutation.mutate()} disabled={!url.trim() || isLoading}>
                {videoAnalyzeMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Analyzing...</> : 'Analyze Video Frames'}
              </Button>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Smart Transcribe Result */}
      {smartMutation.data && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex gap-2 mb-4 items-center flex-wrap">
              <h2 className="text-lg font-semibold text-[var(--text-high)]">Transcription Result</h2>
              <ProviderBadge provider={smartMutation.data.provider} />
              {smartMutation.data.is_manual && <Badge variant="outline">Manual subs</Badge>}
              <Badge variant="outline">{formatDuration(smartMutation.data.duration_seconds)}</Badge>
              <Badge variant="outline">{smartMutation.data.language}</Badge>
            </div>
            <div className="bg-[var(--bg-elevated)] p-4 rounded-[var(--radius-md,6px)] max-h-[400px] overflow-auto">
              <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap leading-relaxed">
                {smartMutation.data.text}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metadata Result */}
      {metadataMutation.data && <div className="mb-6"><MetadataCard data={metadataMutation.data} /></div>}

      {/* Playlist Result */}
      {playlistMutation.data?.success && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex gap-4 mb-4 items-center">
              <h2 className="text-lg font-semibold text-[var(--text-high)]">Playlist Results</h2>
              <Badge>{playlistMutation.data.transcribed}/{playlistMutation.data.total} transcribed</Badge>
            </div>
            <div className="divide-y divide-[var(--border)]">
              {playlistMutation.data.results.map((r) => (
                <div key={r.video_id} className="py-3">
                  <div className="flex gap-2 items-center mb-1">
                    <span className="text-sm font-semibold text-[var(--text-high)]">{r.title || r.video_id}</span>
                    <ProviderBadge provider={r.provider} />
                    {r.success ? <Badge variant="success">OK</Badge> : <Badge variant="destructive">Failed</Badge>}
                  </div>
                  <p className="text-xs text-[var(--text-mid)] max-h-[60px] overflow-hidden">
                    {r.success ? r.transcript : r.error}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chapter Result */}
      {chapterMutation.data && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">{chapterMutation.data.title}</h2>
            <ProviderBadge provider={chapterMutation.data.provider} />

            {chapterMutation.data.full_summary && (
              <div className="mt-4 p-4 bg-[var(--accent)]/10 rounded-[var(--radius-md,6px)] border border-[var(--accent)]/20">
                <h3 className="text-sm font-semibold text-[var(--text-high)] mb-2">Overall Summary</h3>
                <p className="text-sm text-[var(--text-high)]">{chapterMutation.data.full_summary}</p>
              </div>
            )}

            <hr className="border-[var(--border)] my-4" />

            {chapterMutation.data.chapters.map((ch, i) => (
              <div key={i} className="mb-4 p-4 border border-[var(--border)] rounded-[var(--radius-md,6px)]">
                <div className="flex gap-2 mb-2 items-center">
                  <Badge variant="outline">{formatDuration(Math.round(ch.start_time))}</Badge>
                  <h4 className="text-sm font-semibold text-[var(--text-high)]">{ch.title}</h4>
                </div>
                {ch.summary && (
                  <p className="text-sm text-[var(--text-mid)]">{ch.summary}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Stream Status */}
      {streamStatusMutation.data && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex gap-2 items-center mb-2">
              <h2 className="text-lg font-semibold text-[var(--text-high)]">Stream Status</h2>
              {streamStatusMutation.data.is_live ? (
                <Badge variant="destructive">LIVE</Badge>
              ) : (
                <Badge variant="secondary">OFFLINE</Badge>
              )}
            </div>
            <p className="text-sm text-[var(--text-high)]">{streamStatusMutation.data.title}</p>
            <span className="text-xs text-[var(--text-mid)]">
              {streamStatusMutation.data.uploader}
              {streamStatusMutation.data.concurrent_viewers != null && ` | ${formatNumber(streamStatusMutation.data.concurrent_viewers)} viewers`}
            </span>
          </CardContent>
        </Card>
      )}

      {/* Stream Capture Result */}
      {captureMutation.data?.success && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex gap-2 items-center mb-4 flex-wrap">
              <h2 className="text-lg font-semibold text-[var(--text-high)]">Stream Captured</h2>
              <Badge>{captureMutation.data.capture_method}</Badge>
              <Badge variant="outline">{formatDuration(captureMutation.data.duration_seconds)}</Badge>
            </div>
            {captureMutation.data.transcript && (
              <div className="bg-[var(--bg-elevated)] p-4 rounded-[var(--radius-md,6px)] max-h-[300px] overflow-auto">
                <h3 className="text-sm font-semibold text-[var(--text-high)] mb-2">Auto-Transcription (Whisper)</h3>
                <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap">
                  {captureMutation.data.transcript}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Video Analysis Result */}
      {videoAnalyzeMutation.data && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex gap-2 items-center mb-4 flex-wrap">
              <h2 className="text-lg font-semibold text-[var(--text-high)]">{videoAnalyzeMutation.data.title || 'Video Analysis'}</h2>
              <Badge variant="outline">{videoAnalyzeMutation.data.frames_analyzed} frames</Badge>
            </div>
            {videoAnalyzeMutation.data.summary && (
              <div className="p-4 bg-[var(--accent)]/10 rounded-[var(--radius-md,6px)] border border-[var(--accent)]/20 mb-4">
                <h3 className="text-sm font-semibold text-[var(--text-high)] mb-2">Video Summary</h3>
                <p className="text-sm text-[var(--text-high)]">{videoAnalyzeMutation.data.summary}</p>
              </div>
            )}
            {videoAnalyzeMutation.data.analyses.map((frame, i) => (
              <div key={i} className="mb-3 p-3 border border-[var(--border)] rounded-[var(--radius-md,6px)]">
                <Badge variant="outline" className="mr-2">{formatDuration(Math.round(frame.timestamp))}</Badge>
                <span className="text-sm text-[var(--text-high)]">{frame.description}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Errors */}
      {smartMutation.isError && <Alert variant="destructive" className="mb-4"><AlertDescription>{smartMutation.error.message}</AlertDescription></Alert>}
      {metadataMutation.isError && <Alert variant="destructive" className="mb-4"><AlertDescription>{metadataMutation.error.message}</AlertDescription></Alert>}
      {playlistMutation.isError && <Alert variant="destructive" className="mb-4"><AlertDescription>{playlistMutation.error.message}</AlertDescription></Alert>}
      {chapterMutation.isError && <Alert variant="destructive" className="mb-4"><AlertDescription>{chapterMutation.error.message}</AlertDescription></Alert>}
      {captureMutation.isError && <Alert variant="destructive" className="mb-4"><AlertDescription>{captureMutation.error.message}</AlertDescription></Alert>}
      {videoAnalyzeMutation.isError && <Alert variant="destructive" className="mb-4"><AlertDescription>{videoAnalyzeMutation.error.message}</AlertDescription></Alert>}
    </div>
  );
}
