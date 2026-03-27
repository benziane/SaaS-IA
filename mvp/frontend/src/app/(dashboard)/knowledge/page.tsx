'use client';

import { useRef, useState } from 'react';
import { Database, Upload, Search, MessageSquare, FileText, Trash2, Loader2, BookOpen } from 'lucide-react';

import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Separator } from '@/lib/design-hub/components/Separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/lib/design-hub/components/Dialog';

import {
  useAsk,
  useDeleteDocument,
  useDocumentChunks,
  useDocuments,
  useSearch,
  useUploadDocument,
} from '@/features/knowledge/hooks/useKnowledge';

const STATUS_DOT: Record<string, string> = {
  pending: 'bg-[var(--text-low)]',
  processing: 'bg-[var(--accent)] animate-pulse',
  indexed: 'bg-[var(--success)]',
  failed: 'bg-[var(--error)]',
};

export default function KnowledgePage() {
  const { data: documents, isLoading } = useDocuments();
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();
  const searchMutation = useSearch();
  const askMutation = useAsk();

  const fileRef = useRef<HTMLInputElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [question, setQuestion] = useState('');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedDocName, setSelectedDocName] = useState<string>('');
  const [dragOver, setDragOver] = useState(false);

  const { data: chunks, isLoading: chunksLoading } = useDocumentChunks(selectedDocId);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  const handleViewChunks = (id: string, name: string) => {
    setSelectedDocId(id);
    setSelectedDocName(name);
  };

  const handleCloseModal = () => {
    setSelectedDocId(null);
    setSelectedDocName('');
  };

  return (
    <div className="p-5 space-y-5 animate-enter">

      {/* Page Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <Database className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Knowledge Base</h1>
          <p className="text-xs text-[var(--text-mid)]">Upload, search, and ask questions about your documents</p>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        className={`surface-card p-6 transition-all duration-200 ${dragOver ? 'border-[var(--accent)] shadow-[0_0_0_2px_var(--accent-glow)]' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileRef}
          accept=".txt,.md,.csv"
          onChange={handleUpload}
          className="hidden"
        />
        <div className="flex flex-col items-center text-center gap-3 py-2">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${dragOver ? 'bg-[var(--accent)]/20 border border-[var(--accent)]/40' : 'bg-[var(--bg-elevated)] border border-[var(--border)]'}`}>
            <Upload className={`h-6 w-6 ${dragOver ? 'text-[var(--accent)]' : 'text-[var(--text-low)]'}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--text-high)]">
              {dragOver ? 'Drop to upload' : 'Upload Document'}
            </p>
            <p className="text-xs text-[var(--text-low)] mt-0.5">Drag & drop or click to browse · TXT, MD, CSV · max 10 MB</p>
          </div>
          <Button
            onClick={() => fileRef.current?.click()}
            disabled={uploadMutation.isPending}
            variant="outline"
            size="sm"
          >
            {uploadMutation.isPending ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />Uploading…</>
            ) : 'Browse Files'}
          </Button>
        </div>

        {uploadMutation.isError && (
          <Alert variant="destructive" className="mt-3">
            <AlertDescription>{uploadMutation.error?.message}</AlertDescription>
          </Alert>
        )}
        {uploadMutation.isSuccess && (
          <Alert variant="success" className="mt-3">
            <AlertDescription>Document uploaded and indexed successfully.</AlertDescription>
          </Alert>
        )}
      </div>

      {/* Documents + Search/Ask grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* Documents List */}
        <div className="surface-card">
          <div className="px-5 py-4 border-b border-[var(--border)] flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-[var(--accent)]" />
            <h2 className="text-sm font-semibold text-[var(--text-high)]">Documents</h2>
            {documents?.length ? (
              <span className="ml-auto text-xs text-[var(--text-low)]">{documents.length} files</span>
            ) : null}
          </div>
          <div className="p-4">
            {isLoading ? (
              <Skeleton className="h-[200px] w-full" />
            ) : !documents?.length ? (
              <div className="py-8 text-center">
                <FileText className="h-8 w-8 text-[var(--text-low)] mx-auto mb-2 opacity-40" />
                <p className="text-sm text-[var(--text-low)]">No documents uploaded yet.</p>
              </div>
            ) : (
              <ul className="space-y-1.5">
                {documents.map((doc) => (
                  <li key={doc.id} className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleViewChunks(doc.id, doc.filename)}
                      disabled={doc.status !== 'indexed'}
                      className="flex-1 flex items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors
                                 hover:bg-[var(--bg-elevated)] disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <div className="w-7 h-7 rounded-md flex items-center justify-center bg-[var(--bg-elevated)] shrink-0">
                        <FileText className="h-3.5 w-3.5 text-[var(--accent)]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-[var(--text-high)] truncate">{doc.filename}</p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[doc.status] || 'bg-[var(--text-low)]'}`} />
                          <span className="text-[10px] text-[var(--text-low)]">
                            {doc.status} · {doc.total_chunks} chunks
                          </span>
                        </div>
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteMutation.mutate(doc.id)}
                      disabled={deleteMutation.isPending}
                      className="p-1.5 rounded-md text-[var(--text-low)] hover:text-[var(--error)] hover:bg-[var(--error)]/10 transition-colors disabled:opacity-50"
                      title="Delete document"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Search + Ask */}
        <div className="flex flex-col gap-4">

          {/* Search */}
          <div className="surface-card">
            <div className="px-5 py-4 border-b border-[var(--border)] flex items-center gap-2">
              <Search className="h-4 w-4 text-[var(--accent)]" />
              <h2 className="text-sm font-semibold text-[var(--text-high)]">Search</h2>
            </div>
            <div className="p-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Search your documents…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && searchQuery.trim() && searchMutation.mutate(searchQuery)}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => searchMutation.mutate(searchQuery)}
                  disabled={!searchQuery.trim() || searchMutation.isPending}
                >
                  {searchMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Search'}
                </Button>
              </div>
              {searchMutation.data && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs text-[var(--text-low)]">{searchMutation.data.total} result{searchMutation.data.total !== 1 ? 's' : ''}</p>
                  {searchMutation.data.results.map((r, i) => (
                    <div key={i} className="rounded-lg border border-[var(--border)] p-3 hover:border-[var(--accent)]/30 transition-colors">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-medium text-[var(--accent)]">{r.filename}</span>
                        <span className="text-[10px] text-[var(--text-low)]">score {r.score.toFixed(2)}</span>
                      </div>
                      <p className="text-xs text-[var(--text-mid)] line-clamp-3">{r.content.substring(0, 200)}…</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* RAG Ask */}
          <div className="surface-card">
            <div className="px-5 py-4 border-b border-[var(--border)] flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-[var(--accent)]" />
              <h2 className="text-sm font-semibold text-[var(--text-high)]">Ask a Question <span className="text-[var(--text-low)] font-normal">RAG</span></h2>
            </div>
            <div className="p-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Ask a question about your documents…"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && question.trim() && askMutation.mutate(question)}
                />
                <Button
                  size="sm"
                  onClick={() => askMutation.mutate(question)}
                  disabled={!question.trim() || askMutation.isPending}
                >
                  {askMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Ask'}
                </Button>
              </div>
              {askMutation.data && (
                <div className="mt-3">
                  <div className="rounded-lg bg-[var(--accent)]/5 border border-[var(--accent)]/20 p-3.5 mb-3">
                    <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap leading-relaxed">
                      {askMutation.data.answer}
                    </p>
                  </div>
                  <p className="text-[10px] text-[var(--text-low)]">
                    Provider: <span className="text-[var(--accent)]">{askMutation.data.provider}</span>
                    {' · '}Sources: {askMutation.data.sources.length}
                  </p>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>

      {/* Document Chunks Viewer Modal */}
      <Dialog open={!!selectedDocId} onOpenChange={(open) => !open && handleCloseModal()}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-[var(--accent)]" />
              {selectedDocName}
            </DialogTitle>
            {chunks && (
              <p className="text-xs text-[var(--text-low)]">{chunks.length} chunk{chunks.length !== 1 ? 's' : ''}</p>
            )}
          </DialogHeader>
          <div className="max-h-[70vh] overflow-y-auto">
            {chunksLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
              </div>
            ) : !chunks?.length ? (
              <p className="text-sm text-[var(--text-low)] text-center py-6">No chunks available.</p>
            ) : (
              chunks.map((chunk, idx) => (
                <div key={chunk.id} className="mb-4">
                  <span className="block text-[10px] font-medium text-[var(--text-low)] uppercase tracking-wider mb-1.5">
                    Chunk #{chunk.chunk_index + 1}
                  </span>
                  <div className="p-3 bg-[var(--bg-elevated)] rounded-lg font-mono text-xs whitespace-pre-wrap break-words text-[var(--text-high)] leading-relaxed">
                    {chunk.content}
                  </div>
                  {idx < chunks.length - 1 && <Separator className="mt-4" />}
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>

    </div>
  );
}
