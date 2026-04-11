'use client';

import { useCallback, useRef, useState } from 'react';
import {
  Music, Upload, Scissors, Trash2, FileText, Download, AudioWaveform,
  List, Mic, Podcast, Gauge, Volume2, Loader2, Music2,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import {
  useAudioList,
  useCreateEpisode,
  useDeleteAudio,
  useEditAudio,
  useEpisodeList,
  useGenerateChapters,
  useGenerateShowNotes,
  useSplitAudio,
  useTranscribeAudio,
  useUploadAudio,
} from '@/features/audio-studio/hooks/useAudioStudio';
import { getExportUrl } from '@/features/audio-studio/api';
import type { AudioFile, Chapter, AudioEditOperation } from '@/features/audio-studio/types';

const STATUS_VARIANTS: Record<string, 'default' | 'success' | 'destructive' | 'secondary' | 'warning'> = {
  uploading: 'secondary',
  ready: 'success',
  processing: 'warning',
  failed: 'destructive',
};

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function formatSize(kb: number): string {
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
  return `${kb} KB`;
}

/* ========================================================================
   Mini Waveform Component
   ======================================================================== */

function MiniWaveform({ data }: { data: number[] | null }) {
  if (!data || data.length === 0) return null;
  const step = Math.max(1, Math.floor(data.length / 80));
  const bars: number[] = [];
  for (let i = 0; i < data.length; i += step) {
    bars.push(data[i] ?? 0);
  }
  return (
    <div className="flex items-center gap-px h-8">
      {bars.slice(0, 80).map((v, i) => (
        <div
          key={i}
          className="w-0.5 rounded bg-[var(--accent)] opacity-70"
          style={{ height: `${Math.max(4, (v ?? 0) * 32)}px` }}
        />
      ))}
    </div>
  );
}

/* ========================================================================
   Main Page
   ======================================================================== */

export default function AudioStudioPage() {
  const { data: audioFiles, isLoading } = useAudioList();
  const { data: episodes } = useEpisodeList();
  const uploadMutation = useUploadAudio();
  const deleteMutation = useDeleteAudio();
  const transcribeMutation = useTranscribeAudio();
  const chaptersMutation = useGenerateChapters();
  const showNotesMutation = useGenerateShowNotes();
  const editMutation = useEditAudio();
  const splitMutation = useSplitAudio();
  const createEpisodeMutation = useCreateEpisode();

  const [tab, setTab] = useState('files');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [selected, setSelected] = useState<AudioFile | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [episodeDialogOpen, setEpisodeDialogOpen] = useState(false);
  const [episodeTitle, setEpisodeTitle] = useState('');
  const [episodeDescription, setEpisodeDescription] = useState('');
  const [exportFormat, setExportFormat] = useState('mp3');

  // Edit state
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [fadeDuration, setFadeDuration] = useState(2);
  const [speedFactor, setSpeedFactor] = useState(1.0);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadProgress(0);
    uploadMutation.mutate(
      { file, onProgress: setUploadProgress },
      { onSettled: () => setUploadProgress(null) },
    );
    e.target.value = '';
  }, [uploadMutation]);

  const handleEdit = (opType: AudioEditOperation['type'], params: Record<string, unknown> = {}) => {
    if (!selected) return;
    editMutation.mutate({ id: selected.id, data: { operations: [{ type: opType, params }] } });
    setEditDialogOpen(false);
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Music2 className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Audio Studio</h1>
          <p className="text-xs text-[var(--text-mid)]">Audio editing and noise reduction</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="files" className="flex items-center gap-1.5">
            <AudioWaveform className="h-4 w-4" /> Audio Files
          </TabsTrigger>
          <TabsTrigger value="episodes" className="flex items-center gap-1.5">
            <Podcast className="h-4 w-4" /> Podcast Episodes
          </TabsTrigger>
        </TabsList>

        {/* ============================================================
            TAB 0: Audio Files
            ============================================================ */}
        <TabsContent value="files">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5 mt-5">
            {/* Upload + Actions Panel */}
            <div className="md:col-span-4 space-y-5">
              <div className="surface-card p-5">
                <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Upload Audio</h3>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".mp3,.wav,.ogg,.flac,.m4a,.aac,.webm,.mp4,.wma"
                  hidden
                  onChange={handleUpload}
                />
                <Button
                  className="w-full mb-4"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadMutation.isPending}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  {uploadMutation.isPending ? 'Uploading...' : 'Choose Audio File'}
                </Button>
                {uploadProgress !== null && (
                  <Progress value={uploadProgress} className="mb-4" />
                )}

                {uploadMutation.isError && (
                  <Alert variant="destructive" className="mb-4">
                    <AlertDescription>Upload failed: {uploadMutation.error.message}</AlertDescription>
                  </Alert>
                )}

                <Separator className="my-4" />

                {/* Quick actions on selected file */}
                {selected && (
                  <>
                    <p className="text-sm font-medium text-[var(--text-high)] mb-2">
                      Selected: {selected.filename}
                    </p>

                    <div className="flex flex-wrap gap-2 mb-4">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => transcribeMutation.mutate(selected.id)}
                        disabled={transcribeMutation.isPending}
                      >
                        <Mic className="h-3.5 w-3.5 mr-1" /> Transcribe
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => chaptersMutation.mutate(selected.id)}
                        disabled={chaptersMutation.isPending}
                      >
                        <List className="h-3.5 w-3.5 mr-1" /> Chapters
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => showNotesMutation.mutate(selected.id)}
                        disabled={showNotesMutation.isPending}
                      >
                        <FileText className="h-3.5 w-3.5 mr-1" /> Show Notes
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => splitMutation.mutate({ id: selected.id })}
                        disabled={splitMutation.isPending}
                      >
                        <Scissors className="h-3.5 w-3.5 mr-1" /> Split
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditDialogOpen(true)}
                      >
                        <Gauge className="h-3.5 w-3.5 mr-1" /> Edit
                      </Button>
                    </div>

                    {/* Export */}
                    <div className="flex gap-2 items-center">
                      <Select value={exportFormat} onValueChange={setExportFormat}>
                        <SelectTrigger className="w-24">
                          <SelectValue placeholder="Format" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="mp3">MP3</SelectItem>
                          <SelectItem value="wav">WAV</SelectItem>
                          <SelectItem value="ogg">OGG</SelectItem>
                          <SelectItem value="flac">FLAC</SelectItem>
                        </SelectContent>
                      </Select>
                      <a href={getExportUrl(selected.id, exportFormat)} target="_blank" rel="noopener noreferrer">
                        <Button size="sm">
                          <Download className="h-3.5 w-3.5 mr-1" /> Export
                        </Button>
                      </a>
                    </div>

                    <Separator className="my-4" />

                    {/* Create Episode */}
                    <Button
                      className="w-full"
                      variant="secondary"
                      onClick={() => {
                        setEpisodeTitle('');
                        setEpisodeDescription('');
                        setEpisodeDialogOpen(true);
                      }}
                    >
                      <Podcast className="h-4 w-4 mr-2" /> Create Episode
                    </Button>
                  </>
                )}
              </div>

              {/* Show notes result */}
              {showNotesMutation.data && (
                <div className="surface-card p-5">
                  <h3 className="text-lg font-semibold text-[var(--text-high)] mb-2">Show Notes</h3>
                  <p className="text-sm text-[var(--text-mid)] mb-2">
                    {showNotesMutation.data.show_notes.summary}
                  </p>
                  {showNotesMutation.data.show_notes.key_points.length > 0 && (
                    <>
                      <p className="text-sm font-medium text-[var(--text-high)]">Key Points:</p>
                      <ul className="list-disc list-inside">
                        {showNotesMutation.data.show_notes.key_points.map((p, i) => (
                          <li key={i} className="text-sm text-[var(--text-mid)]">{p}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}

              {/* Split result */}
              {splitMutation.data && (
                <div className="surface-card p-5">
                  <h3 className="text-lg font-semibold text-[var(--text-high)] mb-2">
                    Split Result ({splitMutation.data.count} segments)
                  </h3>
                  {splitMutation.data.segments.map((seg) => (
                    <p key={seg.index} className="text-sm text-[var(--text-mid)]">
                      Segment {seg.index + 1}: {formatDuration(seg.start_seconds)} - {formatDuration(seg.end_seconds)} ({formatDuration(seg.duration_seconds)})
                    </p>
                  ))}
                </div>
              )}
            </div>

            {/* Audio List */}
            <div className="md:col-span-8">
              {isLoading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
                </div>
              ) : !audioFiles?.length ? (
                <div className="surface-card p-5 text-center py-12">
                  <Music className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-[var(--text-mid)]">No audio files yet</h3>
                  <p className="text-sm text-[var(--text-mid)]">
                    Upload your first audio file to get started
                  </p>
                </div>
              ) : (
                audioFiles.map((audio) => (
                  <div
                    key={audio.id}
                    className={`surface-card p-4 mb-3 cursor-pointer transition-colors hover:border-[var(--accent)] ${
                      selected?.id === audio.id ? 'border-2 border-[var(--accent)]' : ''
                    }`}
                    onClick={() => setSelected(audio)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Music className="h-4 w-4 text-[var(--accent)] shrink-0" />
                          <span className="font-semibold text-[var(--text-high)] truncate">
                            {audio.filename}
                          </span>
                          <Badge variant={STATUS_VARIANTS[audio.status] || 'default'}>
                            {audio.status}
                          </Badge>
                        </div>

                        <p className="text-sm text-[var(--text-mid)]">
                          {formatDuration(audio.duration_seconds)} | {audio.sample_rate} Hz | {audio.channels}ch | {audio.format.toUpperCase()} | {formatSize(audio.file_size_kb)}
                        </p>

                        <MiniWaveform data={audio.waveform_data} />

                        {/* Chapters */}
                        {audio.chapters.length > 0 && (
                          <div className="mt-2 flex gap-1 flex-wrap">
                            {audio.chapters.map((ch: Chapter, i: number) => (
                              <Badge key={i} variant="outline">
                                {ch.title} ({formatDuration(ch.start_time)})
                              </Badge>
                            ))}
                          </div>
                        )}

                        {/* Transcript snippet */}
                        {audio.transcript && (
                          <p className="text-sm text-[var(--text-mid)] mt-2 truncate">
                            {audio.transcript.slice(0, 150)}...
                          </p>
                        )}
                      </div>

                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              title="Delete"
                              className="p-1 rounded hover:bg-red-100 text-red-500"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteMutation.mutate(audio.id);
                                if (selected?.id === audio.id) setSelected(null);
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>Delete</TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </TabsContent>

        {/* ============================================================
            TAB 1: Podcast Episodes
            ============================================================ */}
        <TabsContent value="episodes">
          <div className="mt-5">
            {!episodes?.length ? (
              <div className="surface-card p-5 text-center py-12">
                <Podcast className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-[var(--text-mid)]">No episodes yet</h3>
                <p className="text-sm text-[var(--text-mid)]">
                  Select an audio file and create your first podcast episode
                </p>
              </div>
            ) : (
              episodes.map((ep) => (
                <div key={ep.id} className="surface-card p-4 mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Podcast className="h-5 w-5 text-purple-500" />
                    <h3 className="text-lg font-semibold text-[var(--text-high)]">{ep.title}</h3>
                    <Badge variant={ep.is_published ? 'success' : 'default'}>
                      {ep.is_published ? 'Published' : 'Draft'}
                    </Badge>
                  </div>
                  <p className="text-sm text-[var(--text-mid)] mb-2">
                    {ep.description || 'No description'}
                  </p>
                  {ep.publish_date && (
                    <span className="text-xs text-[var(--text-mid)]">
                      Published: {new Date(ep.publish_date).toLocaleDateString()}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* ============================================================
          EDIT DIALOG
          ============================================================ */}
      <Dialog open={editDialogOpen} onOpenChange={(v) => { if (!v) setEditDialogOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Audio</DialogTitle>
          </DialogHeader>
          {selected && (
            <div className="mt-2 space-y-4">
              <p className="text-sm font-medium text-[var(--text-high)]">
                {selected.filename} ({formatDuration(selected.duration_seconds)})
              </p>

              {/* Trim */}
              <p className="text-sm font-semibold text-[var(--text-high)]">Trim</p>
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="text-xs text-[var(--text-mid)]">Start (s)</label>
                  <Input
                    type="number"
                    value={trimStart}
                    onChange={(e) => setTrimStart(Number(e.target.value))}
                  />
                </div>
                <div className="flex-1">
                  <label className="text-xs text-[var(--text-mid)]">End (s)</label>
                  <Input
                    type="number"
                    value={trimEnd || selected.duration_seconds}
                    onChange={(e) => setTrimEnd(Number(e.target.value))}
                  />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEdit('trim', { start: trimStart, end: trimEnd || selected.duration_seconds })}
                >
                  Trim
                </Button>
              </div>

              <Separator />

              {/* Fade */}
              <p className="text-sm font-semibold text-[var(--text-high)]">Fade (seconds): {fadeDuration}</p>
              <Slider
                value={[fadeDuration]}
                min={0.5}
                max={10}
                step={0.5}
                onValueChange={(v) => setFadeDuration(v[0] ?? 0)}
                className="max-w-[300px]"
              />
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleEdit('fade_in', { duration: fadeDuration })}>
                  Fade In
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleEdit('fade_out', { duration: fadeDuration })}>
                  Fade Out
                </Button>
              </div>

              <Separator />

              {/* Speed */}
              <p className="text-sm font-semibold text-[var(--text-high)]">Speed: {speedFactor}x</p>
              <Slider
                value={[speedFactor]}
                min={0.5}
                max={3.0}
                step={0.1}
                onValueChange={(v) => setSpeedFactor(v[0] ?? 1)}
                className="max-w-[300px]"
              />
              <Button variant="outline" size="sm" onClick={() => handleEdit('speed_change', { factor: speedFactor })}>
                Apply Speed
              </Button>

              <Separator />

              {/* One-click operations */}
              <div className="flex gap-2 flex-wrap">
                <Button size="sm" onClick={() => handleEdit('normalize')}>
                  <Volume2 className="h-3.5 w-3.5 mr-1" /> Normalize
                </Button>
                <Button size="sm" onClick={() => handleEdit('noise_reduction')}>
                  Noise Reduction
                </Button>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ============================================================
          CREATE EPISODE DIALOG
          ============================================================ */}
      <Dialog open={episodeDialogOpen} onOpenChange={(v) => { if (!v) setEpisodeDialogOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Podcast Episode</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <Input
              placeholder="Episode Title"
              value={episodeTitle}
              onChange={(e) => setEpisodeTitle(e.target.value)}
            />
            <Textarea
              placeholder="Description"
              rows={3}
              value={episodeDescription}
              onChange={(e) => setEpisodeDescription(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEpisodeDialogOpen(false)}>Cancel</Button>
            <Button
              disabled={!episodeTitle.trim() || !selected || createEpisodeMutation.isPending}
              onClick={() => {
                if (!selected) return;
                createEpisodeMutation.mutate(
                  {
                    title: episodeTitle,
                    description: episodeDescription,
                    audio_id: selected.id,
                  },
                  { onSuccess: () => { setEpisodeDialogOpen(false); setTab('episodes'); } },
                );
              }}
            >
              {createEpisodeMutation.isPending ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Loading overlays for mutations */}
      {(transcribeMutation.isPending || chaptersMutation.isPending || editMutation.isPending) && (
        <div className="fixed bottom-6 right-6 z-[9999]">
          <div className="surface-card p-4 flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-[var(--accent)]" />
            <span className="text-sm text-[var(--text-high)]">
              {transcribeMutation.isPending && 'Transcribing...'}
              {chaptersMutation.isPending && 'Generating chapters...'}
              {editMutation.isPending && 'Applying edits...'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
