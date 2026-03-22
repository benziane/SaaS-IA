/**
 * ConversationList - Sidebar listing all user conversations
 * Displays title, date, and message count for each conversation.
 * Supports active highlighting, deletion with confirmation, and empty state.
 */

'use client';

import { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Skeleton,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add, Delete, Forum } from '@mui/icons-material';

import type { Conversation } from '@/features/conversation/types';

/* ========================================================================
   TYPES
   ======================================================================== */

export interface ConversationListProps {
  /** Array of conversations to display */
  conversations: Conversation[];
  /** Currently selected conversation ID */
  activeId: string | null;
  /** Called when a conversation is selected */
  onSelect: (id: string) => void;
  /** Called when the user confirms deletion of a conversation */
  onDelete: (id: string) => void;
  /** Called to create a new conversation */
  onCreate: () => void;
  /** Whether the list is loading */
  isLoading: boolean;
}

/* ========================================================================
   HELPERS
   ======================================================================== */

function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onCreate,
  isLoading,
}: ConversationListProps): JSX.Element {
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const handleConfirmDelete = (): void => {
    if (deleteTarget) {
      onDelete(deleteTarget);
      setDeleteTarget(null);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: 'background.paper',
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, pb: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
          Conversations
        </Typography>
        <Button
          fullWidth
          variant="contained"
          startIcon={<Add />}
          onClick={onCreate}
          size="small"
        >
          New Conversation
        </Button>
      </Box>

      <Divider />

      {/* Conversation List */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {isLoading ? (
          <Box sx={{ p: 2 }}>
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton
                key={i}
                variant="rectangular"
                height={56}
                sx={{ mb: 1, borderRadius: 1 }}
              />
            ))}
          </Box>
        ) : conversations.length === 0 ? (
          <Box
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1,
              color: 'text.secondary',
            }}
          >
            <Forum sx={{ fontSize: 48, opacity: 0.3 }} />
            <Typography variant="body2" color="text.secondary" textAlign="center">
              No conversations yet. Start a new one to chat with AI.
            </Typography>
          </Box>
        ) : (
          <List disablePadding>
            {conversations.map((conversation) => {
              const isActive = conversation.id === activeId;

              return (
                <ListItem
                  key={conversation.id}
                  disablePadding
                  secondaryAction={
                    <Tooltip title="Delete conversation">
                      <IconButton
                        edge="end"
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteTarget(conversation.id);
                        }}
                        sx={{
                          opacity: 0,
                          transition: 'opacity 0.2s',
                          '.MuiListItem-root:hover &': { opacity: 1 },
                        }}
                      >
                        <Delete fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  }
                >
                  <ListItemButton
                    selected={isActive}
                    onClick={() => onSelect(conversation.id)}
                    sx={{
                      borderRadius: 0,
                      borderLeft: isActive ? '3px solid' : '3px solid transparent',
                      borderLeftColor: isActive ? 'primary.main' : 'transparent',
                      py: 1.5,
                      px: 2,
                    }}
                  >
                    <ListItemText
                      primary={
                        <Typography
                          variant="body2"
                          sx={{
                            fontWeight: isActive ? 600 : 400,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: 180,
                          }}
                        >
                          {conversation.title || 'New Conversation'}
                        </Typography>
                      }
                      secondary={
                        <Box
                          component="span"
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            mt: 0.5,
                          }}
                        >
                          <Typography variant="caption" color="text.secondary">
                            {formatRelativeDate(conversation.updated_at)}
                          </Typography>
                          {conversation.message_count > 0 && (
                            <Chip
                              label={conversation.message_count}
                              size="small"
                              variant="outlined"
                              sx={{ height: 18, fontSize: '0.65rem' }}
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        )}
      </Box>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Delete Conversation</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this conversation? All messages will
            be permanently removed. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ConversationList;
