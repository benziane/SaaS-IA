'use client';

import { useState } from 'react';
import {
  Bot, Plus, Trash2, Pencil, Copy, Code, BarChart3, MessageSquare, Globe, Loader2,
} from 'lucide-react';

import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Switch } from '@/lib/design-hub/components/Switch';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import {
  useChatbots,
  useCreateChatbot,
  useDeleteChatbot,
  usePublishChatbot,
  useUnpublishChatbot,
  useChatbotAnalytics,
  useEmbedCode,
} from '@/features/ai-chatbot-builder/hooks/useChatbotBuilder';
import type { Chatbot } from '@/features/ai-chatbot-builder/types';

const MODEL_OPTIONS = ['gemini', 'claude', 'groq'];
const PERSONALITY_OPTIONS = ['professional', 'friendly', 'casual', 'technical', 'empathetic', 'concise'];

export default function ChatbotsPage() {
  const { data: chatbots, isLoading } = useChatbots();
  const createMutation = useCreateChatbot();
  const deleteMutation = useDeleteChatbot();
  const publishMutation = usePublishChatbot();
  const unpublishMutation = useUnpublishChatbot();

  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful assistant.');
  const [model, setModel] = useState('gemini');
  const [personality, setPersonality] = useState('professional');
  const [welcomeMessage, setWelcomeMessage] = useState('');

  const [detailBot, setDetailBot] = useState<Chatbot | null>(null);
  const [embedOpen, setEmbedOpen] = useState(false);
  const [embedBotId, setEmbedBotId] = useState<string | null>(null);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [analyticsBotId, setAnalyticsBotId] = useState<string | null>(null);

  const { data: embedCode } = useEmbedCode(embedOpen ? embedBotId : null);
  const { data: analytics } = useChatbotAnalytics(analyticsOpen ? analyticsBotId : null);

  const handleCreate = () => {
    if (!name.trim() || !systemPrompt.trim()) return;
    createMutation.mutate(
      {
        name,
        description: description || undefined,
        system_prompt: systemPrompt,
        model,
        personality,
        welcome_message: welcomeMessage || undefined,
      },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setName('');
          setDescription('');
          setSystemPrompt('You are a helpful assistant.');
          setModel('gemini');
          setPersonality('professional');
          setWelcomeMessage('');
        },
      }
    );
  };

  const handleTogglePublish = (bot: Chatbot) => {
    if (bot.is_published) {
      unpublishMutation.mutate(bot.id);
    } else {
      publishMutation.mutate(bot.id);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-high)] flex items-center gap-2">
            <Bot className="h-8 w-8 text-[var(--accent)]" /> Chatbot Builder
          </h1>
          <p className="text-sm text-[var(--text-mid)]">
            Create AI chatbots with custom knowledge bases, deploy on web widgets and messaging channels
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> New Chatbot
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-56 rounded-lg" />
          ))}
        </div>
      ) : !chatbots?.length ? (
        <Card>
          <CardContent className="text-center py-16 px-6">
            <Bot className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-[var(--text-mid)]">No chatbots yet</h3>
            <p className="text-sm text-[var(--text-mid)] mt-2 mb-4">
              Build your first AI chatbot with custom instructions, knowledge base integration, and multi-channel deployment
            </p>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-2" /> Create your first chatbot
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {chatbots.map((bot) => (
            <Card
              key={bot.id}
              className="flex flex-col h-full border border-[var(--border)] hover:border-[var(--accent)] transition-colors"
            >
              <CardContent className="flex-1 p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-[var(--text-high)] truncate max-w-[70%]">
                    {bot.name}
                  </h3>
                  <div className="flex items-center gap-1">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div>
                            <Switch
                              checked={bot.is_published}
                              onCheckedChange={() => handleTogglePublish(bot)}
                              disabled={publishMutation.isPending || unpublishMutation.isPending}
                            />
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>{bot.is_published ? 'Published' : 'Draft'}</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>

                {bot.description && (
                  <p className="text-sm text-[var(--text-mid)] mb-3 line-clamp-2">
                    {bot.description}
                  </p>
                )}

                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="outline" className="text-[var(--accent)]">{bot.model}</Badge>
                  <Badge variant="outline">{bot.personality}</Badge>
                  {bot.is_published && (
                    <Badge variant="success">
                      <Globe className="h-3 w-3 mr-1" /> Published
                    </Badge>
                  )}
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1">
                    <MessageSquare className="h-3.5 w-3.5 text-[var(--text-mid)]" />
                    <span className="text-xs text-[var(--text-mid)]">
                      {bot.conversations_count} conversations
                    </span>
                  </div>
                  {bot.channels.length > 0 && (
                    <span className="text-xs text-[var(--text-mid)]">
                      {bot.channels.length} channel{bot.channels.length > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </CardContent>

              <CardFooter className="justify-end gap-1 px-4 pb-3 pt-0">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        title="Analytics"
                        className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                        onClick={() => {
                          setAnalyticsBotId(bot.id);
                          setAnalyticsOpen(true);
                        }}
                      >
                        <BarChart3 className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Analytics</TooltipContent>
                  </Tooltip>
                  {bot.is_published && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          title="Embed Code"
                          className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                          onClick={() => {
                            setEmbedBotId(bot.id);
                            setEmbedOpen(true);
                          }}
                        >
                          <Code className="h-4 w-4 text-[var(--text-mid)]" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Embed Code</TooltipContent>
                    </Tooltip>
                  )}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        title="Edit"
                        className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                        onClick={() => setDetailBot(bot)}
                      >
                        <Pencil className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Edit</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        title="Delete"
                        className="p-1.5 rounded hover:bg-red-100 text-red-500"
                        onClick={() => deleteMutation.mutate(bot.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Delete</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Chatbot Dialog */}
      <Dialog open={createOpen} onOpenChange={(v) => { if (!v) setCreateOpen(false); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Chatbot</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <Input
              placeholder="Chatbot Name (e.g., Customer Support Bot)"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Input
              placeholder="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <Textarea
              rows={5}
              placeholder="System Prompt - Instructions for the AI. Define its role, knowledge boundaries, and response style."
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
            />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-[var(--text-mid)] mb-1 block">AI Model</label>
                <Select value={model} onValueChange={setModel}>
                  <SelectTrigger>
                    <SelectValue placeholder="AI Model" />
                  </SelectTrigger>
                  <SelectContent>
                    {MODEL_OPTIONS.map((m) => (
                      <SelectItem key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs text-[var(--text-mid)] mb-1 block">Personality</label>
                <Select value={personality} onValueChange={setPersonality}>
                  <SelectTrigger>
                    <SelectValue placeholder="Personality" />
                  </SelectTrigger>
                  <SelectContent>
                    {PERSONALITY_OPTIONS.map((p) => (
                      <SelectItem key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Input
              placeholder="Welcome Message (optional) - e.g., Hello! How can I help you today?"
              value={welcomeMessage}
              onChange={(e) => setWelcomeMessage(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreate}
              disabled={!name.trim() || !systemPrompt.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Bot className="h-4 w-4 mr-2" />
              )}
              Create Chatbot
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Chatbot Detail / Edit Dialog */}
      <Dialog open={!!detailBot} onOpenChange={(v) => { if (!v) setDetailBot(null); }}>
        {detailBot && (
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-[var(--accent)]" />
                {detailBot.name}
                {detailBot.is_published && <Badge variant="success">Published</Badge>}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 border-t border-[var(--border)] pt-4">
              <div>
                <p className="text-xs text-[var(--text-mid)] mb-1">System Prompt</p>
                <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap bg-[var(--bg-surface)] p-3 rounded">
                  {detailBot.system_prompt}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Model</span>
                  <p className="text-sm text-[var(--text-high)]">{detailBot.model}</p>
                </div>
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Personality</span>
                  <p className="text-sm text-[var(--text-high)]">{detailBot.personality}</p>
                </div>
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Conversations</span>
                  <p className="text-sm text-[var(--text-high)]">{detailBot.conversations_count}</p>
                </div>
              </div>

              {detailBot.welcome_message && (
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Welcome Message</span>
                  <p className="text-sm text-[var(--text-high)]">{detailBot.welcome_message}</p>
                </div>
              )}

              {detailBot.embed_token && (
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Embed Token</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono bg-[var(--bg-surface)] px-2 py-1 rounded">
                      {detailBot.embed_token}
                    </span>
                    <button
                      type="button"
                      title="Copy"
                      className="p-1 rounded hover:bg-[var(--bg-hover)]"
                      onClick={() => handleCopy(detailBot.embed_token!)}
                    >
                      <Copy className="h-4 w-4 text-[var(--text-mid)]" />
                    </button>
                  </div>
                </div>
              )}

              {detailBot.channels.length > 0 && (
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Channels</span>
                  <div className="flex gap-1 mt-1">
                    {detailBot.channels.map((ch, i) => (
                      <Badge key={i} variant={ch.is_active ? 'success' : 'default'}>{ch.type}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDetailBot(null)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        )}
      </Dialog>

      {/* Embed Code Dialog */}
      <Dialog open={embedOpen} onOpenChange={(v) => { if (!v) setEmbedOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Code className="h-5 w-5 text-[var(--accent)]" /> Embed Code
            </DialogTitle>
          </DialogHeader>
          {embedCode ? (
            <div>
              <p className="text-sm text-[var(--text-mid)] mb-2">
                Add this snippet to your website to embed the chatbot widget:
              </p>
              <div className="font-mono text-sm bg-gray-900 text-gray-100 p-4 rounded whitespace-pre-wrap break-all">
                {embedCode.html_snippet}
              </div>
              <Button variant="outline" className="mt-2" onClick={() => handleCopy(embedCode.html_snippet)}>
                <Copy className="h-4 w-4 mr-2" /> Copy Snippet
              </Button>
            </div>
          ) : (
            <div className="flex justify-center py-6">
              <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEmbedOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Analytics Dialog */}
      <Dialog open={analyticsOpen} onOpenChange={(v) => { if (!v) setAnalyticsOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-[var(--accent)]" /> Chatbot Analytics
            </DialogTitle>
          </DialogHeader>
          {analytics ? (
            <div>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <Card className="border border-[var(--border)]">
                  <CardContent className="text-center p-4">
                    <p className="text-3xl font-bold text-[var(--text-high)]">{analytics.total_conversations}</p>
                    <span className="text-xs text-[var(--text-mid)]">Conversations</span>
                  </CardContent>
                </Card>
                <Card className="border border-[var(--border)]">
                  <CardContent className="text-center p-4">
                    <p className="text-3xl font-bold text-[var(--text-high)]">{analytics.total_messages}</p>
                    <span className="text-xs text-[var(--text-mid)]">Messages</span>
                  </CardContent>
                </Card>
                <Card className="border border-[var(--border)]">
                  <CardContent className="text-center p-4">
                    <p className="text-3xl font-bold text-[var(--text-high)]">{analytics.avg_messages_per_conversation}</p>
                    <span className="text-xs text-[var(--text-mid)]">Avg Messages/Conv</span>
                  </CardContent>
                </Card>
                <Card className="border border-[var(--border)]">
                  <CardContent className="text-center p-4">
                    <p className="text-3xl font-bold text-[var(--text-high)]">
                      {analytics.satisfaction_score !== null ? analytics.satisfaction_score : '--'}
                    </p>
                    <span className="text-xs text-[var(--text-mid)]">Satisfaction</span>
                  </CardContent>
                </Card>
              </div>

              {analytics.top_questions.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-[var(--text-high)] mb-2">Top Questions</p>
                  {analytics.top_questions.map((q, i) => (
                    <div key={i} className="flex justify-between py-1 border-b border-[var(--border)]">
                      <span className="text-sm text-[var(--text-high)] truncate max-w-[80%]">{q.question}</span>
                      <Badge>{q.count}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setAnalyticsOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {createMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{createMutation.error?.message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
