'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip,
  Divider, Grid, IconButton, Typography,
} from '@mui/material';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';

/**
 * Visual Pipeline Builder Demo
 *
 * Interactive DAG editor for building AI pipelines visually.
 * Uses a custom node-based canvas (React Flow-compatible structure).
 * Install @xyflow/react for the full drag-and-drop experience.
 */

const NODE_TYPES = [
  { type: 'transcribe', label: 'Transcribe', icon: '🎤', color: '#e3f2fd' },
  { type: 'summarize', label: 'Summarize', icon: '📋', color: '#f3e5f5' },
  { type: 'translate', label: 'Translate', icon: '🌐', color: '#e8f5e9' },
  { type: 'sentiment', label: 'Sentiment', icon: '💭', color: '#fff3e0' },
  { type: 'content_studio', label: 'Content Gen', icon: '✨', color: '#fce4ec' },
  { type: 'generate_image', label: 'Image Gen', icon: '🖼️', color: '#e0f7fa' },
  { type: 'generate_video', label: 'Video Gen', icon: '🎬', color: '#f1f8e9' },
  { type: 'text_to_speech', label: 'TTS', icon: '🔊', color: '#ede7f6' },
  { type: 'crawl', label: 'Web Crawl', icon: '🕷️', color: '#fff8e1' },
  { type: 'search_knowledge', label: 'Search KB', icon: '🔍', color: '#e1f5fe' },
  { type: 'security_scan', label: 'Security Scan', icon: '🛡️', color: '#ffebee' },
  { type: 'generate', label: 'AI Generate', icon: '🤖', color: '#f5f5f5' },
];

interface PipelineNode {
  id: string;
  type: string;
  label: string;
  icon: string;
  color: string;
  x: number;
  y: number;
  config: Record<string, string>;
}

interface PipelineEdge {
  id: string;
  source: string;
  target: string;
}

export default function PipelineBuilderPage() {
  const [nodes, setNodes] = useState<PipelineNode[]>([]);
  const [edges, setEdges] = useState<PipelineEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [connectFrom, setConnectFrom] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [validationResult, setValidationResult] = useState<Record<string, unknown> | null>(null);

  const addNode = (type: typeof NODE_TYPES[0]) => {
    const id = `node_${Date.now()}`;
    const col = nodes.length % 3;
    const row = Math.floor(nodes.length / 3);
    setNodes(prev => [...prev, {
      id, type: type.type, label: type.label, icon: type.icon,
      color: type.color, x: 100 + col * 250, y: 100 + row * 140, config: {},
    }]);
  };

  const removeNode = (id: string) => {
    setNodes(prev => prev.filter(n => n.id !== id));
    setEdges(prev => prev.filter(e => e.source !== id && e.target !== id));
    if (selectedNode === id) setSelectedNode(null);
  };

  const handleNodeClick = (id: string) => {
    if (connectFrom && connectFrom !== id) {
      // Create edge
      const edgeId = `edge_${Date.now()}`;
      setEdges(prev => [...prev, { id: edgeId, source: connectFrom, target: id }]);
      setConnectFrom(null);
    } else {
      setSelectedNode(id === selectedNode ? null : id);
    }
  };

  const handleValidate = async () => {
    try {
      const { default: apiClient } = await import('@/lib/apiClient');
      const resp = await apiClient.post('/api/workflows/validate', {
        name: 'Visual Pipeline',
        nodes: nodes.map(n => ({ id: n.id, type: 'action', action: n.type, label: n.label, config: n.config, position_x: n.x, position_y: n.y })),
        edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target })),
      });
      setValidationResult(resp.data);
    } catch (err: unknown) {
      setValidationResult({ valid: false, errors: [(err as Error).message] });
    }
  };

  const handleSave = async () => {
    try {
      const { default: apiClient } = await import('@/lib/apiClient');
      await apiClient.post('/api/workflows', {
        name: `Visual Pipeline ${new Date().toLocaleTimeString()}`,
        description: 'Created with visual pipeline builder',
        trigger_type: 'manual',
        nodes: nodes.map(n => ({ id: n.id, type: 'action', action: n.type, label: n.label, config: n.config, position_x: n.x, position_y: n.y })),
        edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target })),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // handle error
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AccountTreeIcon color="primary" /> Visual Pipeline Builder
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Build AI pipelines visually - drag nodes, connect edges, validate and execute
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" onClick={handleValidate} disabled={nodes.length === 0}>
            Validate DAG
          </Button>
          <Button variant="outlined" startIcon={<SaveIcon />} onClick={handleSave} disabled={nodes.length === 0}>
            Save as Workflow
          </Button>
        </Box>
      </Box>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>Pipeline saved as workflow!</Alert>}

      {validationResult && (
        <Alert severity={(validationResult as { valid: boolean }).valid ? 'success' : 'error'} sx={{ mb: 2 }} onClose={() => setValidationResult(null)}>
          {(validationResult as { valid: boolean }).valid
            ? `Valid DAG! ${((validationResult as { stats?: { total_nodes?: number } }).stats?.total_nodes) || 0} nodes, execution order ready.`
            : `Invalid: ${((validationResult as { errors?: string[] }).errors || []).join('; ')}`}
        </Alert>
      )}

      <Grid container spacing={2}>
        {/* Node Palette */}
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Add Nodes</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                {NODE_TYPES.map((nt) => (
                  <Chip
                    key={nt.type}
                    label={`${nt.icon} ${nt.label}`}
                    onClick={() => addNode(nt)}
                    sx={{ justifyContent: 'flex-start', bgcolor: nt.color, cursor: 'pointer' }}
                    icon={<AddIcon sx={{ fontSize: 16 }} />}
                  />
                ))}
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="caption" color="text.secondary">
                Click a node then click "Connect" and click another node to create an edge.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Canvas */}
        <Grid item xs={12} md={10}>
          <Card sx={{ minHeight: 500, position: 'relative', overflow: 'hidden' }}>
            <CardContent sx={{ p: 0, height: 500, position: 'relative' }}>
              {nodes.length === 0 ? (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Typography color="text.secondary">Add nodes from the palette to start building your pipeline</Typography>
                </Box>
              ) : (
                <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                      <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                    </marker>
                  </defs>
                  {edges.map((edge) => {
                    const src = nodes.find(n => n.id === edge.source);
                    const tgt = nodes.find(n => n.id === edge.target);
                    if (!src || !tgt) return null;
                    return (
                      <line key={edge.id} x1={src.x + 90} y1={src.y + 25} x2={tgt.x + 90} y2={tgt.y + 25}
                        stroke="#666" strokeWidth={2} markerEnd="url(#arrowhead)" style={{ pointerEvents: 'auto' }} />
                    );
                  })}
                </svg>
              )}

              {nodes.map((node) => (
                <Box
                  key={node.id}
                  onClick={() => handleNodeClick(node.id)}
                  sx={{
                    position: 'absolute',
                    left: node.x, top: node.y,
                    width: 180, height: 50,
                    bgcolor: node.color,
                    border: selectedNode === node.id ? '3px solid #1976d2' : connectFrom === node.id ? '3px solid #f57c00' : '1px solid #ccc',
                    borderRadius: 2, px: 1.5, py: 0.5,
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    cursor: 'pointer', boxShadow: 1,
                    '&:hover': { boxShadow: 3 },
                  }}
                >
                  <Typography variant="body2" fontWeight="bold" noWrap>
                    {node.icon} {node.label}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.3 }}>
                    <IconButton size="small"
                      onClick={(e) => { e.stopPropagation(); setConnectFrom(connectFrom === node.id ? null : node.id); }}
                      sx={{ color: connectFrom === node.id ? 'warning.main' : 'text.secondary', fontSize: 12 }}>
                      {connectFrom === node.id ? '⬤' : '→'}
                    </IconButton>
                    <IconButton size="small" onClick={(e) => { e.stopPropagation(); removeNode(node.id); }}>
                      <DeleteIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>

          {/* Pipeline Summary */}
          {nodes.length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="subtitle2">Flow:</Typography>
                  {nodes.map((n, i) => (
                    <Box key={n.id} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Chip label={`${n.icon} ${n.label}`} size="small" sx={{ bgcolor: n.color }} />
                      {i < nodes.length - 1 && <Typography color="text.disabled">→</Typography>}
                    </Box>
                  ))}
                  <Chip label={`${nodes.length} nodes, ${edges.length} edges`} size="small" variant="outlined" sx={{ ml: 'auto' }} />
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
