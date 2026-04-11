'use client';

import { useState, useCallback, useRef, useMemo, type DragEvent, type MouseEvent } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  Panel,
  Handle,
  Position,
  addEdge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
  type Node,
  type Edge,
  type Connection,
  type NodeTypes,
  type NodeProps,
  type ReactFlowInstance,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { GitBranch } from 'lucide-react';

import { useCreatePipeline } from '@/features/pipelines/hooks/usePipelines';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NodeField {
  key: string;
  label: string;
  type: 'text' | 'select' | 'textarea' | 'number';
  options?: string[];
  defaultValue?: string;
  placeholder?: string;
}

interface NodeTemplate {
  type: string;
  category: 'input' | 'ai' | 'data' | 'output';
  label: string;
  icon: string;
  description: string;
  fields: NodeField[];
}

type BuilderNodeData = {
  label: string;
  category: 'input' | 'ai' | 'data' | 'output';
  icon: string;
  templateType: string;
  fields: NodeField[];
  fieldValues: Record<string, string>;
};

type BuilderNode = Node<BuilderNodeData>;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CATEGORY_COLORS: Record<string, { bg: string; border: string; header: string; headerText: string; accent: string }> = {
  input: {
    bg: 'var(--bg-surface)',
    border: '#f97316',
    header: 'linear-gradient(135deg, #f97316 0%, #fb923c 100%)',
    headerText: '#ffffff',
    accent: '#f97316',
  },
  ai: {
    bg: '#0a0f1e',
    border: '#22d3ee',
    header: 'var(--bg-elevated)',
    headerText: '#22d3ee',
    accent: '#22d3ee',
  },
  data: {
    bg: 'var(--bg-surface)',
    border: '#3b82f6',
    header: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
    headerText: '#ffffff',
    accent: '#3b82f6',
  },
  output: {
    bg: 'var(--bg-surface)',
    border: '#22c55e',
    header: 'linear-gradient(135deg, #16a34a 0%, #22c55e 100%)',
    headerText: '#ffffff',
    accent: '#22c55e',
  },
};

const NODE_TEMPLATES: NodeTemplate[] = [
  // Input nodes
  {
    type: 'text_input',
    category: 'input',
    label: 'Text Input',
    icon: '✏',
    description: 'Raw text input for the pipeline',
    fields: [
      { key: 'text', label: 'Input Text', type: 'textarea', placeholder: 'Enter text to process...' },
    ],
  },
  {
    type: 'url_input',
    category: 'input',
    label: 'URL Input',
    icon: '\uD83C\uDF10',
    description: 'Fetch content from a URL',
    fields: [
      { key: 'url', label: 'URL', type: 'text', placeholder: 'https://example.com' },
      { key: 'extract_mode', label: 'Extract Mode', type: 'select', options: ['full_page', 'article', 'headings'], defaultValue: 'article' },
    ],
  },
  {
    type: 'file_input',
    category: 'input',
    label: 'File Upload',
    icon: '\uD83D\uDCC1',
    description: 'Upload a file for processing',
    fields: [
      { key: 'file_type', label: 'File Type', type: 'select', options: ['pdf', 'txt', 'csv', 'docx', 'audio'], defaultValue: 'pdf' },
      { key: 'file_path', label: 'File Path / ID', type: 'text', placeholder: 'Document ID or path' },
    ],
  },
  // AI nodes
  {
    type: 'generate',
    category: 'ai',
    label: 'AI Generate',
    icon: '✨',
    description: 'Generate text using AI models',
    fields: [
      { key: 'prompt', label: 'Prompt', type: 'textarea', placeholder: 'Write a prompt...' },
      { key: 'provider', label: 'Provider', type: 'select', options: ['gemini', 'claude', 'groq'], defaultValue: 'gemini' },
      { key: 'temperature', label: 'Temperature', type: 'text', defaultValue: '0.7', placeholder: '0.0 - 1.0' },
    ],
  },
  {
    type: 'analyze',
    category: 'ai',
    label: 'AI Analyze',
    icon: '\uD83D\uDD0D',
    description: 'Analyze text with AI (sentiment, entities, topics)',
    fields: [
      { key: 'analysis_type', label: 'Analysis Type', type: 'select', options: ['sentiment', 'entities', 'topics', 'classification', 'key_phrases'], defaultValue: 'sentiment' },
      { key: 'provider', label: 'Provider', type: 'select', options: ['gemini', 'claude', 'groq'], defaultValue: 'gemini' },
    ],
  },
  {
    type: 'translate',
    category: 'ai',
    label: 'Translate',
    icon: '\uD83C\uDF0D',
    description: 'Translate text between languages',
    fields: [
      { key: 'source_lang', label: 'Source Language', type: 'select', options: ['auto', 'en', 'fr', 'es', 'de', 'ar', 'zh', 'ja'], defaultValue: 'auto' },
      { key: 'target_lang', label: 'Target Language', type: 'select', options: ['en', 'fr', 'es', 'de', 'ar', 'zh', 'ja'], defaultValue: 'fr' },
      { key: 'provider', label: 'Provider', type: 'select', options: ['gemini', 'claude', 'groq'], defaultValue: 'gemini' },
    ],
  },
  {
    type: 'summarize',
    category: 'ai',
    label: 'Summarize',
    icon: '\uD83D\uDCDD',
    description: 'Summarize text to key points',
    fields: [
      { key: 'length', label: 'Summary Length', type: 'select', options: ['short', 'medium', 'detailed'], defaultValue: 'medium' },
      { key: 'format', label: 'Output Format', type: 'select', options: ['paragraph', 'bullets', 'numbered'], defaultValue: 'bullets' },
      { key: 'provider', label: 'Provider', type: 'select', options: ['gemini', 'claude', 'groq'], defaultValue: 'gemini' },
    ],
  },
  {
    type: 'transcription',
    category: 'ai',
    label: 'Transcribe',
    icon: '\uD83C\uDFA4',
    description: 'Transcribe audio/video to text',
    fields: [
      { key: 'language', label: 'Language', type: 'select', options: ['auto', 'en', 'fr', 'es', 'de', 'ar'], defaultValue: 'auto' },
      { key: 'engine', label: 'Engine', type: 'select', options: ['faster-whisper', 'assemblyai'], defaultValue: 'faster-whisper' },
    ],
  },
  // Data nodes
  {
    type: 'fetch_data',
    category: 'data',
    label: 'Fetch Data',
    icon: '\uD83D\uDCE5',
    description: 'Fetch data from knowledge base or API',
    fields: [
      { key: 'source', label: 'Source', type: 'select', options: ['knowledge_base', 'api', 'database'], defaultValue: 'knowledge_base' },
      { key: 'query', label: 'Query / Endpoint', type: 'text', placeholder: 'Search query or API endpoint' },
    ],
  },
  {
    type: 'transform',
    category: 'data',
    label: 'Transform',
    icon: '⚙️',
    description: 'Transform data (split, merge, format)',
    fields: [
      { key: 'operation', label: 'Operation', type: 'select', options: ['split_text', 'merge_texts', 'extract_json', 'format_template', 'chunk_text'], defaultValue: 'split_text' },
      { key: 'params', label: 'Parameters', type: 'text', placeholder: 'e.g. chunk_size=500' },
    ],
  },
  {
    type: 'filter',
    category: 'data',
    label: 'Filter',
    icon: '\uD83D\uDCCA',
    description: 'Filter and validate data',
    fields: [
      { key: 'condition', label: 'Condition', type: 'select', options: ['length_min', 'length_max', 'contains', 'not_empty', 'regex_match', 'score_above'], defaultValue: 'not_empty' },
      { key: 'value', label: 'Value', type: 'text', placeholder: 'Condition value' },
    ],
  },
  // Output nodes
  {
    type: 'publish',
    category: 'output',
    label: 'Publish',
    icon: '\uD83D\uDE80',
    description: 'Publish content to a destination',
    fields: [
      { key: 'destination', label: 'Destination', type: 'select', options: ['content_studio', 'api_endpoint', 'webhook', 'knowledge_base'], defaultValue: 'content_studio' },
      { key: 'format', label: 'Format', type: 'select', options: ['markdown', 'html', 'json', 'plain'], defaultValue: 'markdown' },
    ],
  },
  {
    type: 'export',
    category: 'output',
    label: 'Export',
    icon: '\uD83D\uDCBE',
    description: 'Export results to a file',
    fields: [
      { key: 'file_format', label: 'File Format', type: 'select', options: ['json', 'csv', 'txt', 'pdf', 'docx'], defaultValue: 'json' },
      { key: 'filename', label: 'Filename', type: 'text', placeholder: 'output_results', defaultValue: 'pipeline_output' },
    ],
  },
  {
    type: 'notify',
    category: 'output',
    label: 'Notify',
    icon: '\uD83D\uDD14',
    description: 'Send notifications with results',
    fields: [
      { key: 'channel', label: 'Channel', type: 'select', options: ['email', 'webhook', 'slack', 'in_app'], defaultValue: 'in_app' },
      { key: 'message_template', label: 'Message', type: 'textarea', placeholder: 'Pipeline completed: {{result}}', defaultValue: 'Pipeline completed successfully.' },
    ],
  },
];

const CATEGORY_LABELS: Record<string, string> = {
  input: 'Input',
  ai: 'AI Operations',
  data: 'Data Processing',
  output: 'Output',
};

const CATEGORY_ORDER = ['input', 'ai', 'data', 'output'] as const;

// ---------------------------------------------------------------------------
// Custom Node Components
// ---------------------------------------------------------------------------

const DEFAULT_COLORS = {
  bg: 'var(--bg-surface)',
  border: '#6b7280',
  header: 'linear-gradient(135deg, #6b7280 0%, #9ca3af 100%)',
  headerText: '#ffffff',
  accent: '#6b7280',
};

function BaseNode({ data, selected, id }: NodeProps<BuilderNode>) {
  const colors = CATEGORY_COLORS[data.category] ?? DEFAULT_COLORS;

  return (
    <div
      style={{
        background: colors.bg,
        border: `2px solid ${selected ? colors.accent : 'var(--border)'}`,
        borderRadius: 12,
        minWidth: 220,
        maxWidth: 260,
        boxShadow: selected
          ? `0 0 20px ${colors.accent}40, 0 4px 24px rgba(0,0,0,0.5)`
          : '0 4px 16px rgba(0,0,0,0.4)',
        transition: 'border-color 0.2s, box-shadow 0.2s',
        overflow: 'hidden',
        fontSize: 13,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: colors.accent,
          border: `2px solid ${colors.bg}`,
          width: 12,
          height: 12,
          top: -6,
        }}
      />

      {/* Header */}
      <div
        style={{
          background: colors.header,
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span style={{ fontSize: 16 }}>{data.icon}</span>
        <span style={{ color: colors.headerText, fontWeight: 600, fontSize: 13, flex: 1 }}>
          {data.label}
        </span>
        <span
          style={{
            fontSize: 9,
            color: 'rgba(255,255,255,0.6)',
            background: 'rgba(0,0,0,0.2)',
            padding: '2px 6px',
            borderRadius: 4,
            textTransform: 'uppercase',
            letterSpacing: 0.5,
            fontWeight: 600,
          }}
        >
          {data.category}
        </span>
      </div>

      {/* Body - show compact field summary */}
      <div style={{ padding: '8px 12px' }}>
        {data.fields.slice(0, 3).map((field) => {
          const val = data.fieldValues[field.key] || field.defaultValue || '';
          return (
            <div
              key={field.key}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '3px 0',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <span style={{ color: '#9ca3af', fontSize: 11 }}>{field.label}</span>
              <span
                style={{
                  color: '#e5e7eb',
                  fontSize: 11,
                  maxWidth: 110,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  textAlign: 'right',
                }}
              >
                {val || '—'}
              </span>
            </div>
          );
        })}
        {data.fields.length > 3 && (
          <div style={{ color: '#6b7280', fontSize: 10, textAlign: 'center', marginTop: 4 }}>
            +{data.fields.length - 3} more fields
          </div>
        )}
        {data.fields.length === 0 && (
          <div style={{ color: '#6b7280', fontSize: 11, textAlign: 'center', padding: '4px 0' }}>
            No configuration needed
          </div>
        )}
      </div>

      {/* Node ID indicator */}
      <div
        style={{
          padding: '4px 12px 6px',
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        <span
          style={{
            fontSize: 9,
            color: '#4b5563',
            fontFamily: 'monospace',
          }}
        >
          {id}
        </span>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: colors.accent,
          border: `2px solid ${colors.bg}`,
          width: 12,
          height: 12,
          bottom: -6,
        }}
      />
    </div>
  );
}

function InputNode(props: NodeProps<BuilderNode>) {
  return <BaseNode {...props} />;
}

function AINode(props: NodeProps<BuilderNode>) {
  return <BaseNode {...props} />;
}

function DataNode(props: NodeProps<BuilderNode>) {
  return <BaseNode {...props} />;
}

function OutputNode(props: NodeProps<BuilderNode>) {
  return <BaseNode {...props} />;
}

// ---------------------------------------------------------------------------
// Sidebar Node Template Component
// ---------------------------------------------------------------------------

function SidebarNodeItem({ template }: { template: NodeTemplate }) {
  const colors = CATEGORY_COLORS[template.category] ?? DEFAULT_COLORS;

  const onDragStart = (event: DragEvent<HTMLDivElement>) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(template));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      draggable
      onDragStart={onDragStart}
      style={{
        background: '#1a1825',
        border: `1px solid var(--border)`,
        borderLeft: `3px solid ${colors.accent}`,
        borderRadius: 8,
        padding: '8px 10px',
        cursor: 'grab',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        transition: 'all 0.15s',
        marginBottom: 6,
      }}
      className="sidebar-node-item"
      title={template.description}
    >
      <span style={{ fontSize: 16, flexShrink: 0 }}>{template.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ color: '#e5e7eb', fontSize: 12, fontWeight: 600 }}>{template.label}</div>
        <div
          style={{
            color: '#6b7280',
            fontSize: 10,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {template.description}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Properties Panel
// ---------------------------------------------------------------------------

function PropertiesPanel({
  node,
  onUpdate,
  onDelete,
}: {
  node: BuilderNode | null;
  onUpdate: (nodeId: string, fieldValues: Record<string, string>, label: string) => void;
  onDelete: (nodeId: string) => void;
}) {
  if (!node) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: '#6b7280',
          padding: 20,
          textAlign: 'center',
        }}
      >
        <span style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>{'👈'}</span>
        <div style={{ fontSize: 13, fontWeight: 500 }}>Select a node</div>
        <div style={{ fontSize: 11, marginTop: 4, color: '#4b5563' }}>
          Click on a node in the canvas to edit its properties
        </div>
      </div>
    );
  }

  const colors = CATEGORY_COLORS[node.data.category] ?? DEFAULT_COLORS;
  const [localValues, setLocalValues] = useState<Record<string, string>>(node.data.fieldValues);
  const [localLabel, setLocalLabel] = useState(node.data.label);

  // Sync when selected node changes
  const nodeIdRef = useRef(node.id);
  if (nodeIdRef.current !== node.id) {
    nodeIdRef.current = node.id;
    setLocalValues(node.data.fieldValues);
    setLocalLabel(node.data.label);
  }

  const handleFieldChange = (key: string, value: string) => {
    const updated = { ...localValues, [key]: value };
    setLocalValues(updated);
    onUpdate(node.id, updated, localLabel);
  };

  const handleLabelChange = (value: string) => {
    setLocalLabel(value);
    onUpdate(node.id, localValues, value);
  };

  return (
    <div style={{ padding: 16, overflowY: 'auto', height: '100%' }}>
      {/* Node header */}
      <div
        style={{
          background: colors.header,
          borderRadius: 8,
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 16,
        }}
      >
        <span style={{ fontSize: 20 }}>{node.data.icon}</span>
        <div>
          <div style={{ color: '#fff', fontWeight: 600, fontSize: 14 }}>{node.data.label}</div>
          <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 11 }}>{node.data.templateType}</div>
        </div>
      </div>

      {/* Node label */}
      <div style={{ marginBottom: 14 }}>
        <label style={{ color: '#9ca3af', fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Node Label
        </label>
        <input
          type="text"
          value={localLabel}
          onChange={(e) => handleLabelChange(e.target.value)}
          style={{
            width: '100%',
            background: '#1a1825',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '7px 10px',
            color: '#e5e7eb',
            fontSize: 12,
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Node ID */}
      <div style={{ marginBottom: 14 }}>
        <label style={{ color: '#9ca3af', fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Node ID
        </label>
        <div
          style={{
            background: '#1a1825',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '7px 10px',
            color: '#6b7280',
            fontSize: 11,
            fontFamily: 'monospace',
          }}
        >
          {node.id}
        </div>
      </div>

      {/* Fields */}
      {node.data.fields.map((field) => (
        <div key={field.key} style={{ marginBottom: 14 }}>
          <label
            style={{
              color: '#9ca3af',
              fontSize: 11,
              fontWeight: 600,
              display: 'block',
              marginBottom: 4,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            {field.label}
          </label>
          {field.type === 'select' ? (
            <select
              value={localValues[field.key] || field.defaultValue || ''}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
              style={{
                width: '100%',
                background: '#1a1825',
                border: '1px solid var(--border)',
                borderRadius: 6,
                padding: '7px 10px',
                color: '#e5e7eb',
                fontSize: 12,
                outline: 'none',
                cursor: 'pointer',
                boxSizing: 'border-box',
              }}
            >
              {field.options?.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          ) : field.type === 'textarea' ? (
            <textarea
              value={localValues[field.key] || ''}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              rows={3}
              style={{
                width: '100%',
                background: '#1a1825',
                border: '1px solid var(--border)',
                borderRadius: 6,
                padding: '7px 10px',
                color: '#e5e7eb',
                fontSize: 12,
                outline: 'none',
                resize: 'vertical',
                fontFamily: 'inherit',
                boxSizing: 'border-box',
              }}
            />
          ) : (
            <input
              type={field.type === 'number' ? 'number' : 'text'}
              value={localValues[field.key] || ''}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              style={{
                width: '100%',
                background: '#1a1825',
                border: '1px solid var(--border)',
                borderRadius: 6,
                padding: '7px 10px',
                color: '#e5e7eb',
                fontSize: 12,
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          )}
        </div>
      ))}

      {/* Delete button */}
      <button
        onClick={() => onDelete(node.id)}
        style={{
          width: '100%',
          marginTop: 8,
          padding: '8px 0',
          background: 'rgba(239,68,68,0.1)',
          border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 6,
          color: '#ef4444',
          fontSize: 12,
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.15s',
        }}
      >
        Delete Node
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

let nodeIdCounter = 0;
function getNextNodeId() {
  nodeIdCounter += 1;
  return `node_${nodeIdCounter}`;
}

// Default pipeline to display on load
const defaultNodes: BuilderNode[] = [
  {
    id: 'node_1',
    type: 'InputNode',
    position: { x: 300, y: 40 },
    data: {
      label: 'Text Input',
      category: 'input',
      icon: '✏',
      templateType: 'text_input',
      fields: NODE_TEMPLATES.find((t) => t.type === 'text_input')!.fields,
      fieldValues: { text: 'Enter your text here...' },
    },
  },
  {
    id: 'node_2',
    type: 'AINode',
    position: { x: 300, y: 220 },
    data: {
      label: 'Summarize',
      category: 'ai',
      icon: '\uD83D\uDCDD',
      templateType: 'summarize',
      fields: NODE_TEMPLATES.find((t) => t.type === 'summarize')!.fields,
      fieldValues: { length: 'medium', format: 'bullets', provider: 'gemini' },
    },
  },
  {
    id: 'node_3',
    type: 'AINode',
    position: { x: 300, y: 420 },
    data: {
      label: 'Translate',
      category: 'ai',
      icon: '\uD83C\uDF0D',
      templateType: 'translate',
      fields: NODE_TEMPLATES.find((t) => t.type === 'translate')!.fields,
      fieldValues: { source_lang: 'auto', target_lang: 'fr', provider: 'gemini' },
    },
  },
  {
    id: 'node_4',
    type: 'OutputNode',
    position: { x: 300, y: 620 },
    data: {
      label: 'Export',
      category: 'output',
      icon: '\uD83D\uDCBE',
      templateType: 'export',
      fields: NODE_TEMPLATES.find((t) => t.type === 'export')!.fields,
      fieldValues: { file_format: 'json', filename: 'pipeline_output' },
    },
  },
];

const defaultEdges: Edge[] = [
  {
    id: 'e1-2',
    source: 'node_1',
    target: 'node_2',
    animated: true,
    style: { stroke: '#22d3ee', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#22d3ee' },
  },
  {
    id: 'e2-3',
    source: 'node_2',
    target: 'node_3',
    animated: true,
    style: { stroke: '#22d3ee', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#22d3ee' },
  },
  {
    id: 'e3-4',
    source: 'node_3',
    target: 'node_4',
    animated: true,
    style: { stroke: '#22c55e', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#22c55e' },
  },
];

nodeIdCounter = 4;

export default function PipelineBuilderPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<BuilderNode>(defaultNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(defaultEdges);
  const [selectedNode, setSelectedNode] = useState<BuilderNode | null>(null);
  const [sidebarSearch, setSidebarSearch] = useState('');
  const [pipelineName, setPipelineName] = useState('');
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [history, setHistory] = useState<{ nodes: BuilderNode[]; edges: Edge[] }[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [propertiesCollapsed, setPropertiesCollapsed] = useState(false);

  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const reactFlowInstance = useRef<ReactFlowInstance<BuilderNode> | null>(null);

  const createMutation = useCreatePipeline();

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      InputNode,
      AINode,
      DataNode,
      OutputNode,
    }),
    []
  );

  // Push to undo history
  const pushHistory = useCallback(() => {
    setHistory((prev) => [...prev.slice(-30), { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }]);
  }, [nodes, edges]);

  // Undo
  const handleUndo = useCallback(() => {
    setHistory((prev) => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1]!;
      setNodes(last.nodes);
      setEdges(last.edges);
      setSelectedNode(null);
      return prev.slice(0, -1);
    });
  }, [setNodes, setEdges]);

  // Connection handler
  const onConnect = useCallback(
    (connection: Connection) => {
      pushHistory();
      const targetNode = nodes.find((n) => n.id === connection.target);
      const edgeColor = targetNode ? (CATEGORY_COLORS[targetNode.data.category]?.accent ?? '#6b7280') : '#6b7280';

      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            animated: true,
            style: { stroke: edgeColor, strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor },
          },
          eds
        )
      );
    },
    [setEdges, pushHistory, nodes]
  );

  // Drop handler
  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();

      const templateData = event.dataTransfer.getData('application/reactflow');
      if (!templateData || !reactFlowInstance.current) return;

      const template: NodeTemplate = JSON.parse(templateData);

      const position = reactFlowInstance.current.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      pushHistory();

      const nodeTypeMap: Record<string, string> = {
        input: 'InputNode',
        ai: 'AINode',
        data: 'DataNode',
        output: 'OutputNode',
      };

      const defaultFieldValues: Record<string, string> = {};
      template.fields.forEach((f) => {
        if (f.defaultValue) defaultFieldValues[f.key] = f.defaultValue;
      });

      const newNode: BuilderNode = {
        id: getNextNodeId(),
        type: nodeTypeMap[template.category],
        position,
        data: {
          label: template.label,
          category: template.category,
          icon: template.icon,
          templateType: template.type,
          fields: template.fields,
          fieldValues: defaultFieldValues,
        },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes, pushHistory]
  );

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Node selection
  const onNodeClick = useCallback(
    (_event: MouseEvent, node: BuilderNode) => {
      setSelectedNode(node);
      setPropertiesCollapsed(false);
    },
    []
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Update node properties
  const handleNodeUpdate = useCallback(
    (nodeId: string, fieldValues: Record<string, string>, label: string) => {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id === nodeId) {
            return {
              ...n,
              data: { ...n.data, fieldValues, label },
            };
          }
          return n;
        })
      );
      setSelectedNode((prev) => {
        if (prev && prev.id === nodeId) {
          return { ...prev, data: { ...prev.data, fieldValues, label } };
        }
        return prev;
      });
    },
    [setNodes]
  );

  // Delete node
  const handleNodeDelete = useCallback(
    (nodeId: string) => {
      pushHistory();
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
      setSelectedNode(null);
    },
    [setNodes, setEdges, pushHistory]
  );

  // Clear all
  const handleClear = useCallback(() => {
    pushHistory();
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setStatusMessage({ type: 'info', text: 'Canvas cleared.' });
    setTimeout(() => setStatusMessage(null), 2500);
  }, [setNodes, setEdges, pushHistory]);

  // Save pipeline
  const handleSave = useCallback(() => {
    if (nodes.length === 0) {
      setStatusMessage({ type: 'error', text: 'Cannot save an empty pipeline. Add some nodes first.' });
      setTimeout(() => setStatusMessage(null), 3000);
      return;
    }

    const name = pipelineName.trim() || `Pipeline ${new Date().toLocaleString()}`;

    // Build an ordered list of steps from the DAG using topological sort
    const adj: Record<string, string[]> = {};
    const deg: Record<string, number> = {};
    for (const n of nodes) {
      adj[n.id] = [];
      deg[n.id] = 0;
    }
    for (const e of edges) {
      (adj[e.source] ?? []).push(e.target);
      deg[e.target] = (deg[e.target] ?? 0) + 1;
    }

    // Kahn's algorithm
    const queue = Object.keys(deg).filter((k) => (deg[k] ?? 0) === 0);
    const sorted: string[] = [];
    while (queue.length > 0) {
      const current = queue.shift()!;
      sorted.push(current);
      for (const neighbor of adj[current] ?? []) {
        deg[neighbor] = (deg[neighbor] ?? 1) - 1;
        if ((deg[neighbor] ?? 0) === 0) queue.push(neighbor);
      }
    }

    const steps = sorted
      .map((nodeId, idx) => {
        const node = nodes.find((n) => n.id === nodeId);
        if (!node) return null;
        return {
          id: nodeId,
          type: node.data.templateType,
          config: {
            label: node.data.label,
            category: node.data.category,
            ...node.data.fieldValues,
            _position: node.position,
          },
          position: idx,
        };
      })
      .filter((s): s is NonNullable<typeof s> => s !== null);

    createMutation.mutate(
      { name, description: `Visual pipeline with ${nodes.length} nodes`, steps },
      {
        onSuccess: () => {
          setStatusMessage({ type: 'success', text: `Pipeline "${name}" saved successfully!` });
          setTimeout(() => setStatusMessage(null), 3000);
        },
        onError: (err) => {
          setStatusMessage({ type: 'error', text: `Failed to save: ${err.message}` });
          setTimeout(() => setStatusMessage(null), 4000);
        },
      }
    );
  }, [nodes, edges, pipelineName, createMutation]);

  // Run pipeline (just visual feedback for demo)
  const handleRun = useCallback(() => {
    if (nodes.length === 0) {
      setStatusMessage({ type: 'error', text: 'Add nodes to the pipeline before running.' });
      setTimeout(() => setStatusMessage(null), 3000);
      return;
    }
    setStatusMessage({ type: 'info', text: `Running pipeline with ${nodes.length} nodes...` });
    // Simulate pipeline execution animation
    const animateNodes = [...nodes];
    let idx = 0;
    const interval = setInterval(() => {
      if (idx >= animateNodes.length) {
        clearInterval(interval);
        setStatusMessage({ type: 'success', text: `Pipeline executed successfully! ${nodes.length} nodes processed.` });
        setTimeout(() => setStatusMessage(null), 3000);
        return;
      }
      const currentNode = animateNodes[idx];
      if (currentNode) {
        setStatusMessage({ type: 'info', text: `Processing: ${currentNode.data.label} (${idx + 1}/${animateNodes.length})...` });
      }
      idx++;
    }, 800);
  }, [nodes]);

  // Filter sidebar templates
  const filteredTemplates = useMemo(() => {
    if (!sidebarSearch.trim()) return NODE_TEMPLATES;
    const q = sidebarSearch.toLowerCase();
    return NODE_TEMPLATES.filter(
      (t) =>
        t.label.toLowerCase().includes(q) ||
        t.type.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.category.toLowerCase().includes(q)
    );
  }, [sidebarSearch]);

  const groupedTemplates = useMemo(() => {
    const groups: Record<string, NodeTemplate[]> = {};
    for (const cat of CATEGORY_ORDER) {
      const items = filteredTemplates.filter((t) => t.category === cat);
      if (items.length > 0) groups[cat] = items;
    }
    return groups;
  }, [filteredTemplates]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', background: 'var(--bg-app)', color: '#e5e7eb', overflow: 'hidden' }}>
      {/* Global styles for hover effects */}
      <style>{`
        .sidebar-node-item:hover {
          background: #252336 !important;
          border-color: #3d3b52 !important;
          transform: translateX(2px);
        }
        .toolbar-btn:hover {
          background: #252336 !important;
          border-color: #4b5563 !important;
        }
        .toolbar-btn:active {
          transform: scale(0.97);
        }
        .react-flow__node:focus {
          outline: none !important;
        }
        .react-flow__attribution {
          display: none !important;
        }
      `}</style>

      {/* Top Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '8px 16px',
          background: 'var(--bg-elevated)',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
          zIndex: 20,
        }}
      >
        {/* S+++ Page header */}
        <div className="flex items-center gap-3 mr-2">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
            <GitBranch className="h-4 w-4 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-[var(--text-high)] leading-none">Pipeline Builder</h1>
            <p className="text-[10px] text-[var(--text-mid)] leading-none mt-0.5">Advanced pipeline step builder</p>
          </div>
        </div>

        {/* Back link */}
        <a
          href="/pipelines"
          style={{
            color: '#9ca3af',
            fontSize: 12,
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            marginRight: 4,
          }}
        >
          ← Pipelines
        </a>

        <div style={{ width: 1, height: 24, background: 'var(--border)', marginRight: 4 }} />

        {/* Pipeline name input */}
        <input
          type="text"
          value={pipelineName}
          onChange={(e) => setPipelineName(e.target.value)}
          placeholder="Untitled Pipeline"
          style={{
            background: '#1a1825',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '6px 10px',
            color: '#e5e7eb',
            fontSize: 13,
            fontWeight: 600,
            width: 220,
            outline: 'none',
          }}
        />

        <div style={{ flex: 1 }} />

        {/* Node count */}
        <span style={{ color: '#6b7280', fontSize: 11, marginRight: 4 }}>
          {nodes.length} nodes &middot; {edges.length} connections
        </span>

        <div style={{ width: 1, height: 24, background: 'var(--border)', margin: '0 4px' }} />

        {/* Buttons */}
        <button
          className="toolbar-btn"
          onClick={handleUndo}
          disabled={history.length === 0}
          style={{
            background: '#1a1825',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '6px 12px',
            color: history.length === 0 ? '#4b5563' : '#e5e7eb',
            fontSize: 12,
            cursor: history.length === 0 ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            transition: 'all 0.15s',
          }}
        >
          ↩ Undo
        </button>

        <button
          className="toolbar-btn"
          onClick={handleClear}
          style={{
            background: '#1a1825',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '6px 12px',
            color: '#e5e7eb',
            fontSize: 12,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            transition: 'all 0.15s',
          }}
        >
          🗑 Clear
        </button>

        <button
          className="toolbar-btn"
          onClick={handleRun}
          style={{
            background: 'rgba(34,197,94,0.15)',
            border: '1px solid rgba(34,197,94,0.3)',
            borderRadius: 6,
            padding: '6px 14px',
            color: '#22c55e',
            fontSize: 12,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            transition: 'all 0.15s',
          }}
        >
          ▶ Run
        </button>

        <button
          className="toolbar-btn"
          onClick={handleSave}
          disabled={createMutation.isPending}
          style={{
            background: 'var(--accent)',
            border: 'none',
            borderRadius: 6,
            padding: '6px 16px',
            color: '#000000',
            fontSize: 12,
            fontWeight: 600,
            cursor: createMutation.isPending ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            transition: 'all 0.15s',
            opacity: createMutation.isPending ? 0.7 : 1,
          }}
        >
          {createMutation.isPending ? 'Saving...' : '💾 Save Pipeline'}
        </button>
      </div>

      {/* Status message bar */}
      {statusMessage && (
        <div
          style={{
            padding: '6px 16px',
            fontSize: 12,
            fontWeight: 500,
            flexShrink: 0,
            background:
              statusMessage.type === 'success'
                ? 'rgba(34,197,94,0.12)'
                : statusMessage.type === 'error'
                  ? 'rgba(239,68,68,0.12)'
                  : 'rgba(59,130,246,0.12)',
            color:
              statusMessage.type === 'success'
                ? '#22c55e'
                : statusMessage.type === 'error'
                  ? '#ef4444'
                  : '#3b82f6',
            borderBottom: `1px solid ${
              statusMessage.type === 'success'
                ? 'rgba(34,197,94,0.2)'
                : statusMessage.type === 'error'
                  ? 'rgba(239,68,68,0.2)'
                  : 'rgba(59,130,246,0.2)'
            }`,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span>
            {statusMessage.type === 'success' ? '✔' : statusMessage.type === 'error' ? '✖' : 'ℹ'}
          </span>
          {statusMessage.text}
          <button
            onClick={() => setStatusMessage(null)}
            style={{
              marginLeft: 'auto',
              background: 'none',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              fontSize: 14,
              opacity: 0.6,
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Main content area */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Sidebar */}
        <div
          style={{
            width: sidebarCollapsed ? 42 : 260,
            background: 'var(--bg-elevated)',
            borderRight: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            flexShrink: 0,
            transition: 'width 0.2s',
            overflow: 'hidden',
          }}
        >
          {/* Sidebar toggle */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: '1px solid var(--border)',
              color: '#9ca3af',
              padding: '8px',
              cursor: 'pointer',
              fontSize: 14,
              textAlign: sidebarCollapsed ? 'center' : 'right',
            }}
          >
            {sidebarCollapsed ? '»' : '«'}
          </button>

          {!sidebarCollapsed && (
            <>
              {/* Sidebar header */}
              <div style={{ padding: '12px 14px 8px' }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#e5e7eb', marginBottom: 8 }}>
                  Node Library
                </div>
                <input
                  type="text"
                  value={sidebarSearch}
                  onChange={(e) => setSidebarSearch(e.target.value)}
                  placeholder="Search nodes..."
                  style={{
                    width: '100%',
                    background: '#1a1825',
                    border: '1px solid var(--border)',
                    borderRadius: 6,
                    padding: '6px 10px',
                    color: '#e5e7eb',
                    fontSize: 12,
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              {/* Node templates */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '0 10px 10px' }}>
                {Object.entries(groupedTemplates).map(([category, templates]) => (
                  <div key={category} style={{ marginBottom: 12 }}>
                    <div
                      style={{
                        fontSize: 10,
                        fontWeight: 700,
                        color: CATEGORY_COLORS[category]?.accent ?? '#6b7280',
                        textTransform: 'uppercase',
                        letterSpacing: 1,
                        padding: '6px 4px 4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      <span
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          background: CATEGORY_COLORS[category]?.accent ?? '#6b7280',
                          display: 'inline-block',
                          flexShrink: 0,
                        }}
                      />
                      {CATEGORY_LABELS[category]}
                    </div>
                    {templates.map((template) => (
                      <SidebarNodeItem key={template.type} template={template} />
                    ))}
                  </div>
                ))}

                {filteredTemplates.length === 0 && (
                  <div style={{ color: '#6b7280', fontSize: 12, textAlign: 'center', padding: 20 }}>
                    No nodes match your search.
                  </div>
                )}

                {/* Instructions */}
                <div
                  style={{
                    marginTop: 16,
                    padding: '10px 12px',
                    background: '#1a1825',
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                  }}
                >
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#9ca3af', marginBottom: 6 }}>How to use</div>
                  <div style={{ fontSize: 10, color: '#6b7280', lineHeight: 1.6 }}>
                    <div><strong style={{ color: '#9ca3af' }}>Drag</strong> nodes from here onto the canvas</div>
                    <div><strong style={{ color: '#9ca3af' }}>Connect</strong> nodes by dragging from handles</div>
                    <div><strong style={{ color: '#9ca3af' }}>Click</strong> a node to edit its properties</div>
                    <div><strong style={{ color: '#9ca3af' }}>Delete</strong> key to remove selected nodes</div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Canvas */}
        <div ref={reactFlowWrapper} style={{ flex: 1, position: 'relative' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onInit={(instance) => {
              reactFlowInstance.current = instance as unknown as ReactFlowInstance<BuilderNode>;
            }}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            deleteKeyCode={['Backspace', 'Delete']}
            snapToGrid
            snapGrid={[16, 16]}
            defaultEdgeOptions={{
              animated: true,
              style: { stroke: '#6b7280', strokeWidth: 2 },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#6b7280' },
            }}
            style={{ background: 'var(--bg-app)' }}
            proOptions={{ hideAttribution: true }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="var(--border)" />
            <Controls
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 8,
              }}
            />
            <MiniMap
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 8,
              }}
              nodeColor={(node) => {
                const n = node as BuilderNode;
                return CATEGORY_COLORS[n.data?.category]?.accent || '#6b7280';
              }}
              maskColor="rgba(15, 14, 23, 0.8)"
            />

            {/* Canvas empty state */}
            {nodes.length === 0 && (
              <Panel position="top-center">
                <div
                  style={{
                    marginTop: 120,
                    textAlign: 'center',
                    color: '#4b5563',
                    userSelect: 'none',
                  }}
                >
                  <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.3 }}>⭐</div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#6b7280' }}>
                    Drag nodes here to build your pipeline
                  </div>
                  <div style={{ fontSize: 12, marginTop: 6 }}>
                    Choose from the node library on the left and connect them to create a flow
                  </div>
                </div>
              </Panel>
            )}
          </ReactFlow>
        </div>

        {/* Right Properties Panel */}
        <div
          style={{
            width: propertiesCollapsed ? 42 : 280,
            background: 'var(--bg-elevated)',
            borderLeft: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            flexShrink: 0,
            transition: 'width 0.2s',
            overflow: 'hidden',
          }}
        >
          {/* Properties toggle */}
          <button
            onClick={() => setPropertiesCollapsed(!propertiesCollapsed)}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: '1px solid var(--border)',
              color: '#9ca3af',
              padding: '8px',
              cursor: 'pointer',
              fontSize: 14,
              textAlign: propertiesCollapsed ? 'center' : 'left',
            }}
          >
            {propertiesCollapsed ? '«' : '»'}
          </button>

          {!propertiesCollapsed && (
            <>
              <div
                style={{
                  padding: '10px 14px 6px',
                  fontSize: 13,
                  fontWeight: 700,
                  color: '#e5e7eb',
                  borderBottom: '1px solid var(--border)',
                }}
              >
                Properties
              </div>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <PropertiesPanel
                  node={selectedNode}
                  onUpdate={handleNodeUpdate}
                  onDelete={handleNodeDelete}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
