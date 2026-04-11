'use client';

import { useRef, useState } from 'react';
import {
  Radio, Bot, Mic, Square, Send, History, Loader2,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';

import {
  useCreateSession, useEndSession, useRealtimeSessions, useSendMessage,
} from '@/features/realtime/hooks/useRealtime';
import type { RealtimeSession } from '@/features/realtime/types';

const MODE_ICONS: Record<string, string> = {
  voice: '🎤', vision: '👁️', voice_vision: '🎤👁️', meeting: '🏢',
};
const STATUS_VARIANTS: Record<string, 'success' | 'default' | 'destructive' | 'warning'> = {
  active: 'success', paused: 'warning', ended: 'default', failed: 'destructive',
};

export default function RealtimePage() {
  const { data: sessions, isLoading } = useRealtimeSessions();
  const createMutation = useCreateSession();
  const endMutation = useEndSession();

  const [activeSession, setActiveSession] = useState<RealtimeSession | null>(null);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [mode, setMode] = useState('voice');
  const [provider, setProvider] = useState('gemini');
  const [systemPrompt, setSystemPrompt] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  const sendMutation = useSendMessage(activeSession?.id || '');

  const handleCreate = () => {
    createMutation.mutate(
      { title: `Session ${new Date().toLocaleTimeString()}`, mode, provider, system_prompt: systemPrompt || undefined },
      { onSuccess: (s) => { setActiveSession(s); setChatHistory([]); } },
    );
  };

  const handleSend = () => {
    if (!message.trim() || !activeSession) return;
    const userMsg = message;
    setChatHistory((prev) => [...prev, { role: 'user', content: userMsg }]);
    setMessage('');
    sendMutation.mutate(userMsg, {
      onSuccess: (result) => {
        const aiMsg = (result as Record<string, Record<string, string>>).ai_message;
        if (aiMsg) setChatHistory((prev) => [...prev, { role: 'assistant', content: aiMsg.content ?? '' }]);
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      },
    });
  };

  const handleEnd = () => {
    if (!activeSession) return;
    endMutation.mutate(activeSession.id, {
      onSuccess: () => { setActiveSession(null); setChatHistory([]); },
    });
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Radio className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Realtime AI</h1>
          <p className="text-xs text-[var(--text-mid)]">Real-time AI voice and vision sessions</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Chat Area */}
        <div className="md:col-span-8">
          {activeSession ? (
            <div className="surface-card h-[70vh] flex flex-col">
              <div className="p-4 flex justify-between items-center border-b border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <Badge>{MODE_ICONS[activeSession.mode] || '🎤'}</Badge>
                  <span className="font-medium text-[var(--text-high)]">{activeSession.title}</span>
                  <Badge variant="success">LIVE</Badge>
                </div>
                <Button variant="outline" size="sm" className="text-red-500 border-red-500 hover:bg-red-50" onClick={handleEnd}>
                  <Square className="h-3.5 w-3.5 mr-1" /> End Session
                </Button>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-auto p-4">
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} mb-3`}>
                    <div className={`max-w-[75%] p-3 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-[var(--accent)] text-white'
                        : 'bg-[var(--bg-surface)] text-[var(--text-high)]'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {sendMutation.isPending && (
                  <div className="flex gap-2 items-center text-[var(--text-mid)]">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-xs">AI is thinking...</span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t border-[var(--border)] flex gap-2">
                <Input
                  placeholder="Type a message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                />
                <button
                  type="button"
                  title="Send"
                  className="p-2 rounded text-[var(--accent)] hover:bg-[var(--bg-hover)] disabled:opacity-40"
                  onClick={handleSend}
                  disabled={!message.trim() || sendMutation.isPending}
                >
                  <Send className="h-5 w-5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="surface-card p-5 text-center py-16 px-6">
              <Bot className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[var(--text-mid)] mb-4">Start a Realtime AI Session</h3>
              <div className="grid grid-cols-2 gap-4 max-w-md mx-auto mb-6">
                <div>
                  <label className="text-xs text-[var(--text-mid)] mb-1 block">Mode</label>
                  <Select value={mode} onValueChange={setMode}>
                    <SelectTrigger>
                      <SelectValue placeholder="Mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="voice">Voice Chat</SelectItem>
                      <SelectItem value="vision">Vision Analysis</SelectItem>
                      <SelectItem value="voice_vision">Voice + Vision</SelectItem>
                      <SelectItem value="meeting">Meeting Assistant</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-[var(--text-mid)] mb-1 block">Provider</label>
                  <Select value={provider} onValueChange={setProvider}>
                    <SelectTrigger>
                      <SelectValue placeholder="Provider" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gemini">Gemini Flash</SelectItem>
                      <SelectItem value="groq">Groq (Ultra-fast)</SelectItem>
                      <SelectItem value="claude">Claude</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-2">
                  <Input
                    placeholder="System Prompt (optional, e.g., You are a helpful coding assistant...)"
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                  />
                </div>
              </div>
              <Button
                size="lg"
                onClick={handleCreate}
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Mic className="h-4 w-4 mr-2" />
                )}
                Start Session
              </Button>
            </div>
          )}
        </div>

        {/* Session History */}
        <div className="md:col-span-4">
          <div className="surface-card p-5">
            <h3 className="text-lg font-semibold text-[var(--text-high)] flex items-center gap-2 mb-4">
              <History className="h-5 w-5" /> Sessions
            </h3>
            {isLoading ? <Skeleton className="h-72 rounded-lg" /> : !sessions?.length ? (
              <p className="text-[var(--text-mid)]">No sessions yet</p>
            ) : (
              sessions.map((s) => (
                <div key={s.id} className="surface-card p-4 mb-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-[var(--text-high)]">{s.title || 'Untitled'}</span>
                    <Badge variant={STATUS_VARIANTS[s.status] || 'default'}>{s.status}</Badge>
                  </div>
                  <div className="flex gap-1 mt-1">
                    <Badge variant="outline">{MODE_ICONS[s.mode] || s.mode}</Badge>
                    <Badge variant="outline">{s.provider}</Badge>
                    <Badge variant="outline">{s.total_turns} turns</Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
