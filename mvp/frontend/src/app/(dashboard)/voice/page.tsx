'use client';

import { useState } from 'react';
import { Loader2, Mic, Volume2, Languages } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Slider } from '@/components/ui/slider';

import { useBuiltinVoices, useSynthesize, useSyntheses } from '@/features/voice/hooks/useVoice';

const STATUS_VARIANTS: Record<string, 'secondary' | 'success' | 'destructive' | 'default'> = {
  pending: 'secondary', processing: 'default', completed: 'success', failed: 'destructive',
};

export default function VoicePage() {
  const { data: voices } = useBuiltinVoices();
  const { data: syntheses, isLoading } = useSyntheses();
  const synthesizeMutation = useSynthesize();

  const [text, setText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('alloy');
  const [provider, setProvider] = useState('openai');
  const [speed, setSpeed] = useState(1.0);
  const [language, setLanguage] = useState('auto');

  const handleSynthesize = () => {
    if (!text.trim()) return;
    synthesizeMutation.mutate({
      text, voice_id: selectedVoice, provider, language, speed,
    });
  };

  const filteredVoices = voices?.filter((v) => v.provider === provider) || [];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-high)] flex items-center gap-2">
          <Mic className="h-7 w-7 text-[var(--accent)]" /> Voice Studio
        </h1>
        <p className="text-sm text-[var(--text-mid)]">
          AI voice cloning, text-to-speech, and automatic dubbing
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* TTS Input */}
        <div className="md:col-span-7">
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Text to Speech</h3>
              <Textarea
                rows={6}
                placeholder="Enter the text you want to convert to speech..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="mb-4"
              />

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Provider</label>
                  <Select value={provider} onValueChange={setProvider}>
                    <SelectTrigger>
                      <SelectValue placeholder="Provider" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI TTS</SelectItem>
                      <SelectItem value="elevenlabs">ElevenLabs</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Voice</label>
                  <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                    <SelectTrigger>
                      <SelectValue placeholder="Voice" />
                    </SelectTrigger>
                    <SelectContent>
                      {filteredVoices.map((v) => (
                        <SelectItem key={v.id} value={v.id}>{v.name} ({v.gender})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">Language</label>
                  <Select value={language} onValueChange={setLanguage}>
                    <SelectTrigger>
                      <SelectValue placeholder="Language" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Auto</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="mt-4 px-1">
                <span className="text-xs text-[var(--text-mid)]">Speed: {speed}x</span>
                <Slider
                  value={[speed]}
                  onValueChange={(v) => setSpeed(v[0] ?? 1)}
                  min={0.5}
                  max={2.0}
                  step={0.1}
                  className="mt-2"
                />
              </div>

              <Button
                className="w-full mt-4"
                onClick={handleSynthesize}
                disabled={!text.trim() || synthesizeMutation.isPending}
              >
                {synthesizeMutation.isPending
                  ? <><Loader2 className="h-4 w-4 animate-spin" /> Generating...</>
                  : <><Volume2 className="h-4 w-4" /> Generate Speech</>
                }
              </Button>

              {synthesizeMutation.isError && (
                <Alert variant="destructive" className="mt-4">
                  <AlertDescription>{synthesizeMutation.error.message}</AlertDescription>
                </Alert>
              )}
              {synthesizeMutation.isSuccess && (
                <Alert variant="success" className="mt-4">
                  <AlertDescription>
                    Audio generated! Status: {synthesizeMutation.data.status}
                    {synthesizeMutation.data.audio_url && (
                      <div className="mt-1">
                        <Badge variant="outline">Duration: ~{synthesizeMutation.data.duration_s?.toFixed(1)}s</Badge>
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>

        {/* History */}
        <div className="md:col-span-5">
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Synthesis History</h3>
              {isLoading ? <Skeleton className="h-[300px] w-full" /> : !syntheses?.length ? (
                <p className="text-sm text-[var(--text-mid)]">No syntheses yet</p>
              ) : (
                syntheses.map((s) => (
                  <Card key={s.id} className="mb-2 border border-[var(--border)]">
                    <CardContent className="py-3 px-4">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-1">
                          <Badge variant={STATUS_VARIANTS[s.status] || 'secondary'}>{s.status}</Badge>
                          <Badge variant="outline">{s.provider}</Badge>
                          {s.target_language && (
                            <Badge variant="outline" className="flex items-center gap-1">
                              <Languages className="h-3 w-3" />{s.target_language}
                            </Badge>
                          )}
                        </div>
                        {s.duration_s && <span className="text-xs text-[var(--text-mid)]">{s.duration_s.toFixed(1)}s</span>}
                      </div>
                      <span className="text-xs text-[var(--text-mid)] mt-1 block">
                        {new Date(s.created_at).toLocaleString()}
                      </span>
                    </CardContent>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
