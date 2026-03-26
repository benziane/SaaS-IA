'use client';

import { useState } from 'react';
import { Copy, FileText, Loader2, Plus, RefreshCw, Sparkles, Trash2 } from 'lucide-react';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Separator } from '@/lib/design-hub/components/Separator';
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from '@/lib/design-hub/components/Dialog';
import {
  Tooltip, TooltipTrigger, TooltipContent, TooltipProvider,
} from '@/lib/design-hub/components/Tooltip';

import {
  useCreateProject,
  useDeleteProject,
  useGenerateContents,
  useProjectContents,
  useProjects,
  useRegenerateContent,
} from '@/features/content-studio/hooks/useContentStudio';
import type { GeneratedContent } from '@/features/content-studio/types';

const FORMAT_OPTIONS = [
  { id: 'blog_article', label: 'Blog Article', icon: '📝' },
  { id: 'twitter_thread', label: 'Twitter/X Thread', icon: '🐦' },
  { id: 'linkedin_post', label: 'LinkedIn Post', icon: '💼' },
  { id: 'newsletter', label: 'Newsletter', icon: '📧' },
  { id: 'instagram_carousel', label: 'Instagram Carousel', icon: '📸' },
  { id: 'youtube_description', label: 'YouTube Description', icon: '🎬' },
  { id: 'seo_meta', label: 'SEO Metadata', icon: '🔍' },
  { id: 'press_release', label: 'Press Release', icon: '📰' },
  { id: 'email_campaign', label: 'Email Campaign', icon: '📨' },
  { id: 'podcast_notes', label: 'Podcast Notes', icon: '🎙️' },
];

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive' | 'warning' | 'outline'> = {
  draft: 'secondary',
  generating: 'default',
  generated: 'success',
  published: 'default',
  scheduled: 'warning',
  failed: 'destructive',
};

const TONE_OPTIONS = ['professional', 'casual', 'engaging', 'formal', 'humorous', 'inspirational', 'educational'];

export default function ContentStudioPage() {
  const { data: projects, isLoading } = useProjects();
  const createMutation = useCreateProject();
  const deleteMutation = useDeleteProject();

  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [tone, setTone] = useState('professional');
  const [audience, setAudience] = useState('');
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['blog_article', 'twitter_thread', 'linkedin_post']);

  const [activeProject, setActiveProject] = useState<string | null>(null);
  const [viewContent, setViewContent] = useState<GeneratedContent | null>(null);

  const { data: contents, isLoading: contentsLoading } = useProjectContents(activeProject);
  const generateMutation = useGenerateContents(activeProject || '');
  const regenerateMutation = useRegenerateContent();

  const handleCreate = () => {
    if (!title.trim() || !sourceText.trim()) return;
    createMutation.mutate(
      {
        title,
        source_type: 'text',
        source_text: sourceText,
        tone,
        target_audience: audience || undefined,
      },
      {
        onSuccess: (project) => {
          setCreateOpen(false);
          setTitle('');
          setSourceText('');
          setActiveProject(project.id);
          // Auto-generate
          generateMutation.mutate({ formats: selectedFormats });
        },
      }
    );
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <TooltipProvider>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-high)] flex items-center gap-2">
              <Sparkles className="h-7 w-7 text-[var(--accent)]" /> Content Studio
            </h1>
            <p className="text-sm text-[var(--text-mid)]">
              Transform any content into blog articles, social media posts, newsletters, and more
            </p>
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-1" /> New Project
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Projects List */}
          <div className="md:col-span-4">
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Projects</h3>
                {isLoading ? (
                  <Skeleton className="h-[200px] w-full" />
                ) : !projects?.length ? (
                  <div className="text-center py-8">
                    <FileText className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                    <p className="text-sm text-[var(--text-mid)]">No projects yet</p>
                    <Button variant="ghost" size="sm" onClick={() => setCreateOpen(true)} className="mt-2">
                      Create your first project
                    </Button>
                  </div>
                ) : (
                  projects.map((project) => (
                    <Card
                      key={project.id}
                      className={`mb-2 border cursor-pointer transition-colors ${
                        activeProject === project.id
                          ? 'border-[var(--accent)] bg-[var(--bg-elevated)]'
                          : 'border-[var(--border)] hover:bg-[var(--bg-elevated)]'
                      }`}
                      onClick={() => setActiveProject(project.id)}
                    >
                      <CardContent className="py-3 px-4">
                        <h4 className="text-sm font-medium text-[var(--text-high)]">{project.title}</h4>
                        <div className="flex gap-1 mt-1">
                          <Badge variant="outline">{project.source_type}</Badge>
                          <Badge variant="outline">{project.tone}</Badge>
                        </div>
                      </CardContent>
                      <CardFooter className="pt-0 justify-end px-4 pb-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-red-400 hover:text-red-300"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteMutation.mutate(project.id);
                            if (activeProject === project.id) setActiveProject(null);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </CardFooter>
                    </Card>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Generated Contents */}
          <div className="md:col-span-8">
            {activeProject ? (
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-[var(--text-high)]">Generated Content</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => generateMutation.mutate({ formats: selectedFormats })}
                      disabled={generateMutation.isPending}
                    >
                      {generateMutation.isPending
                        ? <><Loader2 className="h-4 w-4 animate-spin mr-1" /> Generating...</>
                        : <><Sparkles className="h-4 w-4 mr-1" /> Generate More</>
                      }
                    </Button>
                  </div>

                  {/* Format selector for generation */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {FORMAT_OPTIONS.map((fmt) => (
                      <Badge
                        key={fmt.id}
                        variant={selectedFormats.includes(fmt.id) ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => {
                          setSelectedFormats((prev) =>
                            prev.includes(fmt.id) ? prev.filter((f) => f !== fmt.id) : [...prev, fmt.id]
                          );
                        }}
                      >
                        {fmt.icon} {fmt.label}
                      </Badge>
                    ))}
                  </div>

                  <Separator className="mb-4" />

                  {contentsLoading ? (
                    <Skeleton className="h-[300px] w-full" />
                  ) : !contents?.length ? (
                    <div className="text-center py-8">
                      <p className="text-sm text-[var(--text-mid)]">
                        {generateMutation.isPending
                          ? 'Generating content with AI...'
                          : 'Select formats above and click "Generate More"'}
                      </p>
                      {generateMutation.isPending && <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)] mx-auto mt-4" />}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {contents.map((content) => {
                        const fmtInfo = FORMAT_OPTIONS.find((f) => f.id === content.format);
                        return (
                          <Card
                            key={content.id}
                            className="border border-[var(--border)] cursor-pointer hover:border-[var(--accent)] transition-colors"
                            onClick={() => setViewContent(content)}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-medium text-[var(--text-high)]">
                                  {fmtInfo?.icon} {fmtInfo?.label || content.format}
                                </h4>
                                <Badge variant={STATUS_VARIANTS[content.status] || 'secondary'}>
                                  {content.status}
                                </Badge>
                              </div>
                              {content.title && (
                                <p className="text-sm font-bold text-[var(--text-high)] mb-1">{content.title}</p>
                              )}
                              <p className="text-sm text-[var(--text-mid)] overflow-hidden line-clamp-3">
                                {content.content.substring(0, 200)}...
                              </p>
                              <div className="flex items-center justify-between mt-2">
                                <span className="text-xs text-[var(--text-mid)]">
                                  {content.word_count} words | v{content.version}
                                </span>
                                <span className="text-xs text-[var(--text-mid)]">
                                  {content.provider}
                                </span>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  )}

                  {generateMutation.isError && (
                    <Alert variant="destructive" className="mt-4">
                      <AlertDescription>{generateMutation.error?.message}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-16 px-6">
                  <Sparkles className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-[var(--text-mid)]">
                    Select a project or create a new one
                  </h3>
                  <p className="text-sm text-[var(--text-mid)] mt-2">
                    Paste any text, select a transcription, or enter a URL to generate multi-format content
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Create Project Dialog */}
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>New Content Project</DialogTitle>
              <DialogDescription>Create a new project and generate multi-format content with AI.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div>
                <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Project Title</label>
                <Input
                  placeholder="Project title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Source Text</label>
                <Textarea
                  rows={8}
                  placeholder="Paste the content you want to transform (article, transcription, notes...)"
                  value={sourceText}
                  onChange={(e) => setSourceText(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Tone</label>
                  <Select value={tone} onValueChange={setTone}>
                    <SelectTrigger>
                      <SelectValue placeholder="Tone" />
                    </SelectTrigger>
                    <SelectContent>
                      {TONE_OPTIONS.map((t) => (
                        <SelectItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Target Audience (optional)</label>
                  <Input
                    placeholder="e.g., tech professionals, students"
                    value={audience}
                    onChange={(e) => setAudience(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <h4 className="text-sm font-medium text-[var(--text-high)] mb-2">Output Formats</h4>
                <div className="flex flex-wrap gap-1.5">
                  {FORMAT_OPTIONS.map((fmt) => (
                    <Badge
                      key={fmt.id}
                      variant={selectedFormats.includes(fmt.id) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        setSelectedFormats((prev) =>
                          prev.includes(fmt.id) ? prev.filter((f) => f !== fmt.id) : [...prev, fmt.id]
                        );
                      }}
                    >
                      {fmt.icon} {fmt.label}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button
                onClick={handleCreate}
                disabled={!title.trim() || !sourceText.trim() || selectedFormats.length === 0 || createMutation.isPending}
              >
                {createMutation.isPending
                  ? <><Loader2 className="h-4 w-4 animate-spin mr-1" /> Creating...</>
                  : <><Sparkles className="h-4 w-4 mr-1" /> Create &amp; Generate</>
                }
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Content Viewer Dialog */}
        <Dialog open={!!viewContent} onOpenChange={(open) => { if (!open) setViewContent(null); }}>
          <DialogContent className="max-w-2xl">
            {viewContent && (
              <>
                <DialogHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <DialogTitle>
                        {FORMAT_OPTIONS.find((f) => f.id === viewContent.format)?.icon}{' '}
                        {FORMAT_OPTIONS.find((f) => f.id === viewContent.format)?.label}
                      </DialogTitle>
                      {viewContent.title && (
                        <p className="text-sm text-[var(--text-mid)] mt-1">{viewContent.title}</p>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="ghost" size="icon" onClick={() => handleCopy(viewContent.content)}>
                            <Copy className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Copy to clipboard</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              regenerateMutation.mutate({ id: viewContent.id });
                              setViewContent(null);
                            }}
                            disabled={regenerateMutation.isPending}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Regenerate</TooltipContent>
                      </Tooltip>
                    </div>
                  </div>
                </DialogHeader>
                <Separator />
                <div
                  className={`whitespace-pre-wrap text-sm leading-relaxed ${
                    viewContent.format === 'seo_meta' ? 'font-mono' : ''
                  }`}
                >
                  {viewContent.content}
                </div>
                <Separator />
                <div className="flex items-center gap-4">
                  <span className="text-xs text-[var(--text-mid)]">{viewContent.word_count} words</span>
                  <span className="text-xs text-[var(--text-mid)]">Version {viewContent.version}</span>
                  <span className="text-xs text-[var(--text-mid)]">Provider: {viewContent.provider}</span>
                  <Badge variant={STATUS_VARIANTS[viewContent.status] || 'secondary'}>{viewContent.status}</Badge>
                </div>
                <DialogFooter>
                  <Button variant="ghost" onClick={() => setViewContent(null)}>Close</Button>
                  <Button onClick={() => handleCopy(viewContent.content)}>
                    <Copy className="h-4 w-4 mr-1" /> Copy Content
                  </Button>
                </DialogFooter>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
