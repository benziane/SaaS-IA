'use client';

import { useState } from 'react';
import { ImageIcon, Loader2, Sparkles, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Input } from '@/lib/design-hub/components/Input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';

import { useDeleteImage, useGenerateImage, useImages } from '@/features/image-gen/hooks/useImageGen';

const STYLES = [
  { id: 'realistic', label: 'Realistic', icon: '📷' },
  { id: 'artistic', label: 'Artistic', icon: '🎨' },
  { id: 'cartoon', label: 'Cartoon', icon: '🖍️' },
  { id: 'digital_art', label: 'Digital Art', icon: '💠' },
  { id: 'photography', label: 'Photography', icon: '📸' },
  { id: '3d_render', label: '3D Render', icon: '🧊' },
  { id: 'minimalist', label: 'Minimalist', icon: '⬜' },
  { id: 'watercolor', label: 'Watercolor', icon: '🌊' },
];

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive'> = {
  pending: 'secondary', generating: 'default', completed: 'success', failed: 'destructive',
};

export default function ImagesPage() {
  const { data: images, isLoading } = useImages();
  const genMutation = useGenerateImage();
  const deleteMutation = useDeleteImage();

  const [prompt, setPrompt] = useState('');
  const [negPrompt, setNegPrompt] = useState('');
  const [style, setStyle] = useState('digital_art');
  const [width, setWidth] = useState(1024);
  const [height, setHeight] = useState(1024);

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    genMutation.mutate({ prompt, negative_prompt: negPrompt || undefined, style, width, height });
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <ImageIcon className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Image Studio</h1>
          <p className="text-xs text-[var(--text-mid)]">Generate AI images, thumbnails, and visual content</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
        <div className="md:col-span-5">
          <div className="surface-card p-5">
            <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Generate Image</h3>
            <Textarea
              rows={4}
              placeholder="Describe the image you want to create..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="mb-4"
            />
            <Input
              placeholder="Negative prompt — what to avoid... (optional)"
              value={negPrompt}
              onChange={(e) => setNegPrompt(e.target.value)}
              className="mb-4"
            />

            <h4 className="text-sm font-medium text-[var(--text-high)] mb-2">Style</h4>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {STYLES.map((s) => (
                <Badge
                  key={s.id}
                  variant={style === s.id ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setStyle(s.id)}
                >
                  {s.icon} {s.label}
                </Badge>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-2 mb-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Width</label>
                <Select value={String(width)} onValueChange={(v) => setWidth(Number(v))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Width" />
                  </SelectTrigger>
                  <SelectContent>
                    {[512, 768, 1024, 1280, 1536, 1920].map((w) => (
                      <SelectItem key={w} value={String(w)}>{w}px</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Height</label>
                <Select value={String(height)} onValueChange={(v) => setHeight(Number(v))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Height" />
                  </SelectTrigger>
                  <SelectContent>
                    {[512, 768, 1024, 1280, 1536, 1920].map((h) => (
                      <SelectItem key={h} value={String(h)}>{h}px</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button
              className="w-full"
              onClick={handleGenerate}
              disabled={!prompt.trim() || genMutation.isPending}
            >
              {genMutation.isPending
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Generating...</>
                : <><Sparkles className="h-4 w-4" /> Generate Image</>
              }
            </Button>
            {genMutation.isError && (
              <Alert variant="destructive" className="mt-4">
                <AlertDescription>{genMutation.error.message}</AlertDescription>
              </Alert>
            )}
          </div>
        </div>

        <div className="md:col-span-7">
          <div className="surface-card p-5">
            <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Gallery</h3>
            {isLoading ? <Skeleton className="h-[400px] w-full" /> : !images?.length ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] mx-auto mb-3">
                  <ImageIcon className="h-8 w-8 text-white" />
                </div>
                <p className="text-sm text-[var(--text-mid)]">No images yet. Generate your first one!</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {images.map((img) => (
                  <div key={img.id} className="surface-card p-0 border border-[var(--border)] relative overflow-hidden">
                    <div className="h-40 bg-[var(--bg-elevated)] flex items-center justify-center">
                      {img.status === 'completed' ? (
                        <span className="text-xs text-[var(--text-mid)] p-2 text-center">{img.prompt.substring(0, 60)}...</span>
                      ) : img.status === 'generating' ? (
                        <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
                      ) : (
                        <span className="text-xs text-red-400">Failed</span>
                      )}
                    </div>
                    <div className="p-2 flex justify-between items-center">
                      <div className="flex gap-1">
                        <Badge variant="outline">{img.style}</Badge>
                        <Badge variant={STATUS_VARIANTS[img.status] || 'secondary'}>{img.status}</Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-red-400 hover:text-red-300"
                        onClick={() => deleteMutation.mutate(img.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
