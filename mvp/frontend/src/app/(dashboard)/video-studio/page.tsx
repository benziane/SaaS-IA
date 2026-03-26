'use client';

import { useState } from 'react';
import { Loader2, Video, Sparkles, Trash2, Clapperboard, User } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Slider } from '@/components/ui/slider';

import { useDeleteVideo, useGenerateAvatar, useGenerateVideo, useVideos } from '@/features/video-gen/hooks/useVideoGen';

const VIDEO_TYPES = [
  { id: 'text_to_video', label: 'Text to Video', icon: '🎬' },
  { id: 'explainer', label: 'Explainer', icon: '📖' },
  { id: 'short_form', label: 'Short Form', icon: '📱' },
  { id: 'avatar_talking', label: 'Talking Avatar', icon: '🧑' },
];

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive'> = {
  pending: 'secondary', generating: 'default', processing: 'default', completed: 'success', failed: 'destructive',
};

export default function VideoStudioPage() {
  const { data: videos, isLoading } = useVideos();
  const genMutation = useGenerateVideo();
  const avatarMutation = useGenerateAvatar();
  const deleteMutation = useDeleteVideo();

  const [title, setTitle] = useState('');
  const [prompt, setPrompt] = useState('');
  const [videoType, setVideoType] = useState('text_to_video');
  const [duration, setDuration] = useState(10);
  const [avatarText, setAvatarText] = useState('');

  const handleGenerate = () => {
    if (!title.trim() || !prompt.trim()) return;
    genMutation.mutate({ title, prompt, video_type: videoType, duration_s: duration });
  };

  const handleAvatar = () => {
    if (!avatarText.trim()) return;
    avatarMutation.mutate({ text: avatarText });
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-high)] flex items-center gap-2">
          <Video className="h-7 w-7 text-[var(--accent)]" /> Video Studio
        </h1>
        <p className="text-sm text-[var(--text-mid)]">
          Generate AI videos, highlight clips, talking avatars, and explainer videos
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Generation */}
        <div className="md:col-span-5">
          <Card className="mb-4">
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
                <Clapperboard className="h-5 w-5" /> Generate Video
              </h3>
              <Input
                placeholder="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mb-4"
              />
              <Textarea
                rows={3}
                placeholder="Describe the video you want to create..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="mb-4"
              />

              <div className="flex flex-wrap gap-1.5 mb-4">
                {VIDEO_TYPES.filter((t) => t.id !== 'avatar_talking').map((t) => (
                  <Badge
                    key={t.id}
                    variant={videoType === t.id ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => setVideoType(t.id)}
                  >
                    {t.icon} {t.label}
                  </Badge>
                ))}
              </div>

              <p className="text-xs text-[var(--text-low)] mb-1">Duration: {duration}s</p>
              <Slider
                value={[duration]}
                onValueChange={(v) => setDuration(v[0] ?? 5)}
                min={5}
                max={120}
                step={5}
                className="mb-4"
              />

              <Button
                className="w-full"
                onClick={handleGenerate}
                disabled={!title.trim() || !prompt.trim() || genMutation.isPending}
              >
                {genMutation.isPending ? (
                  <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Generating...</>
                ) : (
                  <><Sparkles className="h-4 w-4 mr-2" /> Generate Video</>
                )}
              </Button>
              {genMutation.isError && (
                <Alert variant="destructive" className="mt-2">
                  <AlertDescription>{genMutation.error.message}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Avatar */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
                <User className="h-5 w-5" /> Talking Avatar
              </h3>
              <Textarea
                rows={3}
                placeholder="What should the avatar say?"
                value={avatarText}
                onChange={(e) => setAvatarText(e.target.value)}
                className="mb-4"
              />
              <Button
                variant="outline"
                className="w-full"
                onClick={handleAvatar}
                disabled={!avatarText.trim() || avatarMutation.isPending}
              >
                {avatarMutation.isPending ? (
                  <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Generating...</>
                ) : (
                  <><User className="h-4 w-4 mr-2" /> Generate Avatar Video</>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Gallery */}
        <div className="md:col-span-7">
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Videos</h3>
              {isLoading ? <Skeleton className="h-[400px] w-full" /> : !videos?.length ? (
                <div className="text-center py-12">
                  <Video className="h-16 w-16 text-[var(--text-low)] mx-auto mb-2" />
                  <p className="text-[var(--text-mid)]">No videos yet</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {videos.map((v) => (
                    <Card key={v.id} className="border border-[var(--border)]">
                      <div className="h-[120px] bg-[var(--bg-elevated)] flex items-center justify-center">
                        {v.status === 'completed' ? (
                          <span className="text-xs p-2 text-[var(--text-mid)]">{v.title}</span>
                        ) : v.status === 'failed' ? (
                          <span className="text-xs text-red-400">Failed</span>
                        ) : (
                          <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
                        )}
                      </div>
                      <CardContent className="py-2 px-3">
                        <p className="text-sm font-medium text-[var(--text-high)] truncate">{v.title}</p>
                        <div className="flex justify-between items-center mt-1">
                          <div className="flex gap-1">
                            <Badge variant="outline" className="text-[10px]">{v.video_type.replace('_', ' ')}</Badge>
                            <Badge variant={STATUS_VARIANTS[v.status] || 'secondary'} className="text-[10px]">{v.status}</Badge>
                            {v.duration_s && <Badge variant="outline" className="text-[10px]">{v.duration_s}s</Badge>}
                          </div>
                          <button
                            type="button"
                            onClick={() => deleteMutation.mutate(v.id)}
                            className="p-1 text-red-400 hover:text-red-300 transition-colors"
                            aria-label="Delete video"
                            title="Delete video"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
