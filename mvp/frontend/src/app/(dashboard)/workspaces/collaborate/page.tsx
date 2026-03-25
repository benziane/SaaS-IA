'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Avatar,
  AvatarGroup,
  Badge,
  Box,
  Button,
  Chip,
  Collapse,
  Divider,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ArticleIcon from '@mui/icons-material/Article';
import BoltIcon from '@mui/icons-material/Bolt';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import CircleIcon from '@mui/icons-material/Circle';
import CloudDoneIcon from '@mui/icons-material/CloudDone';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import CodeIcon from '@mui/icons-material/Code';
import CommentIcon from '@mui/icons-material/Comment';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import FormatBoldIcon from '@mui/icons-material/FormatBold';
import FormatItalicIcon from '@mui/icons-material/FormatItalic';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import FormatUnderlinedIcon from '@mui/icons-material/FormatUnderlined';
import HistoryIcon from '@mui/icons-material/History';
import ReplyIcon from '@mui/icons-material/Reply';
import RestoreIcon from '@mui/icons-material/Restore';
import SendIcon from '@mui/icons-material/Send';
import SyncIcon from '@mui/icons-material/Sync';
import TitleIcon from '@mui/icons-material/Title';
import WifiIcon from '@mui/icons-material/Wifi';

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
  {
    id: 'doc-1',
    title: 'Product Requirements - Q1 2026',
    lastModified: '2026-03-25T14:30:00Z',
    contributors: ['Alice Martin', 'Bob Dupont'],
    isActive: true,
    wordCount: 2340,
  },
  {
    id: 'doc-2',
    title: 'Technical Architecture Notes',
    lastModified: '2026-03-24T10:15:00Z',
    contributors: ['Claire Bernard', 'Alice Martin'],
    isActive: false,
    wordCount: 1856,
  },
  {
    id: 'doc-3',
    title: 'Sprint Retrospective - Week 12',
    lastModified: '2026-03-23T16:45:00Z',
    contributors: ['Bob Dupont'],
    isActive: false,
    wordCount: 620,
  },
  {
    id: 'doc-4',
    title: 'API Integration Guide',
    lastModified: '2026-03-22T09:00:00Z',
    contributors: ['Alice Martin', 'Claire Bernard', 'Bob Dupont'],
    isActive: false,
    wordCount: 4120,
  },
  {
    id: 'doc-5',
    title: 'User Research Findings',
    lastModified: '2026-03-20T11:30:00Z',
    contributors: ['Claire Bernard'],
    isActive: false,
    wordCount: 1450,
  },
];

const MOCK_COMMENTS: DocComment[] = [
  {
    id: 'c1',
    authorId: 'u2',
    authorName: 'Bob Dupont',
    authorColor: '#4CAF50',
    content: 'Should we add more detail on the authentication flow here? The current description is a bit vague for the backend team.',
    timestamp: '2026-03-25T13:15:00Z',
    resolved: false,
    selection: 'authentication requirements',
    replies: [
      {
        id: 'r1',
        authorId: 'u1',
        authorName: 'Alice Martin',
        content: 'Good point. I\'ll add a sequence diagram in the next revision.',
        timestamp: '2026-03-25T13:22:00Z',
      },
    ],
  },
  {
    id: 'c2',
    authorId: 'u3',
    authorName: 'Claire Bernard',
    authorColor: '#FF9800',
    content: 'This section needs to be reviewed by the security team before we finalize.',
    timestamp: '2026-03-25T12:00:00Z',
    resolved: false,
    selection: 'data encryption policy',
    replies: [],
  },
  {
    id: 'c3',
    authorId: 'u1',
    authorName: 'Alice Martin',
    authorColor: '#2196F3',
    content: 'Updated the performance targets based on last week\'s benchmarks.',
    timestamp: '2026-03-24T16:30:00Z',
    resolved: true,
    selection: 'performance requirements',
    replies: [
      {
        id: 'r2',
        authorId: 'u2',
        authorName: 'Bob Dupont',
        content: 'Looks good. The new numbers align with our SLA.',
        timestamp: '2026-03-24T16:45:00Z',
      },
      {
        id: 'r3',
        authorId: 'u3',
        authorName: 'Claire Bernard',
        content: 'Confirmed. Marking as resolved.',
        timestamp: '2026-03-24T17:00:00Z',
      },
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
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
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

/** Sidebar: list of workspace documents */
function DocumentSidebar({
  documents,
  selectedId,
  onSelect,
  onCreateNew,
  collapsed,
  onToggle,
}: {
  documents: WorkspaceDocument[];
  selectedId: string;
  onSelect: (id: string) => void;
  onCreateNew: () => void;
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <Box
      sx={{
        width: collapsed ? 48 : 280,
        minWidth: collapsed ? 48 : 280,
        borderRight: 1,
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper',
        transition: 'width 0.2s, min-width 0.2s',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between', p: 1.5, minHeight: 56 }}>
        {!collapsed && (
          <Typography variant="subtitle2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, color: 'text.secondary', fontSize: '0.7rem' }}>
            Documents
          </Typography>
        )}
        <IconButton size="small" onClick={onToggle}>
          {collapsed ? <ChevronRightIcon fontSize="small" /> : <ChevronLeftIcon fontSize="small" />}
        </IconButton>
      </Box>

      {!collapsed && (
        <>
          <Box sx={{ px: 1.5, pb: 1 }}>
            <Button
              fullWidth
              variant="outlined"
              size="small"
              startIcon={<AddIcon />}
              onClick={onCreateNew}
              sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
            >
              New Document
            </Button>
          </Box>

          <Divider />

          <List sx={{ flex: 1, overflow: 'auto', py: 0.5 }}>
            {documents.map((doc) => (
              <ListItemButton
                key={doc.id}
                selected={doc.id === selectedId}
                onClick={() => onSelect(doc.id)}
                sx={{
                  mx: 0.5,
                  borderRadius: 1,
                  mb: 0.25,
                  py: 1,
                  '&.Mui-selected': { bgcolor: 'action.selected' },
                }}
              >
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <Badge
                    variant="dot"
                    color="success"
                    invisible={!doc.isActive}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  >
                    <ArticleIcon fontSize="small" color={doc.id === selectedId ? 'primary' : 'action'} />
                  </Badge>
                </ListItemIcon>
                <ListItemText
                  primary={doc.title}
                  secondary={formatTimestamp(doc.lastModified)}
                  primaryTypographyProps={{
                    variant: 'body2',
                    fontWeight: doc.id === selectedId ? 600 : 400,
                    noWrap: true,
                    sx: { fontSize: '0.82rem' },
                  }}
                  secondaryTypographyProps={{ variant: 'caption', noWrap: true }}
                />
              </ListItemButton>
            ))}
          </List>

          <Divider />
          <Box sx={{ p: 1.5 }}>
            <Typography variant="caption" color="text.secondary">
              {documents.length} documents
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
}

/** Toolbar for the rich text editor */
function EditorToolbar({
  onCommand,
  activeFormats,
}: {
  onCommand: (cmd: string, value?: string) => void;
  activeFormats: Set<string>;
}) {
  const [headingAnchor, setHeadingAnchor] = useState<null | HTMLElement>(null);

  const handleHeading = (level: HeadingLevel) => {
    onCommand('formatBlock', `<${level}>`);
    setHeadingAnchor(null);
  };

  return (
    <Paper
      variant="outlined"
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.25,
        px: 1,
        py: 0.5,
        borderRadius: '8px 8px 0 0',
        borderBottom: 'none',
        flexWrap: 'wrap',
      }}
    >
      <ToggleButtonGroup size="small" sx={{ '& .MuiToggleButton-root': { border: 'none', borderRadius: 1, px: 1 } }}>
        <ToggleButton
          value="bold"
          selected={activeFormats.has('bold')}
          onClick={() => onCommand('bold')}
          aria-label="Bold"
        >
          <FormatBoldIcon fontSize="small" />
        </ToggleButton>
        <ToggleButton
          value="italic"
          selected={activeFormats.has('italic')}
          onClick={() => onCommand('italic')}
          aria-label="Italic"
        >
          <FormatItalicIcon fontSize="small" />
        </ToggleButton>
        <ToggleButton
          value="underline"
          selected={activeFormats.has('underline')}
          onClick={() => onCommand('underline')}
          aria-label="Underline"
        >
          <FormatUnderlinedIcon fontSize="small" />
        </ToggleButton>
      </ToggleButtonGroup>

      <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />

      {/* Heading dropdown */}
      <Tooltip title="Heading">
        <IconButton size="small" onClick={(e) => setHeadingAnchor(e.currentTarget)}>
          <TitleIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Menu anchorEl={headingAnchor} open={!!headingAnchor} onClose={() => setHeadingAnchor(null)}>
        <MenuItem onClick={() => handleHeading('h1')}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>Heading 1</Typography>
        </MenuItem>
        <MenuItem onClick={() => handleHeading('h2')}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Heading 2</Typography>
        </MenuItem>
        <MenuItem onClick={() => handleHeading('h3')}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Heading 3</Typography>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => { onCommand('formatBlock', '<p>'); setHeadingAnchor(null); }}>
          <Typography variant="body2">Normal text</Typography>
        </MenuItem>
      </Menu>

      <Tooltip title="Bullet List">
        <IconButton size="small" onClick={() => onCommand('insertUnorderedList')}>
          <FormatListBulletedIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Tooltip title="Code Block">
        <IconButton size="small" onClick={() => onCommand('formatBlock', '<pre>')}>
          <CodeIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Paper>
  );
}

/** Presence bar showing connected users */
function PresenceBar({ users }: { users: CollabUser[] }) {
  const onlineUsers = users.filter((u) => u.isOnline);
  return (
    <Stack direction="row" alignItems="center" spacing={1.5}>
      <Chip
        icon={<WifiIcon sx={{ fontSize: 14 }} />}
        label={`${onlineUsers.length} user${onlineUsers.length !== 1 ? 's' : ''} online`}
        size="small"
        color="success"
        variant="outlined"
        sx={{ fontWeight: 500 }}
      />
      <AvatarGroup
        max={5}
        sx={{
          '& .MuiAvatar-root': { width: 30, height: 30, fontSize: '0.75rem', fontWeight: 600 },
        }}
      >
        {onlineUsers.map((u) => (
          <Tooltip key={u.id} title={`${u.name} - Line ${u.cursorLine}, Col ${u.cursorChar}`} arrow>
            <Avatar sx={{ bgcolor: u.color, cursor: 'pointer' }}>
              {getInitials(u.name)}
            </Avatar>
          </Tooltip>
        ))}
      </AvatarGroup>
    </Stack>
  );
}

/** Comments panel */
function CommentsPanel({
  comments,
  onResolve,
  onReply,
  onDelete,
  onAdd,
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
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, color: 'text.secondary', fontSize: '0.7rem' }}>
          Comments ({openComments.length})
        </Typography>
      </Box>

      {/* New comment input */}
      <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <TextField
          fullWidth
          size="small"
          multiline
          minRows={2}
          maxRows={4}
          placeholder="Add a comment..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          sx={{ mb: 1 }}
        />
        <Button
          size="small"
          variant="contained"
          disabled={!newComment.trim()}
          onClick={handleAdd}
          startIcon={<SendIcon />}
          sx={{ textTransform: 'none' }}
        >
          Comment
        </Button>
      </Box>

      {/* Open comments */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {openComments.length === 0 && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <CommentIcon sx={{ fontSize: 40, color: 'text.disabled', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              No open comments
            </Typography>
          </Box>
        )}

        {openComments.map((comment) => (
          <Box key={comment.id} sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
            {/* Highlighted selection reference */}
            <Chip
              label={comment.selection}
              size="small"
              variant="outlined"
              sx={{ mb: 1, fontSize: '0.7rem', borderStyle: 'dashed' }}
            />

            {/* Comment header */}
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
              <Avatar sx={{ width: 24, height: 24, fontSize: '0.65rem', bgcolor: comment.authorColor }}>
                {getInitials(comment.authorName)}
              </Avatar>
              <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.82rem' }}>
                {comment.authorName}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatTimestamp(comment.timestamp)}
              </Typography>
            </Stack>

            {/* Comment body */}
            <Typography variant="body2" sx={{ ml: 4, mb: 1, color: 'text.primary', lineHeight: 1.5 }}>
              {comment.content}
            </Typography>

            {/* Replies */}
            {comment.replies.length > 0 && (
              <Box sx={{ ml: 4, pl: 1.5, borderLeft: 2, borderColor: 'divider', mb: 1 }}>
                {comment.replies.map((reply) => (
                  <Box key={reply.id} sx={{ mb: 1 }}>
                    <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mb: 0.25 }}>
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                        {reply.authorName}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatTimestamp(reply.timestamp)}
                      </Typography>
                    </Stack>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                      {reply.content}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {/* Reply input */}
            {replyingTo === comment.id ? (
              <Box sx={{ ml: 4, mt: 0.5 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Reply..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleReply(comment.id);
                    }
                  }}
                  sx={{ mb: 0.5 }}
                />
                <Stack direction="row" spacing={0.5}>
                  <Button size="small" onClick={() => handleReply(comment.id)} disabled={!replyText.trim()} sx={{ textTransform: 'none', minWidth: 0 }}>
                    Reply
                  </Button>
                  <Button size="small" onClick={() => { setReplyingTo(null); setReplyText(''); }} sx={{ textTransform: 'none', minWidth: 0 }}>
                    Cancel
                  </Button>
                </Stack>
              </Box>
            ) : (
              <Stack direction="row" spacing={0.5} sx={{ ml: 4 }}>
                <Button size="small" startIcon={<ReplyIcon sx={{ fontSize: 14 }} />} onClick={() => setReplyingTo(comment.id)} sx={{ textTransform: 'none', fontSize: '0.75rem', minWidth: 0 }}>
                  Reply
                </Button>
                <Button size="small" startIcon={<CheckCircleOutlineIcon sx={{ fontSize: 14 }} />} onClick={() => onResolve(comment.id)} sx={{ textTransform: 'none', fontSize: '0.75rem', minWidth: 0 }}>
                  Resolve
                </Button>
                <IconButton size="small" onClick={() => onDelete(comment.id)} sx={{ ml: 'auto' }}>
                  <DeleteOutlineIcon sx={{ fontSize: 14 }} />
                </IconButton>
              </Stack>
            )}
          </Box>
        ))}

        {/* Resolved section */}
        {resolvedComments.length > 0 && (
          <>
            <ListItemButton onClick={() => setShowResolved(!showResolved)} sx={{ py: 1 }}>
              <ListItemIcon sx={{ minWidth: 28 }}>
                <CheckCircleIcon fontSize="small" color="success" />
              </ListItemIcon>
              <ListItemText
                primary={`${resolvedComments.length} resolved`}
                primaryTypographyProps={{ variant: 'body2', color: 'text.secondary', fontSize: '0.82rem' }}
              />
              {showResolved ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
            </ListItemButton>
            <Collapse in={showResolved}>
              {resolvedComments.map((comment) => (
                <Box key={comment.id} sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider', opacity: 0.7 }}>
                  <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
                    <Avatar sx={{ width: 20, height: 20, fontSize: '0.6rem', bgcolor: comment.authorColor }}>
                      {getInitials(comment.authorName)}
                    </Avatar>
                    <Typography variant="caption" sx={{ fontWeight: 600 }}>{comment.authorName}</Typography>
                    <CheckCircleIcon sx={{ fontSize: 14, color: 'success.main' }} />
                  </Stack>
                  <Typography variant="body2" sx={{ ml: 3.5, fontSize: '0.8rem', color: 'text.secondary', textDecoration: 'line-through' }}>
                    {comment.content}
                  </Typography>
                </Box>
              ))}
            </Collapse>
          </>
        )}
      </Box>
    </Box>
  );
}

/** Version history drawer */
function VersionHistory({
  versions,
  open,
  onToggle,
  onRestore,
}: {
  versions: VersionEntry[];
  open: boolean;
  onToggle: () => void;
  onRestore: (id: string) => void;
}) {
  return (
    <Box sx={{ borderTop: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      {/* Toggle header */}
      <ListItemButton onClick={onToggle} sx={{ py: 0.75, px: 2 }}>
        <ListItemIcon sx={{ minWidth: 28 }}>
          <HistoryIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText
          primary="Version History"
          primaryTypographyProps={{ variant: 'body2', fontWeight: 600, fontSize: '0.82rem' }}
        />
        <Chip label={`${versions.length} versions`} size="small" variant="outlined" sx={{ mr: 1, fontSize: '0.7rem' }} />
        {open ? <ExpandMoreIcon fontSize="small" /> : <ExpandLessIcon fontSize="small" />}
      </ListItemButton>

      <Collapse in={open}>
        <Box sx={{ maxHeight: 260, overflow: 'auto', px: 2, pb: 1.5 }}>
          {versions.map((v, idx) => (
            <Box
              key={v.id}
              sx={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1.5,
                py: 1.25,
                borderBottom: idx < versions.length - 1 ? 1 : 0,
                borderColor: 'divider',
              }}
            >
              {/* Timeline indicator */}
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', pt: 0.5 }}>
                <FiberManualRecordIcon sx={{ fontSize: 10, color: v.authorColor }} />
                {idx < versions.length - 1 && (
                  <Box sx={{ width: 1.5, flex: 1, bgcolor: 'divider', mt: 0.5, minHeight: 24 }} />
                )}
              </Box>

              {/* Content */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mb: 0.25 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.82rem' }}>
                    {v.authorName}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatFullTimestamp(v.timestamp)}
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem', mb: 0.5 }}>
                  {v.summary}
                </Typography>

                {/* Diff indicators */}
                <Stack direction="row" spacing={1} alignItems="center">
                  {v.additions > 0 && (
                    <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600, fontFamily: 'monospace' }}>
                      +{v.additions}
                    </Typography>
                  )}
                  {v.deletions > 0 && (
                    <Typography variant="caption" sx={{ color: 'error.main', fontWeight: 600, fontFamily: 'monospace' }}>
                      -{v.deletions}
                    </Typography>
                  )}
                  {/* Visual bar */}
                  <Box sx={{ display: 'flex', height: 6, borderRadius: 3, overflow: 'hidden', flex: 1, maxWidth: 80 }}>
                    <Box sx={{ width: `${(v.additions / (v.additions + v.deletions)) * 100}%`, bgcolor: 'success.main' }} />
                    <Box sx={{ width: `${(v.deletions / (v.additions + v.deletions)) * 100}%`, bgcolor: 'error.main' }} />
                  </Box>
                </Stack>
              </Box>

              {/* Restore button */}
              <Tooltip title="Restore this version" arrow>
                <IconButton size="small" onClick={() => onRestore(v.id)} sx={{ mt: 0.25 }}>
                  <RestoreIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
}

/** Status bar at the bottom */
function StatusBar({
  connectionStatus,
  lastSaved,
  isSyncing,
  documentId,
  wordCount,
  charCount,
}: {
  connectionStatus: ConnectionStatus;
  lastSaved: string;
  isSyncing: boolean;
  documentId: string;
  wordCount: number;
  charCount: number;
}) {
  const statusConfig: Record<ConnectionStatus, { icon: React.ReactNode; label: string; color: string }> = {
    connected: { icon: <CloudDoneIcon sx={{ fontSize: 14 }} />, label: 'Connected', color: 'success.main' },
    reconnecting: { icon: <SyncIcon sx={{ fontSize: 14, animation: 'spin 1s linear infinite', '@keyframes spin': { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } } }} />, label: 'Reconnecting...', color: 'warning.main' },
    offline: { icon: <CloudOffIcon sx={{ fontSize: 14 }} />, label: 'Offline', color: 'error.main' },
  };

  const cfg = statusConfig[connectionStatus];

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 2,
        py: 0.5,
        borderTop: 1,
        borderColor: 'divider',
        bgcolor: 'background.default',
        minHeight: 32,
      }}
    >
      <Stack direction="row" alignItems="center" spacing={2}>
        {/* Connection status */}
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ color: cfg.color, display: 'flex', alignItems: 'center' }}>{cfg.icon}</Box>
          <Typography variant="caption" sx={{ color: cfg.color, fontWeight: 500 }}>
            {cfg.label}
          </Typography>
        </Stack>

        <Divider orientation="vertical" flexItem />

        {/* Sync indicator */}
        <Stack direction="row" alignItems="center" spacing={0.5}>
          {isSyncing ? (
            <>
              <SyncIcon sx={{ fontSize: 14, color: 'info.main', animation: 'spin 1s linear infinite', '@keyframes spin': { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } } }} />
              <Typography variant="caption" color="info.main">Syncing...</Typography>
            </>
          ) : (
            <>
              <CheckCircleIcon sx={{ fontSize: 14, color: 'success.main' }} />
              <Typography variant="caption" color="text.secondary">Saved {formatTimestamp(lastSaved)}</Typography>
            </>
          )}
        </Stack>
      </Stack>

      <Stack direction="row" alignItems="center" spacing={2}>
        {/* Word/char count */}
        <Typography variant="caption" color="text.secondary">
          {wordCount.toLocaleString()} words | {charCount.toLocaleString()} chars
        </Typography>

        <Divider orientation="vertical" flexItem />

        {/* Document ID */}
        <Typography variant="caption" color="text.disabled" sx={{ fontFamily: 'monospace', fontSize: '0.65rem' }}>
          {documentId}
        </Typography>
      </Stack>
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function CollaboratePage() {
  // State
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

  // Simulate periodic syncing
  useEffect(() => {
    const interval = setInterval(() => {
      setIsSyncing(true);
      setTimeout(() => {
        setIsSyncing(false);
        setLastSaved(new Date().toISOString());
      }, 800);
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  // Simulate connection status changes (reconnecting blip)
  useEffect(() => {
    const timeout = setTimeout(() => {
      setConnectionStatus('reconnecting');
      setTimeout(() => setConnectionStatus('connected'), 2000);
    }, 30000);
    return () => clearTimeout(timeout);
  }, []);

  // Track active formatting from selection
  const updateActiveFormats = useCallback(() => {
    const formats = new Set<string>();
    if (document.queryCommandState('bold')) formats.add('bold');
    if (document.queryCommandState('italic')) formats.add('italic');
    if (document.queryCommandState('underline')) formats.add('underline');
    setActiveFormats(formats);
  }, []);

  // Editor command handler
  const handleEditorCommand = useCallback((cmd: string, value?: string) => {
    document.execCommand(cmd, false, value);
    editorRef.current?.focus();
    updateActiveFormats();
  }, [updateActiveFormats]);

  // Handle content changes
  const handleContentChange = useCallback(() => {
    if (editorRef.current) {
      setEditorContent(editorRef.current.innerHTML);
    }
  }, []);

  // Computed values
  const wordCount = useMemo(() => countWords(editorContent), [editorContent]);
  const charCount = useMemo(() => countChars(editorContent), [editorContent]);

  // Document selection
  const handleSelectDoc = useCallback((id: string) => {
    setSelectedDocId(id);
    // In a real app, would load document content from backend/Yjs
  }, []);

  // Create new document
  const handleCreateDoc = useCallback(() => {
    const newDoc: WorkspaceDocument = {
      id: `doc-${Date.now()}`,
      title: 'Untitled Document',
      lastModified: new Date().toISOString(),
      contributors: ['You'],
      isActive: true,
      wordCount: 0,
    };
    setDocuments((prev) => [newDoc, ...prev]);
    setSelectedDocId(newDoc.id);
  }, []);

  // Comment actions
  const handleResolveComment = useCallback((id: string) => {
    setComments((prev) => prev.map((c) => (c.id === id ? { ...c, resolved: true } : c)));
  }, []);

  const handleReplyComment = useCallback((commentId: string, text: string) => {
    const newReply: CommentReply = {
      id: `r-${Date.now()}`,
      authorId: 'current-user',
      authorName: 'You',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setComments((prev) =>
      prev.map((c) => (c.id === commentId ? { ...c, replies: [...c.replies, newReply] } : c))
    );
  }, []);

  const handleDeleteComment = useCallback((id: string) => {
    setComments((prev) => prev.filter((c) => c.id !== id));
  }, []);

  const handleAddComment = useCallback((content: string) => {
    const newComment: DocComment = {
      id: `c-${Date.now()}`,
      authorId: 'current-user',
      authorName: 'You',
      authorColor: '#9C27B0',
      content,
      timestamp: new Date().toISOString(),
      resolved: false,
      selection: 'selected text',
      replies: [],
    };
    setComments((prev) => [newComment, ...prev]);
  }, []);

  const handleRestoreVersion = useCallback((_versionId: string) => {
    // In a real app, this would restore document content from the version
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      setLastSaved(new Date().toISOString());
    }, 1500);
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
      {/* Top bar */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 2,
          py: 1,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          minHeight: 48,
        }}
      >
        <Stack direction="row" alignItems="center" spacing={2}>
          <BoltIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.1rem' }}>
            Collaborative Editor
          </Typography>
          <Chip
            label="Real-time"
            size="small"
            color="info"
            variant="outlined"
            icon={<CircleIcon sx={{ fontSize: '8px !important', color: 'success.main' }} />}
            sx={{ fontSize: '0.7rem' }}
          />
        </Stack>

        <Stack direction="row" alignItems="center" spacing={2}>
          <PresenceBar users={users} />
          <Divider orientation="vertical" flexItem />
          <Tooltip title={commentsPanelOpen ? 'Hide comments' : 'Show comments'}>
            <IconButton
              size="small"
              onClick={() => setCommentsPanelOpen(!commentsPanelOpen)}
              color={commentsPanelOpen ? 'primary' : 'default'}
            >
              <Badge badgeContent={comments.filter((c) => !c.resolved).length} color="error" max={9}>
                <CommentIcon fontSize="small" />
              </Badge>
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {/* Main content area */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Document sidebar */}
        <DocumentSidebar
          documents={documents}
          selectedId={selectedDocId}
          onSelect={handleSelectDoc}
          onCreateNew={handleCreateDoc}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Editor area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Collaborative editing indicator */}
          <Box sx={{ px: 2, py: 0.75, bgcolor: 'action.hover', display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              {users.filter((u) => u.isOnline).map((u) => (
                <Tooltip key={u.id} title={`${u.name} is editing`} arrow>
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: u.color,
                      animation: 'pulse 2s infinite',
                      '@keyframes pulse': {
                        '0%, 100%': { opacity: 1 },
                        '50%': { opacity: 0.4 },
                      },
                    }}
                  />
                </Tooltip>
              ))}
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              {users.filter((u) => u.isOnline).length} collaborators editing | Yjs WebSocket: awaiting backend connection
            </Typography>
          </Box>

          {/* Toolbar */}
          <Box sx={{ px: 2, pt: 1 }}>
            <EditorToolbar onCommand={handleEditorCommand} activeFormats={activeFormats} />
          </Box>

          {/* Editor */}
          <Box sx={{ flex: 1, overflow: 'auto', px: 2, pb: 1 }}>
            <Paper
              variant="outlined"
              sx={{
                minHeight: '100%',
                borderRadius: '0 0 8px 8px',
                p: 0,
              }}
            >
              <Box
                ref={editorRef}
                contentEditable
                suppressContentEditableWarning
                dangerouslySetInnerHTML={{ __html: INITIAL_CONTENT }}
                onInput={handleContentChange}
                onMouseUp={updateActiveFormats}
                onKeyUp={updateActiveFormats}
                sx={{
                  p: 3,
                  minHeight: 400,
                  outline: 'none',
                  fontFamily: '"Inter", "Roboto", sans-serif',
                  fontSize: '0.95rem',
                  lineHeight: 1.7,
                  color: 'text.primary',
                  '& h1': {
                    fontSize: '1.75rem',
                    fontWeight: 700,
                    mt: 2,
                    mb: 1,
                    color: 'text.primary',
                    borderBottom: 1,
                    borderColor: 'divider',
                    pb: 0.5,
                  },
                  '& h2': {
                    fontSize: '1.35rem',
                    fontWeight: 600,
                    mt: 2.5,
                    mb: 0.75,
                    color: 'text.primary',
                  },
                  '& h3': {
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    mt: 2,
                    mb: 0.5,
                    color: 'text.secondary',
                  },
                  '& p': {
                    mb: 1,
                    color: 'text.primary',
                  },
                  '& ul, & ol': {
                    pl: 3,
                    mb: 1,
                  },
                  '& li': {
                    mb: 0.5,
                  },
                  '& pre': {
                    bgcolor: 'action.hover',
                    p: 2,
                    borderRadius: 1,
                    fontFamily: '"Fira Code", "JetBrains Mono", monospace',
                    fontSize: '0.85rem',
                    overflow: 'auto',
                    mb: 1,
                  },
                  '& code': {
                    bgcolor: 'action.hover',
                    px: 0.5,
                    py: 0.25,
                    borderRadius: 0.5,
                    fontFamily: '"Fira Code", "JetBrains Mono", monospace',
                    fontSize: '0.85rem',
                  },
                  // Simulated remote cursors
                  '&::after': {
                    content: '""',
                    display: 'none',
                  },
                }}
              />
            </Paper>
          </Box>

          {/* Version history drawer */}
          <VersionHistory
            versions={versions}
            open={versionHistoryOpen}
            onToggle={() => setVersionHistoryOpen(!versionHistoryOpen)}
            onRestore={handleRestoreVersion}
          />
        </Box>

        {/* Comments panel (right) */}
        <Collapse in={commentsPanelOpen} orientation="horizontal" sx={{ borderLeft: 1, borderColor: 'divider' }}>
          <Box sx={{ width: 320, minWidth: 320, height: '100%', bgcolor: 'background.paper', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <CommentsPanel
              comments={comments}
              onResolve={handleResolveComment}
              onReply={handleReplyComment}
              onDelete={handleDeleteComment}
              onAdd={handleAddComment}
            />
          </Box>
        </Collapse>
      </Box>

      {/* Status bar */}
      <StatusBar
        connectionStatus={connectionStatus}
        lastSaved={lastSaved}
        isSyncing={isSyncing}
        documentId={selectedDocId}
        wordCount={wordCount}
        charCount={charCount}
      />
    </Box>
  );
}
