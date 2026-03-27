'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Plus, FileText, CheckCircle2, CheckCircle, ChevronLeft, ChevronRight,
  Circle, CloudOff, Cloud, Code, MessageSquare, Trash2, ChevronDown, ChevronUp,
  Bold, Italic, Underline, List, History, Reply, RotateCcw, Send,
  RefreshCw, Type, Wifi, Users,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Avatar, AvatarFallback } from '@/lib/design-hub/components/Avatar';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CollabUser {
  id: string;
  name: string;
  color: string;
  avatar?: string;
  cursorLine: number;
  cursorChar: number;
  isOnline: boolean;
}

interface WorkspaceDocument {
  id: string;
  title: string;
  lastModified: string;
  contributors: string[];
  isActive: boolean;
  wordCount: number;
}

interface CommentReply {
  id: string;
  authorId: string;
  authorName: string;
  content: string;
  timestamp: string;
}

interface DocComment {
  id: string;
  authorId: string;
  authorName: string;
  authorColor: string;
  content: string;
  timestamp: string;
  resolved: boolean;
  selection: string;
  replies: CommentReply[];
}

interface VersionEntry {
  id: string;
  authorName: string;
  authorColor: string;
  timestamp: string;
  summary: string;
  additions: number;
  deletions: number;
}

type ConnectionStatus = 'connected' | 'reconnecting' | 'offline';
type HeadingLevel = 'h1' | 'h2' | 'h3';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MOCK_USERS: CollabUser[] = [
  { id: 'u1', name: 'Alice Martin', color: '#2196F3', cursorLine: 12, cursorChar: 34, isOnline: true },
  { id: 'u2', name: 'Bob Dupont', color: '#4CAF50', cursorLine: 45, cursorChar: 8, isOnline: true },
  { id: 'u3', name: 'Claire Bernard', color: '#FF9800', cursorLine: 3, cursorChar: 22, isOnline: true },
];

const MOCK_DOCUMENTS: WorkspaceDocument[] = [
  { id: 'doc-1', title: 'Product Requirements - Q1 2026', lastModified: '2026-03-25T14:30:00Z', contributors: ['Alice Martin', 'Bob Dupont'], isActive: true, wordCount: 2340 },
  { id: 'doc-2', title: 'Technical Architecture Notes', lastModified: '2026-03-24T10:15:00Z', contributors: ['Claire Bernard', 'Alice Martin'], isActive: false, wordCount: 1856 },
  { id: 'doc-3', title: 'Sprint Retrospective - Week 12', lastModified: '2026-03-23T16:45:00Z', contributors: ['Bob Dupont'], isActive: false, wordCount: 620 },
  { id: 'doc-4', title: 'API Integration Guide', lastModified: '2026-03-22T09:00:00Z', contributors: ['Alice Martin', 'Claire Bernard', 'Bob Dupont'], isActive: false, wordCount: 4120 },
  { id: 'doc-5', title: 'User Research Findings', lastModified: '2026-03-20T11:30:00Z', contributors: ['Claire Bernard'], isActive: false, wordCount: 1450 },
];

const MOCK_COMMENTS: DocComment[] = [
  {
    id: 'c1', authorId: 'u2', authorName: 'Bob Dupont', authorColor: '#4CAF50',
    content: 'Should we add more detail on the authentication flow here? The current description is a bit vague for the backend team.',
    timestamp: '2026-03-25T13:15:00Z', resolved: false, selection: 'authentication requirements',
    replies: [{ id: 'r1', authorId: 'u1', authorName: 'Alice Martin', content: 'Good point. I\'ll add a sequence diagram in the next revision.', timestamp: '2026-03-25T13:22:00Z' }],
  },
  {
    id: 'c2', authorId: 'u3', authorName: 'Claire Bernard', authorColor: '#FF9800',
    content: 'This section needs to be reviewed by the security team before we finalize.',
    timestamp: '2026-03-25T12:00:00Z', resolved: false, selection: 'data encryption policy', replies: [],
  },
  {
    id: 'c3', authorId: 'u1', authorName: 'Alice Martin', authorColor: '#2196F3',
    content: 'Updated the performance targets based on last week\'s benchmarks.',
    timestamp: '2026-03-24T16:30:00Z', resolved: true, selection: 'performance requirements',
    replies: [
      { id: 'r2', authorId: 'u2', authorName: 'Bob Dupont', content: 'Looks good. The new numbers align with our SLA.', timestamp: '2026-03-24T16:45:00Z' },
      { id: 'r3', authorId: 'u3', authorName: 'Claire Bernard', content: 'Confirmed. Marking as resolved.', timestamp: '2026-03-24T17:00:00Z' },
    ],
  },
];

const MOCK_VERSIONS: VersionEntry[] = [
  { id: 'v6', authorName: 'Alice Martin', authorColor: '#2196F3', timestamp: '2026-03-25T14:30:00Z', summary: 'Updated authentication section with OAuth2 flow details', additions: 45, deletions: 12 },
  { id: 'v5', authorName: 'Bob Dupont', authorColor: '#4CAF50', timestamp: '2026-03-25T11:00:00Z', summary: 'Added performance benchmarks table', additions: 28, deletions: 3 },
  { id: 'v4', authorName: 'Claire Bernard', authorColor: '#FF9800', timestamp: '2026-03-24T16:20:00Z', summary: 'Restructured API endpoints section', additions: 67, deletions: 42 },
  { id: 'v3', authorName: 'Alice Martin', authorColor: '#2196F3', timestamp: '2026-03-24T10:15:00Z', summary: 'Added data model diagrams and schema descriptions', additions: 112, deletions: 0 },
  { id: 'v2', authorName: 'Bob Dupont', authorColor: '#4CAF50', timestamp: '2026-03-23T14:00:00Z', summary: 'Initial draft of technical requirements', additions: 230, deletions: 0 },
  { id: 'v1', authorName: 'Alice Martin', authorColor: '#2196F3', timestamp: '2026-03-23T09:00:00Z', summary: 'Created document with project overview', additions: 85, deletions: 0 },
];

const INITIAL_CONTENT = `<h1>Product Requirements - Q1 2026</h1>
<p>This document outlines the core product requirements for the Q1 2026 release cycle. All stakeholders should review and provide feedback by March 28th.</p>
<h2>1. Overview</h2>
<p>The platform will introduce real-time collaborative editing capabilities, enabling teams to work simultaneously on documents, specifications, and reports. This feature targets enterprise customers who need seamless coordination across distributed teams.</p>
<h2>2. Authentication Requirements</h2>
<p>Users must authenticate via SSO (SAML 2.0 or OAuth 2.0). Multi-factor authentication is required for all admin-level operations. Session tokens expire after 8 hours of inactivity.</p>
<h2>3. Data Encryption Policy</h2>
<p>All data at rest must be encrypted using AES-256. Data in transit uses TLS 1.3. Encryption keys are managed through the platform's key management service with automatic rotation every 90 days.</p>
<h2>4. Performance Requirements</h2>
<p>The collaborative editor must support at least 50 concurrent users per document with latency under 100ms for character-level operations. Document loading time should not exceed 2 seconds for documents up to 100 pages.</p>
<ul>
<li>P99 latency for sync operations: &lt; 150ms</li>
<li>Document save reliability: 99.99%</li>
<li>Conflict resolution accuracy: 100% (CRDT-based)</li>
</ul>
<h2>5. API Integration</h2>
<p>The REST API must expose endpoints for document CRUD, real-time presence, comment threads, and version history. WebSocket connections handle live updates. All endpoints require JWT authentication.</p>
<h3>5.1 Endpoints</h3>
<p>Detailed endpoint specifications will follow in the API Integration Guide (separate document).</p>
<h3>5.2 Rate Limiting</h3>
<p>Standard tier: 100 requests/minute. Enterprise tier: 1000 requests/minute. WebSocket connections are not rate-limited but are throttled at 60 messages/second per client.</p>`;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatFullTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function getInitials(name: string): string {
  return name.split(' ').map((p) => p[0]).join('').toUpperCase().slice(0, 2);
}

function countWords(html: string): number {
  const text = html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  if (!text) return 0;
  return text.split(' ').length;
}

function countChars(html: string): number {
  return html.replace(/<[^>]*>/g, '').length;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function DocumentSidebar({
  documents, selectedId, onSelect, onCreateNew, collapsed, onToggle,
}: {
  documents: WorkspaceDocument[];
  selectedId: string;
  onSelect: (id: string) => void;
  onCreateNew: () => void;
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      className="flex flex-col bg-[var(--bg-surface)] overflow-hidden transition-all duration-200"
      style={{ width: collapsed ? 48 : 280, minWidth: collapsed ? 48 : 280, borderRight: '1px solid var(--border)' }}
    >
      <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} p-3 min-h-[56px]`}>
        {!collapsed && (
          <span className="text-[0.7rem] font-bold uppercase tracking-wider text-[var(--text-low)]">Documents</span>
        )}
        <button type="button" onClick={onToggle} className="p-1 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="px-3 pb-2">
            <Button variant="outline" size="sm" className="w-full justify-start" onClick={onCreateNew}>
              <Plus className="h-4 w-4 mr-2" /> New Document
            </Button>
          </div>

          <Separator />

          <div className="flex-1 overflow-auto py-1">
            {documents.map((doc) => (
              <button
                key={doc.id}
                type="button"
                onClick={() => onSelect(doc.id)}
                className={`w-full text-left mx-1 rounded px-3 py-2 mb-0.5 flex items-start gap-2 transition-colors ${doc.id === selectedId ? 'bg-[var(--bg-elevated)]' : 'hover:bg-[var(--bg-elevated)]'}`}
              >
                <div className="relative mt-0.5">
                  <FileText className={`h-4 w-4 ${doc.id === selectedId ? 'text-[var(--accent)]' : 'text-[var(--text-low)]'}`} />
                  {doc.isActive && <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-500 border border-[var(--bg-surface)]" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-[0.82rem] truncate ${doc.id === selectedId ? 'font-semibold text-[var(--text-high)]' : 'text-[var(--text-mid)]'}`}>{doc.title}</p>
                  <p className="text-xs text-[var(--text-low)] truncate">{formatTimestamp(doc.lastModified)}</p>
                </div>
              </button>
            ))}
          </div>

          <Separator />
          <div className="p-3">
            <span className="text-xs text-[var(--text-low)]">{documents.length} documents</span>
          </div>
        </>
      )}
    </div>
  );
}

function EditorToolbar({
  onCommand, activeFormats,
}: {
  onCommand: (cmd: string, value?: string) => void;
  activeFormats: Set<string>;
}) {
  const [headingOpen, setHeadingOpen] = useState(false);

  const handleHeading = (level: HeadingLevel) => {
    onCommand('formatBlock', `<${level}>`);
    setHeadingOpen(false);
  };

  return (
    <div className="flex items-center gap-1 px-2 py-1 border border-[var(--border)] border-b-0 rounded-t-lg flex-wrap bg-[var(--bg-surface)]">
      <div className="flex">
        <button type="button" onClick={() => onCommand('bold')} className={`p-1.5 rounded transition-colors ${activeFormats.has('bold') ? 'bg-[var(--bg-elevated)] text-[var(--text-high)]' : 'text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]'}`} aria-label="Bold">
          <Bold className="h-4 w-4" />
        </button>
        <button type="button" onClick={() => onCommand('italic')} className={`p-1.5 rounded transition-colors ${activeFormats.has('italic') ? 'bg-[var(--bg-elevated)] text-[var(--text-high)]' : 'text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]'}`} aria-label="Italic">
          <Italic className="h-4 w-4" />
        </button>
        <button type="button" onClick={() => onCommand('underline')} className={`p-1.5 rounded transition-colors ${activeFormats.has('underline') ? 'bg-[var(--bg-elevated)] text-[var(--text-high)]' : 'text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]'}`} aria-label="Underline">
          <Underline className="h-4 w-4" />
        </button>
      </div>

      <Separator orientation="vertical" className="h-5 mx-1" />

      <div className="relative">
        <Tooltip>
          <TooltipTrigger asChild>
            <button type="button" onClick={() => setHeadingOpen(!headingOpen)} className="p-1.5 text-[var(--text-mid)] hover:bg-[var(--bg-elevated)] rounded transition-colors" aria-label="Heading">
              <Type className="h-4 w-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent>Heading</TooltipContent>
        </Tooltip>
        {headingOpen && (
          <div className="absolute top-full left-0 mt-1 z-50 bg-[var(--bg-surface)] border border-[var(--border)] rounded-md shadow-lg py-1 min-w-[140px]">
            <button type="button" onClick={() => handleHeading('h1')} className="w-full text-left px-3 py-1.5 hover:bg-[var(--bg-elevated)] text-lg font-bold text-[var(--text-high)]">Heading 1</button>
            <button type="button" onClick={() => handleHeading('h2')} className="w-full text-left px-3 py-1.5 hover:bg-[var(--bg-elevated)] text-base font-semibold text-[var(--text-high)]">Heading 2</button>
            <button type="button" onClick={() => handleHeading('h3')} className="w-full text-left px-3 py-1.5 hover:bg-[var(--bg-elevated)] text-sm font-semibold text-[var(--text-high)]">Heading 3</button>
            <Separator className="my-1" />
            <button type="button" onClick={() => { onCommand('formatBlock', '<p>'); setHeadingOpen(false); }} className="w-full text-left px-3 py-1.5 hover:bg-[var(--bg-elevated)] text-sm text-[var(--text-mid)]">Normal text</button>
          </div>
        )}
      </div>

      <Tooltip>
        <TooltipTrigger asChild>
          <button type="button" onClick={() => onCommand('insertUnorderedList')} className="p-1.5 text-[var(--text-mid)] hover:bg-[var(--bg-elevated)] rounded transition-colors" aria-label="Bullet List">
            <List className="h-4 w-4" />
          </button>
        </TooltipTrigger>
        <TooltipContent>Bullet List</TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <button type="button" onClick={() => onCommand('formatBlock', '<pre>')} className="p-1.5 text-[var(--text-mid)] hover:bg-[var(--bg-elevated)] rounded transition-colors" aria-label="Code Block">
            <Code className="h-4 w-4" />
          </button>
        </TooltipTrigger>
        <TooltipContent>Code Block</TooltipContent>
      </Tooltip>
    </div>
  );
}

function PresenceBar({ users }: { users: CollabUser[] }) {
  const onlineUsers = users.filter((u) => u.isOnline);
  return (
    <div className="flex items-center gap-3">
      <Badge variant="outline" className="flex items-center gap-1.5 font-medium">
        <Wifi className="h-3.5 w-3.5 text-green-400" />
        {onlineUsers.length} user{onlineUsers.length !== 1 ? 's' : ''} online
      </Badge>
      <div className="flex -space-x-2">
        {onlineUsers.slice(0, 5).map((u) => (
          <Tooltip key={u.id}>
            <TooltipTrigger asChild>
              <Avatar className="w-[30px] h-[30px] border-2 border-[var(--bg-surface)] cursor-pointer">
                <AvatarFallback style={{ backgroundColor: u.color }} className="text-[0.75rem] text-white font-semibold">
                  {getInitials(u.name)}
                </AvatarFallback>
              </Avatar>
            </TooltipTrigger>
            <TooltipContent>{u.name} - Line {u.cursorLine}, Col {u.cursorChar}</TooltipContent>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}

function CommentsPanel({
  comments, onResolve, onReply, onDelete, onAdd,
}: {
  comments: DocComment[];
  onResolve: (id: string) => void;
  onReply: (commentId: string, text: string) => void;
  onDelete: (id: string) => void;
  onAdd: (content: string) => void;
}) {
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyText, setReplyText] = useState('');
  const [newComment, setNewComment] = useState('');
  const [showResolved, setShowResolved] = useState(false);

  const openComments = comments.filter((c) => !c.resolved);
  const resolvedComments = comments.filter((c) => c.resolved);

  const handleReply = (commentId: string) => {
    if (!replyText.trim()) return;
    onReply(commentId, replyText.trim());
    setReplyText('');
    setReplyingTo(null);
  };

  const handleAdd = () => {
    if (!newComment.trim()) return;
    onAdd(newComment.trim());
    setNewComment('');
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-[var(--border)]">
        <span className="text-[0.7rem] font-bold uppercase tracking-wider text-[var(--text-low)]">
          Comments ({openComments.length})
        </span>
      </div>

      <div className="p-3 border-b border-[var(--border)]">
        <Textarea
          rows={2}
          placeholder="Add a comment..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          className="mb-2"
        />
        <Button size="sm" disabled={!newComment.trim()} onClick={handleAdd}>
          <Send className="h-3.5 w-3.5 mr-1.5" /> Comment
        </Button>
      </div>

      <div className="flex-1 overflow-auto">
        {openComments.length === 0 && (
          <div className="p-6 text-center">
            <MessageSquare className="h-10 w-10 text-[var(--text-low)] mx-auto mb-2" />
            <p className="text-sm text-[var(--text-mid)]">No open comments</p>
          </div>
        )}

        {openComments.map((comment) => (
          <div key={comment.id} className="p-3 border-b border-[var(--border)]">
            <Badge variant="outline" className="mb-2 text-[0.7rem] border-dashed">{comment.selection}</Badge>

            <div className="flex items-center gap-2 mb-1">
              <Avatar className="w-6 h-6">
                <AvatarFallback style={{ backgroundColor: comment.authorColor }} className="text-[0.65rem] text-white">{getInitials(comment.authorName)}</AvatarFallback>
              </Avatar>
              <span className="text-[0.82rem] font-semibold text-[var(--text-high)]">{comment.authorName}</span>
              <span className="text-xs text-[var(--text-low)]">{formatTimestamp(comment.timestamp)}</span>
            </div>

            <p className="text-sm text-[var(--text-high)] ml-8 mb-2 leading-relaxed">{comment.content}</p>

            {comment.replies.length > 0 && (
              <div className="ml-8 pl-3 border-l-2 border-[var(--border)] mb-2">
                {comment.replies.map((reply) => (
                  <div key={reply.id} className="mb-2">
                    <div className="flex items-center gap-1 mb-0.5">
                      <span className="text-xs font-semibold text-[var(--text-high)]">{reply.authorName}</span>
                      <span className="text-xs text-[var(--text-low)]">{formatTimestamp(reply.timestamp)}</span>
                    </div>
                    <p className="text-[0.8rem] text-[var(--text-mid)]">{reply.content}</p>
                  </div>
                ))}
              </div>
            )}

            {replyingTo === comment.id ? (
              <div className="ml-8 mt-1">
                <Input
                  placeholder="Reply..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleReply(comment.id); } }}
                  className="mb-1"
                />
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => handleReply(comment.id)} disabled={!replyText.trim()}>Reply</Button>
                  <Button size="sm" variant="ghost" onClick={() => { setReplyingTo(null); setReplyText(''); }}>Cancel</Button>
                </div>
              </div>
            ) : (
              <div className="flex gap-1 ml-8">
                <Button size="sm" variant="ghost" onClick={() => setReplyingTo(comment.id)} className="text-[0.75rem]">
                  <Reply className="h-3.5 w-3.5 mr-1" /> Reply
                </Button>
                <Button size="sm" variant="ghost" onClick={() => onResolve(comment.id)} className="text-[0.75rem]">
                  <CheckCircle className="h-3.5 w-3.5 mr-1" /> Resolve
                </Button>
                <button type="button" onClick={() => onDelete(comment.id)} className="ml-auto p-1 text-[var(--text-low)] hover:text-red-400 transition-colors" aria-label="Delete comment">
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            )}
          </div>
        ))}

        {resolvedComments.length > 0 && (
          <>
            <button type="button" onClick={() => setShowResolved(!showResolved)} className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[var(--bg-elevated)] transition-colors">
              <CheckCircle2 className="h-4 w-4 text-green-400" />
              <span className="text-[0.82rem] text-[var(--text-mid)]">{resolvedComments.length} resolved</span>
              <span className="ml-auto">{showResolved ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}</span>
            </button>
            {showResolved && resolvedComments.map((comment) => (
              <div key={comment.id} className="p-3 border-b border-[var(--border)] opacity-70">
                <div className="flex items-center gap-2 mb-1">
                  <Avatar className="w-5 h-5">
                    <AvatarFallback style={{ backgroundColor: comment.authorColor }} className="text-[0.6rem] text-white">{getInitials(comment.authorName)}</AvatarFallback>
                  </Avatar>
                  <span className="text-xs font-semibold text-[var(--text-mid)]">{comment.authorName}</span>
                  <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
                </div>
                <p className="text-[0.8rem] text-[var(--text-low)] ml-7 line-through">{comment.content}</p>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function VersionHistory({
  versions, open, onToggle, onRestore,
}: {
  versions: VersionEntry[];
  open: boolean;
  onToggle: () => void;
  onRestore: (id: string) => void;
}) {
  return (
    <div className="border-t border-[var(--border)] bg-[var(--bg-surface)]">
      <button type="button" onClick={onToggle} className="w-full flex items-center gap-2 px-4 py-2 hover:bg-[var(--bg-elevated)] transition-colors">
        <History className="h-4 w-4" />
        <span className="text-[0.82rem] font-semibold text-[var(--text-high)]">Version History</span>
        <Badge variant="outline" className="ml-2 text-[0.7rem]">{versions.length} versions</Badge>
        <span className="ml-auto">{open ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}</span>
      </button>

      {open && (
        <div className="max-h-[260px] overflow-auto px-4 pb-3">
          {versions.map((v, idx) => (
            <div
              key={v.id}
              className={`flex items-start gap-3 py-2.5 ${idx < versions.length - 1 ? 'border-b border-[var(--border)]' : ''}`}
            >
              <div className="flex flex-col items-center pt-1">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: v.authorColor }} />
                {idx < versions.length - 1 && <div className="w-px flex-1 bg-[var(--border)] mt-1 min-h-[24px]" />}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1 mb-0.5">
                  <span className="text-[0.82rem] font-semibold text-[var(--text-high)]">{v.authorName}</span>
                  <span className="text-xs text-[var(--text-low)]">{formatFullTimestamp(v.timestamp)}</span>
                </div>
                <p className="text-[0.8rem] text-[var(--text-mid)] mb-1">{v.summary}</p>

                <div className="flex items-center gap-2">
                  {v.additions > 0 && <span className="text-xs font-semibold font-mono text-green-400">+{v.additions}</span>}
                  {v.deletions > 0 && <span className="text-xs font-semibold font-mono text-red-400">-{v.deletions}</span>}
                  <div className="flex h-1.5 rounded-full overflow-hidden flex-1 max-w-[80px]">
                    <div className="bg-green-500" style={{ width: `${(v.additions / (v.additions + v.deletions)) * 100}%` }} />
                    <div className="bg-red-500" style={{ width: `${(v.deletions / (v.additions + v.deletions)) * 100}%` }} />
                  </div>
                </div>
              </div>

              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" onClick={() => onRestore(v.id)} className="p-1 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors mt-0.5" aria-label="Restore this version">
                    <RotateCcw className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Restore this version</TooltipContent>
              </Tooltip>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusBar({
  connectionStatus, lastSaved, isSyncing, documentId, wordCount, charCount,
}: {
  connectionStatus: ConnectionStatus;
  lastSaved: string;
  isSyncing: boolean;
  documentId: string;
  wordCount: number;
  charCount: number;
}) {
  const statusConfig: Record<ConnectionStatus, { icon: React.ReactNode; label: string; className: string }> = {
    connected: { icon: <Cloud className="h-3.5 w-3.5" />, label: 'Connected', className: 'text-green-400' },
    reconnecting: { icon: <RefreshCw className="h-3.5 w-3.5 animate-spin" />, label: 'Reconnecting...', className: 'text-amber-400' },
    offline: { icon: <CloudOff className="h-3.5 w-3.5" />, label: 'Offline', className: 'text-red-400' },
  };

  const cfg = statusConfig[connectionStatus];

  return (
    <div className="flex items-center justify-between px-4 py-1 border-t border-[var(--border)] bg-[var(--bg-app)] min-h-[32px]">
      <div className="flex items-center gap-4">
        <div className={`flex items-center gap-1 ${cfg.className}`}>
          {cfg.icon}
          <span className="text-xs font-medium">{cfg.label}</span>
        </div>

        <Separator orientation="vertical" className="h-4" />

        <div className="flex items-center gap-1">
          {isSyncing ? (
            <>
              <RefreshCw className="h-3.5 w-3.5 text-blue-400 animate-spin" />
              <span className="text-xs text-blue-400">Syncing...</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
              <span className="text-xs text-[var(--text-low)]">Saved {formatTimestamp(lastSaved)}</span>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-xs text-[var(--text-low)]">
          {wordCount.toLocaleString()} words | {charCount.toLocaleString()} chars
        </span>
        <Separator orientation="vertical" className="h-4" />
        <span className="text-[0.65rem] text-[var(--text-low)] font-mono">{documentId}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function CollaboratePage() {
  const [documents, setDocuments] = useState<WorkspaceDocument[]>(MOCK_DOCUMENTS);
  const [selectedDocId, setSelectedDocId] = useState('doc-1');
  const [editorContent, setEditorContent] = useState(INITIAL_CONTENT);
  const [comments, setComments] = useState<DocComment[]>(MOCK_COMMENTS);
  const [versions] = useState<VersionEntry[]>(MOCK_VERSIONS);
  const [users] = useState<CollabUser[]>(MOCK_USERS);

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connected');
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSaved, setLastSaved] = useState('2026-03-25T14:30:00Z');

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [commentsPanelOpen, setCommentsPanelOpen] = useState(true);
  const [versionHistoryOpen, setVersionHistoryOpen] = useState(false);
  const [activeFormats, setActiveFormats] = useState<Set<string>>(new Set());

  const editorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsSyncing(true);
      setTimeout(() => { setIsSyncing(false); setLastSaved(new Date().toISOString()); }, 800);
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setConnectionStatus('reconnecting');
      setTimeout(() => setConnectionStatus('connected'), 2000);
    }, 30000);
    return () => clearTimeout(timeout);
  }, []);

  const updateActiveFormats = useCallback(() => {
    const formats = new Set<string>();
    if (document.queryCommandState('bold')) formats.add('bold');
    if (document.queryCommandState('italic')) formats.add('italic');
    if (document.queryCommandState('underline')) formats.add('underline');
    setActiveFormats(formats);
  }, []);

  const handleEditorCommand = useCallback((cmd: string, value?: string) => {
    document.execCommand(cmd, false, value);
    editorRef.current?.focus();
    updateActiveFormats();
  }, [updateActiveFormats]);

  const handleContentChange = useCallback(() => {
    if (editorRef.current) setEditorContent(editorRef.current.innerHTML);
  }, []);

  const wordCount = useMemo(() => countWords(editorContent), [editorContent]);
  const charCount = useMemo(() => countChars(editorContent), [editorContent]);

  const handleSelectDoc = useCallback((id: string) => { setSelectedDocId(id); }, []);

  const handleCreateDoc = useCallback(() => {
    const newDoc: WorkspaceDocument = {
      id: `doc-${Date.now()}`, title: 'Untitled Document', lastModified: new Date().toISOString(),
      contributors: ['You'], isActive: true, wordCount: 0,
    };
    setDocuments((prev) => [newDoc, ...prev]);
    setSelectedDocId(newDoc.id);
  }, []);

  const handleResolveComment = useCallback((id: string) => {
    setComments((prev) => prev.map((c) => (c.id === id ? { ...c, resolved: true } : c)));
  }, []);

  const handleReplyComment = useCallback((commentId: string, text: string) => {
    const newReply: CommentReply = { id: `r-${Date.now()}`, authorId: 'current-user', authorName: 'You', content: text, timestamp: new Date().toISOString() };
    setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, replies: [...c.replies, newReply] } : c)));
  }, []);

  const handleDeleteComment = useCallback((id: string) => {
    setComments((prev) => prev.filter((c) => c.id !== id));
  }, []);

  const handleAddComment = useCallback((content: string) => {
    const newComment: DocComment = {
      id: `c-${Date.now()}`, authorId: 'current-user', authorName: 'You', authorColor: '#9C27B0',
      content, timestamp: new Date().toISOString(), resolved: false, selection: 'selected text', replies: [],
    };
    setComments((prev) => [newComment, ...prev]);
  }, []);

  const handleRestoreVersion = useCallback((_versionId: string) => {
    setIsSyncing(true);
    setTimeout(() => { setIsSyncing(false); setLastSaved(new Date().toISOString()); }, 1500);
  }, []);

  return (
    <TooltipProvider>
      <div className="p-5 space-y-5 animate-enter">
        {/* Page header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Users className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Collaborative Editor</h1>
            <p className="text-xs text-[var(--text-mid)]">Real-time workspace collaboration</p>
          </div>
        </div>

        {/* Editor surface */}
        <div className="surface-card p-0 overflow-hidden">
          {/* Top bar */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border)] min-h-[48px]">
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="flex items-center gap-1.5 text-[0.7rem]">
                <Circle className="h-2 w-2 text-green-400 fill-green-400" /> Real-time
              </Badge>
            </div>

            <div className="flex items-center gap-4">
              <PresenceBar users={users} />
              <Separator orientation="vertical" className="h-6" />
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={() => setCommentsPanelOpen(!commentsPanelOpen)}
                    className={`relative p-1.5 rounded transition-colors ${commentsPanelOpen ? 'text-[var(--accent)] bg-[var(--accent)]/10' : 'text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]'}`}
                    aria-label={commentsPanelOpen ? 'Hide comments' : 'Show comments'}
                  >
                    <MessageSquare className="h-4 w-4" />
                    {comments.filter((c) => !c.resolved).length > 0 && (
                      <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] flex items-center justify-center font-semibold">
                        {Math.min(comments.filter((c) => !c.resolved).length, 9)}
                      </span>
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent>{commentsPanelOpen ? 'Hide comments' : 'Show comments'}</TooltipContent>
              </Tooltip>
            </div>
          </div>

          {/* Main content area */}
          <div className="flex overflow-hidden" style={{ height: 'calc(100vh - 280px)', minHeight: 400 }}>
            <DocumentSidebar
              documents={documents} selectedId={selectedDocId} onSelect={handleSelectDoc}
              onCreateNew={handleCreateDoc} collapsed={sidebarCollapsed}
              onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            {/* Editor area */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Collaborative editing indicator */}
              <div className="px-4 py-1.5 bg-[var(--bg-elevated)] flex items-center gap-2">
                <div className="flex gap-1">
                  {users.filter((u) => u.isOnline).map((u) => (
                    <Tooltip key={u.id}>
                      <TooltipTrigger asChild>
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: u.color, animation: 'pulse 2s infinite' }} />
                      </TooltipTrigger>
                      <TooltipContent>{u.name} is editing</TooltipContent>
                    </Tooltip>
                  ))}
                </div>
                <span className="text-[0.7rem] text-[var(--text-low)]">
                  {users.filter((u) => u.isOnline).length} collaborators editing | Yjs WebSocket: awaiting backend connection
                </span>
              </div>

              {/* Toolbar */}
              <div className="px-4 pt-2">
                <EditorToolbar onCommand={handleEditorCommand} activeFormats={activeFormats} />
              </div>

              {/* Editor */}
              <div className="flex-1 overflow-auto px-4 pb-2">
                <div className="min-h-full border border-[var(--border)] border-t-0 rounded-b-lg">
                  <div
                    ref={editorRef}
                    contentEditable
                    suppressContentEditableWarning
                    dangerouslySetInnerHTML={{ __html: INITIAL_CONTENT }}
                    onInput={handleContentChange}
                    onMouseUp={updateActiveFormats}
                    onKeyUp={updateActiveFormats}
                    className="p-6 min-h-[400px] outline-none text-[0.95rem] leading-7 text-[var(--text-high)] [&_h1]:text-[1.75rem] [&_h1]:font-bold [&_h1]:mt-4 [&_h1]:mb-2 [&_h1]:border-b [&_h1]:border-[var(--border)] [&_h1]:pb-1 [&_h2]:text-[1.35rem] [&_h2]:font-semibold [&_h2]:mt-5 [&_h2]:mb-1.5 [&_h3]:text-[1.1rem] [&_h3]:font-semibold [&_h3]:mt-4 [&_h3]:mb-1 [&_h3]:text-[var(--text-mid)] [&_p]:mb-2 [&_ul]:pl-6 [&_ul]:mb-2 [&_ol]:pl-6 [&_ol]:mb-2 [&_li]:mb-1 [&_pre]:bg-[var(--bg-elevated)] [&_pre]:p-4 [&_pre]:rounded [&_pre]:font-mono [&_pre]:text-[0.85rem] [&_pre]:overflow-auto [&_pre]:mb-2 [&_code]:bg-[var(--bg-elevated)] [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:font-mono [&_code]:text-[0.85rem]"
                  />
                </div>
              </div>

              <VersionHistory versions={versions} open={versionHistoryOpen} onToggle={() => setVersionHistoryOpen(!versionHistoryOpen)} onRestore={handleRestoreVersion} />
            </div>

            {/* Comments panel (right) */}
            {commentsPanelOpen && (
              <div className="w-[320px] min-w-[320px] h-full bg-[var(--bg-surface)] overflow-hidden flex flex-col border-l border-[var(--border)]">
                <CommentsPanel
                  comments={comments} onResolve={handleResolveComment} onReply={handleReplyComment}
                  onDelete={handleDeleteComment} onAdd={handleAddComment}
                />
              </div>
            )}
          </div>

          <StatusBar connectionStatus={connectionStatus} lastSaved={lastSaved} isSyncing={isSyncing} documentId={selectedDocId} wordCount={wordCount} charCount={charCount} />
        </div>
      </div>
    </TooltipProvider>
  );
}
