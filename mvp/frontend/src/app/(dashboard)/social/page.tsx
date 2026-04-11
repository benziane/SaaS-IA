'use client';

import { useState } from 'react';
import {
  Share2, Plus, Trash2, Send, Clock, BarChart3, Unlink, Copy, Loader2,
} from 'lucide-react';

import { Badge } from '@/lib/design-hub/components/Badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import {
  useAccounts,
  useConnectAccount,
  useCreatePost,
  useDeletePost,
  useDisconnectAccount,
  usePostAnalytics,
  usePosts,
  usePublishPost,
} from '@/features/social-publisher/hooks/useSocialPublisher';
import type { SocialPost } from '@/features/social-publisher/types';

const PLATFORM_OPTIONS = [
  { id: 'twitter', label: 'Twitter / X', color: '#1DA1F2' },
  { id: 'linkedin', label: 'LinkedIn', color: '#0077B5' },
  { id: 'instagram', label: 'Instagram', color: '#E4405F' },
  { id: 'tiktok', label: 'TikTok', color: '#000000' },
  { id: 'facebook', label: 'Facebook', color: '#1877F2' },
];

const STATUS_VARIANT: Record<string, 'secondary' | 'default' | 'success' | 'destructive' | 'warning'> = {
  draft: 'secondary',
  scheduled: 'warning',
  publishing: 'default',
  published: 'success',
  failed: 'destructive',
};

type TabValue = 'compose' | 'scheduled' | 'published' | 'accounts';

export default function SocialPublisherPage() {
  const [activeTab, setActiveTab] = useState<TabValue>('compose');

  // Data hooks
  const { data: accounts, isLoading: accountsLoading } = useAccounts();
  const { data: postsData, isLoading: postsLoading } = usePosts({ limit: 50 });
  const connectMutation = useConnectAccount();
  const disconnectMutation = useDisconnectAccount();
  const createPostMutation = useCreatePost();
  const publishMutation = usePublishPost();
  const deleteMutation = useDeletePost();

  // Compose state
  const [content, setContent] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['twitter', 'linkedin']);
  const [hashtags, setHashtags] = useState('');
  const [scheduleDate, setScheduleDate] = useState('');

  // Connect account dialog
  const [connectOpen, setConnectOpen] = useState(false);
  const [connectPlatform, setConnectPlatform] = useState('twitter');
  const [connectToken, setConnectToken] = useState('');
  const [connectName, setConnectName] = useState('');

  // Analytics dialog
  const [analyticsPostId, setAnalyticsPostId] = useState<string | null>(null);
  const { data: analytics } = usePostAnalytics(analyticsPostId);

  const posts = postsData?.posts || [];
  const draftPosts = posts.filter((p) => p.status === 'draft');
  const scheduledPosts = posts.filter((p) => p.status === 'scheduled');
  const publishedPosts = posts.filter((p) => p.status === 'published' || p.status === 'failed');

  const handleCompose = () => {
    if (!content.trim() || selectedPlatforms.length === 0) return;
    const hashtagList = hashtags
      .split(/[,\s]+/)
      .map((h) => h.trim())
      .filter(Boolean);

    createPostMutation.mutate(
      {
        content,
        platforms: selectedPlatforms,
        schedule_at: scheduleDate || undefined,
        hashtags: hashtagList.length > 0 ? hashtagList : undefined,
      },
      {
        onSuccess: () => {
          setContent('');
          setHashtags('');
          setScheduleDate('');
        },
      }
    );
  };

  const handleConnect = () => {
    if (!connectToken.trim() || !connectName.trim()) return;
    connectMutation.mutate(
      {
        platform: connectPlatform as 'twitter' | 'linkedin' | 'instagram' | 'tiktok' | 'facebook',
        access_token: connectToken,
        account_name: connectName,
      },
      {
        onSuccess: () => {
          setConnectOpen(false);
          setConnectToken('');
          setConnectName('');
        },
      }
    );
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const renderPostCard = (post: SocialPost, showActions: boolean = true) => {
    const platformChips = post.platforms.map((p) => {
      const info = PLATFORM_OPTIONS.find((o) => o.id === p);
      return (
        <span
          key={p}
          className="inline-flex items-center rounded px-2 py-0.5 text-[0.7rem] font-semibold text-white"
          style={{ backgroundColor: info?.color }}
        >
          {info?.label || p}
        </span>
      );
    });

    return (
      <div key={post.id} className="surface-card p-5 mb-2">
        <div className="flex items-center justify-between mb-2">
          <div className="flex gap-1 flex-wrap">
            {platformChips}
          </div>
          <Badge variant={STATUS_VARIANT[post.status] || 'secondary'}>
            {post.status}
          </Badge>
        </div>
        <p className="text-sm whitespace-pre-wrap overflow-hidden text-ellipsis line-clamp-4 mb-2">
          {post.content}
        </p>
        {post.hashtags.length > 0 && (
          <div className="flex gap-1 flex-wrap mb-2">
            {post.hashtags.map((h) => (
              <Badge key={h} variant="outline">#{h}</Badge>
            ))}
          </div>
        )}
        <p className="text-xs text-[var(--text-low)]">
          {post.schedule_at
            ? `Scheduled: ${new Date(post.schedule_at).toLocaleString()}`
            : post.published_at
            ? `Published: ${new Date(post.published_at).toLocaleString()}`
            : `Created: ${new Date(post.created_at).toLocaleString()}`}
        </p>
        {showActions && (
          <div className="flex justify-end gap-1 pt-3 mt-3 border-t border-[var(--border)]">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={() => handleCopy(post.content)}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Copy content</TooltipContent>
              </Tooltip>
              {(post.status === 'draft' || post.status === 'scheduled') && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-[var(--accent)]"
                      onClick={() => publishMutation.mutate(post.id)}
                      disabled={publishMutation.isPending}
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Publish now</TooltipContent>
                </Tooltip>
              )}
              {post.status === 'published' && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setAnalyticsPostId(post.id)}
                    >
                      <BarChart3 className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>View analytics</TooltipContent>
                </Tooltip>
              )}
              {post.status !== 'published' && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-red-500 hover:text-red-600"
                      onClick={() => deleteMutation.mutate(post.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Delete</TooltipContent>
                </Tooltip>
              )}
            </TooltipProvider>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Share2 className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Social Publisher</h1>
          <p className="text-xs text-[var(--text-mid)]">Multi-platform social publishing</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)} className="mb-6">
        <TabsList>
          <TabsTrigger value="compose">Compose</TabsTrigger>
          <TabsTrigger value="scheduled">Scheduled ({scheduledPosts.length})</TabsTrigger>
          <TabsTrigger value="published">Published ({publishedPosts.length})</TabsTrigger>
          <TabsTrigger value="accounts">Accounts ({accounts?.length || 0})</TabsTrigger>
        </TabsList>

        {/* ---- Compose Tab ---- */}
        <TabsContent value="compose">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <div className="surface-card p-5">
                <h3 className="text-lg font-semibold mb-4">New Post</h3>
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">What do you want to share?</label>
                  <Textarea
                    rows={6}
                    placeholder="Write your post content here..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    maxLength={10000}
                  />
                  <p className="text-xs text-[var(--text-low)] mt-1">{content.length} / 10,000 characters</p>
                </div>

                <h4 className="text-sm font-semibold mb-2">Target Platforms</h4>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {PLATFORM_OPTIONS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border transition-colors cursor-pointer"
                      style={
                        selectedPlatforms.includes(p.id)
                          ? { backgroundColor: p.color, color: '#fff', borderColor: p.color }
                          : { borderColor: 'var(--border)', color: 'var(--text-mid)', backgroundColor: 'transparent' }
                      }
                      onClick={() => togglePlatform(p.id)}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Hashtags (comma separated)</label>
                    <Input
                      placeholder="AI, SaaS, innovation"
                      value={hashtags}
                      onChange={(e) => setHashtags(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Schedule (optional)</label>
                    <Input
                      type="datetime-local"
                      value={scheduleDate}
                      onChange={(e) => setScheduleDate(e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex gap-2 mt-6 justify-end">
                  <Button
                    variant="outline"
                    onClick={() => {
                      if (!scheduleDate) return;
                      handleCompose();
                    }}
                    disabled={!content.trim() || selectedPlatforms.length === 0 || !scheduleDate || createPostMutation.isPending}
                  >
                    <Clock className="h-4 w-4 mr-1" />
                    Schedule
                  </Button>
                  <Button
                    onClick={handleCompose}
                    disabled={!content.trim() || selectedPlatforms.length === 0 || createPostMutation.isPending}
                  >
                    {createPostMutation.isPending
                      ? <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      : <Send className="h-4 w-4 mr-1" />}
                    {scheduleDate ? 'Schedule Post' : 'Create Draft'}
                  </Button>
                </div>

                {createPostMutation.isError && (
                  <Alert variant="destructive" className="mt-4">
                    <AlertDescription>{createPostMutation.error?.message}</AlertDescription>
                  </Alert>
                )}
                {createPostMutation.isSuccess && (
                  <Alert variant="success" className="mt-4">
                    <AlertDescription>Post created successfully!</AlertDescription>
                  </Alert>
                )}
              </div>
            </div>

            {/* Draft Posts sidebar */}
            <div>
              <div className="surface-card p-5">
                <h3 className="text-lg font-semibold mb-4">Drafts ({draftPosts.length})</h3>
                {postsLoading ? (
                  <Skeleton className="h-[200px] w-full" />
                ) : draftPosts.length === 0 ? (
                  <p className="text-[var(--text-mid)] text-center py-8">
                    No draft posts yet
                  </p>
                ) : (
                  draftPosts.map((post) => renderPostCard(post))
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ---- Scheduled Tab ---- */}
        <TabsContent value="scheduled">
          <div className="surface-card p-5">
            <h3 className="text-lg font-semibold mb-4">Scheduled Posts</h3>
            {postsLoading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : scheduledPosts.length === 0 ? (
              <div className="text-center py-12">
                <Clock className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                <p className="text-[var(--text-mid)]">No scheduled posts</p>
                <p className="text-sm text-[var(--text-mid)]">
                  Schedule posts from the Compose tab
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {scheduledPosts.map((post) => (
                  <div key={post.id}>
                    {renderPostCard(post)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        {/* ---- Published Tab ---- */}
        <TabsContent value="published">
          <div className="surface-card p-5">
            <h3 className="text-lg font-semibold mb-4">Published Posts</h3>
            {postsLoading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : publishedPosts.length === 0 ? (
              <div className="text-center py-12">
                <Share2 className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                <p className="text-[var(--text-mid)]">No published posts yet</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {publishedPosts.map((post) => (
                  <div key={post.id}>
                    {renderPostCard(post)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        {/* ---- Accounts Tab ---- */}
        <TabsContent value="accounts">
          <div className="surface-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Connected Accounts</h3>
              <Button size="sm" onClick={() => setConnectOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Connect Account
              </Button>
            </div>
            {accountsLoading ? (
              <Skeleton className="h-[200px] w-full" />
            ) : !accounts?.length ? (
              <div className="text-center py-12">
                <Unlink className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                <p className="text-[var(--text-mid)]">No accounts connected</p>
                <Button variant="ghost" size="sm" onClick={() => setConnectOpen(true)} className="mt-2">
                  Connect your first account
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {accounts.map((account) => {
                  const platformInfo = PLATFORM_OPTIONS.find((p) => p.id === account.platform);
                  return (
                    <div key={account.id} className="surface-card p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <span
                            className="inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold text-white mb-2"
                            style={{ backgroundColor: platformInfo?.color }}
                          >
                            {platformInfo?.label || account.platform}
                          </span>
                          <p className="text-sm font-semibold">{account.account_name}</p>
                          <p className="text-xs text-[var(--text-low)]">
                            Connected {new Date(account.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <Badge variant={account.is_active ? 'success' : 'secondary'}>
                          {account.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      {account.is_active && (
                        <div className="flex justify-end pt-3 mt-3 border-t border-[var(--border)]">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => disconnectMutation.mutate(account.id)}
                            disabled={disconnectMutation.isPending}
                          >
                            <Unlink className="h-4 w-4 mr-1" />
                            Disconnect
                          </Button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* ---- Connect Account Dialog ---- */}
      <Dialog open={connectOpen} onOpenChange={setConnectOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Connect Social Account</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Platform</label>
              <Select value={connectPlatform} onValueChange={setConnectPlatform}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PLATFORM_OPTIONS.map((p) => (
                    <SelectItem key={p.id} value={p.id}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Account Name / Handle</label>
              <Input
                placeholder="@myaccount"
                value={connectName}
                onChange={(e) => setConnectName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Access Token</label>
              <Input
                type="password"
                placeholder="OAuth access token"
                value={connectToken}
                onChange={(e) => setConnectToken(e.target.value)}
              />
              <p className="text-xs text-[var(--text-low)] mt-1">Your token is hashed before storage and never displayed again</p>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="ghost" onClick={() => setConnectOpen(false)}>Cancel</Button>
            <Button
              onClick={handleConnect}
              disabled={!connectName.trim() || !connectToken.trim() || connectMutation.isPending}
            >
              {connectMutation.isPending
                ? <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                : <Plus className="h-4 w-4 mr-1" />}
              Connect
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Analytics Dialog ---- */}
      <Dialog open={!!analyticsPostId} onOpenChange={() => setAnalyticsPostId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Post Analytics</DialogTitle>
          </DialogHeader>
          {!analytics ? (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-[var(--accent)]" />
            </div>
          ) : (
            analytics.map((a) => {
              const platformInfo = PLATFORM_OPTIONS.find((p) => p.id === a.platform);
              return (
                <div key={a.platform} className="surface-card p-4 mb-3">
                  <span
                    className="inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold text-white mb-3"
                    style={{ backgroundColor: platformInfo?.color }}
                  >
                    {platformInfo?.label || a.platform}
                  </span>
                  <div className="grid grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-lg font-semibold">{a.impressions.toLocaleString()}</p>
                      <p className="text-xs text-[var(--text-low)]">Impressions</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold">{a.engagements.toLocaleString()}</p>
                      <p className="text-xs text-[var(--text-low)]">Engagements</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold">{a.clicks.toLocaleString()}</p>
                      <p className="text-xs text-[var(--text-low)]">Clicks</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold">{a.shares.toLocaleString()}</p>
                      <p className="text-xs text-[var(--text-low)]">Shares</p>
                    </div>
                  </div>
                </div>
              );
            })
          )}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAnalyticsPostId(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Global mutation error/success feedback */}
      {publishMutation.isError && (
        <Alert variant="destructive" className="fixed bottom-4 right-4 z-[9999] w-auto">
          <AlertDescription>Publish failed: {publishMutation.error?.message}</AlertDescription>
        </Alert>
      )}
      {publishMutation.isSuccess && (
        <Alert variant="success" className="fixed bottom-4 right-4 z-[9999] w-auto">
          <AlertDescription>Post published successfully!</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
