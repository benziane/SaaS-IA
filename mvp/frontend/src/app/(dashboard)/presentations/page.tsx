'use client';

import { useState } from 'react';
import {
  Plus, Trash2, Presentation, Download, ChevronLeft, ChevronRight, Copy, Loader2,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import {
  useCreatePresentation,
  useDeletePresentation,
  useExportPresentation,
  usePresentations,
} from '@/features/presentation-gen/hooks/usePresentationGen';
import type { Presentation as PresentationType, SlideContent } from '@/features/presentation-gen/types';

const TEMPLATE_OPTIONS = [
  { id: 'default', label: 'Default' },
  { id: 'pitch_deck', label: 'Pitch Deck' },
  { id: 'report', label: 'Report' },
  { id: 'tutorial', label: 'Tutorial' },
  { id: 'meeting', label: 'Meeting' },
  { id: 'proposal', label: 'Proposal' },
];

const STYLE_OPTIONS = ['professional', 'creative', 'minimal', 'corporate', 'academic', 'dark', 'colorful'];

const STATUS_VARIANTS: Record<string, 'default' | 'success' | 'destructive' | 'secondary'> = {
  generating: 'secondary',
  ready: 'success',
  error: 'destructive',
};

export default function PresentationsPage() {
  const { data: presentations, isLoading } = usePresentations();
  const createMutation = useCreatePresentation();
  const deleteMutation = useDeletePresentation();

  // Create dialog state
  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [numSlides, setNumSlides] = useState(10);
  const [style, setStyle] = useState('professional');
  const [template, setTemplate] = useState('default');
  const [language, setLanguage] = useState('fr');
  const [sourceText, setSourceText] = useState('');

  // Viewer state
  const [activePresentation, setActivePresentation] = useState<PresentationType | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [exportOpen, setExportOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'html' | 'markdown' | 'pdf'>('html');

  const exportMutation = useExportPresentation(activePresentation?.id || '');

  const handleCreate = () => {
    if (!title.trim() || !topic.trim()) return;
    createMutation.mutate(
      {
        title,
        topic,
        num_slides: numSlides,
        style,
        template,
        language,
        source_text: sourceText || undefined,
      },
      {
        onSuccess: (pres) => {
          setCreateOpen(false);
          setTitle('');
          setTopic('');
          setSourceText('');
          setActivePresentation(pres);
          setCurrentSlide(0);
        },
      },
    );
  };

  const handleExport = () => {
    exportMutation.mutate(
      { format: exportFormat },
      {
        onSuccess: (result) => {
          if (result.content) {
            const blob = new Blob([result.content], {
              type: exportFormat === 'html' ? 'text/html' : 'text/markdown',
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename;
            a.click();
            URL.revokeObjectURL(url);
          }
          setExportOpen(false);
        },
      },
    );
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const slides: SlideContent[] = activePresentation?.slides || [];
  const slide = slides[currentSlide] || null;

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Presentation className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Presentations</h1>
            <p className="text-xs text-[var(--text-mid)]">AI-powered slide generation</p>
          </div>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> New Presentation
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
        {/* Presentations List */}
        <div className="md:col-span-4">
          <div className="surface-card p-5">
            <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">My Presentations</h3>
            {isLoading ? (
              <Skeleton className="h-52 rounded-lg" />
            ) : !presentations?.length ? (
              <div className="text-center py-8">
                <Presentation className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                <p className="text-[var(--text-mid)]">No presentations yet</p>
                <Button size="sm" variant="outline" className="mt-2" onClick={() => setCreateOpen(true)}>
                  Create your first presentation
                </Button>
              </div>
            ) : (
              presentations.map((pres) => (
                <div
                  key={pres.id}
                  className={`surface-card mb-2 cursor-pointer border border-[var(--border)] transition-colors hover:bg-[var(--bg-hover)] ${
                    activePresentation?.id === pres.id ? 'bg-[var(--bg-surface)]' : ''
                  }`}
                  onClick={() => {
                    setActivePresentation(pres);
                    setCurrentSlide(0);
                  }}
                >
                  <div className="py-3 px-4">
                    <p className="text-sm font-medium text-[var(--text-high)]">{pres.title}</p>
                    <span className="text-xs text-[var(--text-mid)] block mt-1">
                      {pres.topic.substring(0, 80)}{pres.topic.length > 80 ? '...' : ''}
                    </span>
                    <div className="flex gap-1 mt-1 flex-wrap">
                      <Badge variant="outline">{pres.template}</Badge>
                      <Badge variant="outline">{pres.num_slides} slides</Badge>
                      <Badge variant={STATUS_VARIANTS[pres.status] || 'default'}>{pres.status}</Badge>
                    </div>
                  </div>
                  <div className="flex justify-end pt-0 px-4 pb-2">
                    <button
                      type="button"
                      title="Delete"
                      className="p-1 rounded hover:bg-red-100 text-red-500"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteMutation.mutate(pres.id);
                        if (activePresentation?.id === pres.id) setActivePresentation(null);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Slide Viewer */}
        <div className="md:col-span-8">
          {activePresentation && slide ? (
            <div className="surface-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-[var(--text-high)]">{activePresentation.title}</h3>
                <div className="flex gap-2">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button type="button" title="Export" className="p-1.5 rounded hover:bg-[var(--bg-hover)]" onClick={() => setExportOpen(true)}>
                          <Download className="h-5 w-5 text-[var(--text-mid)]" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Export</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button type="button" title="Copy slide content" className="p-1.5 rounded hover:bg-[var(--bg-hover)]" onClick={() => handleCopy(slide.content)}>
                          <Copy className="h-5 w-5 text-[var(--text-mid)]" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Copy slide content</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>

              {/* Slide display */}
              <div className="surface-card min-h-[400px] flex flex-col justify-center p-8 bg-gray-50 dark:bg-gray-900 border border-[var(--border)]">
                <h2
                  className={`mb-4 font-bold ${
                    slide.layout === 'title_slide' ? 'text-3xl text-center' : 'text-xl'
                  } ${
                    slide.layout === 'section_header' ? 'text-center' : ''
                  } text-[var(--text-high)]`}
                >
                  {slide.title}
                </h2>
                <p
                  className={`text-[var(--text-high)] whitespace-pre-wrap leading-relaxed ${
                    slide.layout === 'quote' ? 'text-center italic' : ''
                  }`}
                >
                  {slide.content}
                </p>
                {slide.notes && (
                  <div className="mt-6 pt-4 border-t border-dashed border-[var(--border)]">
                    <span className="text-xs text-[var(--text-mid)]">
                      Speaker notes: {slide.notes}
                    </span>
                  </div>
                )}
              </div>

              {/* Navigation */}
              <div className="flex items-center justify-center gap-4 mt-4">
                <button
                  type="button"
                  title="Previous slide"
                  className="p-1.5 rounded hover:bg-[var(--bg-hover)] disabled:opacity-40"
                  onClick={() => setCurrentSlide((prev) => Math.max(0, prev - 1))}
                  disabled={currentSlide === 0}
                >
                  <ChevronLeft className="h-5 w-5 text-[var(--text-mid)]" />
                </button>
                <span className="text-sm text-[var(--text-mid)]">
                  Slide {currentSlide + 1} / {slides.length}
                </span>
                <button
                  type="button"
                  title="Next slide"
                  className="p-1.5 rounded hover:bg-[var(--bg-hover)] disabled:opacity-40"
                  onClick={() => setCurrentSlide((prev) => Math.min(slides.length - 1, prev + 1))}
                  disabled={currentSlide === slides.length - 1}
                >
                  <ChevronRight className="h-5 w-5 text-[var(--text-mid)]" />
                </button>
              </div>

              {/* Slide thumbnails */}
              <div className="flex gap-1 mt-4 overflow-x-auto pb-2">
                {slides.map((s, idx) => (
                  <Badge
                    key={idx}
                    variant={idx === currentSlide ? 'default' : 'outline'}
                    className="cursor-pointer shrink-0"
                    onClick={() => setCurrentSlide(idx)}
                  >
                    {idx + 1}. {s.title.substring(0, 20)}{s.title.length > 20 ? '...' : ''}
                  </Badge>
                ))}
              </div>

              <Separator className="my-4" />
              <div className="flex gap-4">
                <span className="text-xs text-[var(--text-mid)]">Template: {activePresentation.template}</span>
                <span className="text-xs text-[var(--text-mid)]">Style: {activePresentation.style}</span>
                <span className="text-xs text-[var(--text-mid)]">Layout: {slide.layout}</span>
              </div>
            </div>
          ) : (
            <div className="surface-card p-5 text-center py-16">
              <Presentation className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[var(--text-mid)]">
                Select a presentation or create a new one
              </h3>
              <p className="text-sm text-[var(--text-mid)] mt-2">
                Enter a topic, choose a template, and let AI generate your slide deck
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create Presentation Dialog */}
      <Dialog open={createOpen} onOpenChange={(v) => { if (!v) setCreateOpen(false); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Presentation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <Input
              placeholder="Title (e.g., Introduction to AI in Healthcare)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <Textarea
              rows={3}
              placeholder="Topic / Description - Describe the subject, key points, and goals"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            <Textarea
              rows={4}
              placeholder="Source Text (optional) - Paste any reference material, article, or notes"
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
            />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-[var(--text-mid)] mb-1 block">Slides</label>
                <Input
                  type="number"
                  value={numSlides}
                  onChange={(e) => setNumSlides(Math.max(3, Math.min(50, parseInt(e.target.value) || 10)))}
                  min={3}
                  max={50}
                />
              </div>
              <div>
                <label className="text-xs text-[var(--text-mid)] mb-1 block">Template</label>
                <Select value={template} onValueChange={setTemplate}>
                  <SelectTrigger>
                    <SelectValue placeholder="Template" />
                  </SelectTrigger>
                  <SelectContent>
                    {TEMPLATE_OPTIONS.map((t) => (
                      <SelectItem key={t.id} value={t.id}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs text-[var(--text-mid)] mb-1 block">Style</label>
                <Select value={style} onValueChange={setStyle}>
                  <SelectTrigger>
                    <SelectValue placeholder="Style" />
                  </SelectTrigger>
                  <SelectContent>
                    {STYLE_OPTIONS.map((s) => (
                      <SelectItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs text-[var(--text-mid)] mb-1 block">Language</label>
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger>
                    <SelectValue placeholder="Language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fr">French</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Spanish</SelectItem>
                    <SelectItem value="de">German</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreate}
              disabled={!title.trim() || !topic.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Presentation className="h-4 w-4 mr-2" />
              )}
              {createMutation.isPending ? 'Generating...' : 'Generate Presentation'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportOpen} onOpenChange={(v) => { if (!v) setExportOpen(false); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Export Presentation</DialogTitle>
          </DialogHeader>
          <div className="mt-2">
            <label className="text-xs text-[var(--text-mid)] mb-1 block">Format</label>
            <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as 'html' | 'markdown' | 'pdf')}>
              <SelectTrigger>
                <SelectValue placeholder="Format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="html">HTML (interactive)</SelectItem>
                <SelectItem value="markdown">Markdown</SelectItem>
                <SelectItem value="pdf">PDF (requires marp-cli)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExportOpen(false)}>Cancel</Button>
            <Button
              onClick={handleExport}
              disabled={exportMutation.isPending}
            >
              {exportMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              {exportMutation.isPending ? 'Exporting...' : 'Export'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Errors */}
      {createMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{createMutation.error?.message}</AlertDescription>
        </Alert>
      )}
      {exportMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{exportMutation.error?.message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
