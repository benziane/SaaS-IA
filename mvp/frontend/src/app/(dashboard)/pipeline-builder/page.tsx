'use client';

import { useState } from 'react';
import { Plus, Save, Trash2, Workflow } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Separator } from '@/lib/design-hub/components/Separator';

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
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
            <Workflow className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Visual Pipeline Builder</h1>
            <p className="text-xs text-[var(--text-mid)]">Visual pipeline builder</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleValidate} disabled={nodes.length === 0}>
            Validate DAG
          </Button>
          <Button variant="outline" onClick={handleSave} disabled={nodes.length === 0}>
            <Save className="h-4 w-4 mr-1" />
            Save as Workflow
          </Button>
        </div>
      </div>

      {saved && (
        <Alert variant="success">
          <AlertDescription>Pipeline saved as workflow!</AlertDescription>
        </Alert>
      )}

      {validationResult && (
        <Alert
          variant={(validationResult as { valid: boolean }).valid ? 'success' : 'destructive'}
        >
          <AlertDescription>
            {(validationResult as { valid: boolean }).valid
              ? `Valid DAG! ${((validationResult as { stats?: { total_nodes?: number } }).stats?.total_nodes) || 0} nodes, execution order ready.`
              : `Invalid: ${((validationResult as { errors?: string[] }).errors || []).join('; ')}`}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-12 gap-4">
        {/* Node Palette */}
        <div className="col-span-12 md:col-span-2">
          <div className="surface-card p-4">
            <h3 className="text-sm font-semibold text-[var(--text-high)] mb-2">Add Nodes</h3>
            <div className="flex flex-col gap-1">
              {NODE_TYPES.map((nt) => (
                <button
                  key={nt.type}
                  onClick={() => addNode(nt)}
                  className="flex items-center gap-1.5 px-2 py-1.5 rounded text-sm text-left cursor-pointer hover:opacity-80 transition-opacity"
                  style={{ backgroundColor: nt.color }}
                >
                  <Plus className="h-3 w-3 shrink-0" />
                  {nt.icon} {nt.label}
                </button>
              ))}
            </div>
            <Separator className="my-4" />
            <p className="text-xs text-[var(--text-low)]">
              Click a node then click &quot;Connect&quot; and click another node to create an edge.
            </p>
          </div>
        </div>

        {/* Canvas */}
        <div className="col-span-12 md:col-span-10 space-y-4">
          <div className="surface-card p-0 min-h-[500px] relative overflow-hidden">
            <div className="h-[500px] relative">
              {nodes.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-[var(--text-mid)]">Add nodes from the palette to start building your pipeline</p>
                </div>
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
                <div
                  key={node.id}
                  onClick={() => handleNodeClick(node.id)}
                  className="absolute w-[180px] h-[50px] flex items-center justify-between px-3 py-1 rounded-lg cursor-pointer shadow-sm hover:shadow-md transition-shadow"
                  style={{
                    left: node.x, top: node.y,
                    backgroundColor: node.color,
                    border: selectedNode === node.id ? '3px solid #1976d2' : connectFrom === node.id ? '3px solid #f57c00' : '1px solid #ccc',
                  }}
                >
                  <span className="text-sm font-bold truncate">
                    {node.icon} {node.label}
                  </span>
                  <div className="flex gap-0.5">
                    <button
                      type="button"
                      title="Connect node"
                      className="p-0.5 text-xs hover:opacity-80"
                      onClick={(e) => { e.stopPropagation(); setConnectFrom(connectFrom === node.id ? null : node.id); }}
                      style={{ color: connectFrom === node.id ? '#f57c00' : '#666' }}
                    >
                      {connectFrom === node.id ? '⬤' : '→'}
                    </button>
                    <button
                      type="button"
                      title="Remove node"
                      className="p-0.5 hover:opacity-80"
                      onClick={(e) => { e.stopPropagation(); removeNode(node.id); }}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-[var(--text-mid)]" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pipeline Summary */}
          {nodes.length > 0 && (
            <div className="surface-card p-5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-semibold text-[var(--text-high)]">Flow:</span>
                {nodes.map((n, i) => (
                  <div key={n.id} className="flex items-center gap-1">
                    <Badge variant="secondary" className="text-xs" style={{ backgroundColor: n.color, color: '#000' }}>
                      {n.icon} {n.label}
                    </Badge>
                    {i < nodes.length - 1 && <span className="text-[var(--text-low)]">→</span>}
                  </div>
                ))}
                <Badge variant="outline" className="ml-auto text-xs">
                  {nodes.length} nodes, {edges.length} edges
                </Badge>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
