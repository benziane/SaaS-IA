'use client';

import { useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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

const STATUS_VARIANTS: Record<string, 'outline' | 'default' | 'success' | 'destructive' | 'warning'> = {
  pending: 'outline',
  processing: 'default',
  indexed: 'success',
  failed: 'destructive',
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

  const { data: chunks, isLoading: chunksLoading } = useDocumentChunks(selectedDocId);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    if (fileRef.current) fileRef.current.value = '';
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
    <div className="p-6">
      <h1 className="text-2xl font-bold text-[var(--text-high)] mb-6">
        Knowledge Base
      </h1>

      {/* Upload Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
        </CardHeader>
        <CardContent>
          <input
            type="file"
            ref={fileRef}
            accept=".txt,.md,.csv"
            onChange={handleUpload}
            className="hidden"
          />
          <div className="flex items-center gap-3">
            <Button
              onClick={() => fileRef.current?.click()}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <><Loader2 className="h-4 w-4 animate-spin mr-2" />Uploading...</>
              ) : 'Upload File'}
            </Button>
            <span className="text-xs text-[var(--text-low)]">
              Supported: TXT, MD, CSV (max 10 MB)
            </span>
          </div>
          {uploadMutation.isError && (
            <Alert variant="destructive" className="mt-3">
              <AlertDescription>{uploadMutation.error?.message}</AlertDescription>
            </Alert>
          )}
          {uploadMutation.isSuccess && (
            <Alert variant="success" className="mt-3">
              <AlertDescription>Document uploaded and indexed.</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Documents List */}
        <Card className="h-full">
          <CardHeader>
            <CardTitle>Documents</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[200px] w-full" />
            ) : !documents?.length ? (
              <p className="text-sm text-[var(--text-low)]">
                No documents uploaded yet.
              </p>
            ) : (
              <ul className="space-y-1">
                {documents.map((doc) => (
                  <li key={doc.id} className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleViewChunks(doc.id, doc.filename)}
                      disabled={doc.status !== 'indexed'}
                      className="flex-1 flex items-center gap-2 rounded-[var(--radius-md,6px)] px-3 py-2 text-left text-sm text-[var(--text-high)] transition-colors hover:bg-[var(--bg-elevated)] disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <span className="flex-1">
                        <span className="block font-medium">{doc.filename}</span>
                        <span className="block text-xs text-[var(--text-low)]">
                          {doc.total_chunks} chunks — cliquer pour voir
                        </span>
                      </span>
                      <Badge variant={STATUS_VARIANTS[doc.status] || 'outline'}>
                        {doc.status}
                      </Badge>
                    </button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => deleteMutation.mutate(doc.id)}
                      disabled={deleteMutation.isPending}
                    >
                      Delete
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Search + Ask */}
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Search</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="Search your documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Button
                  variant="outline"
                  onClick={() => searchMutation.mutate(searchQuery)}
                  disabled={!searchQuery.trim() || searchMutation.isPending}
                >
                  Search
                </Button>
              </div>
              {searchMutation.data && (
                <div className="mt-4">
                  <p className="text-sm text-[var(--text-low)] mb-2">
                    {searchMutation.data.total} results
                  </p>
                  {searchMutation.data.results.map((r, i) => (
                    <div
                      key={i}
                      className="mb-2 rounded-[var(--radius-md,6px)] border border-[var(--border)] p-3"
                    >
                      <span className="text-xs text-[var(--accent)]">
                        {r.filename} (score: {r.score})
                      </span>
                      <p className="text-sm text-[var(--text-high)] mt-1">
                        {r.content.substring(0, 200)}...
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Ask a Question (RAG)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="Ask a question about your documents..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
                <Button
                  onClick={() => askMutation.mutate(question)}
                  disabled={!question.trim() || askMutation.isPending}
                >
                  {askMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Ask'}
                </Button>
              </div>
              {askMutation.data && (
                <div className="mt-4">
                  <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap mb-2">
                    {askMutation.data.answer}
                  </p>
                  <Separator className="my-2" />
                  <span className="text-xs text-[var(--text-low)]">
                    Provider: {askMutation.data.provider} | Sources: {askMutation.data.sources.length}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Document Chunks Viewer Modal */}
      <Dialog open={!!selectedDocId} onOpenChange={(open) => !open && handleCloseModal()}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedDocName}</DialogTitle>
            {chunks && (
              <p className="text-xs text-[var(--text-low)]">
                {chunks.length} chunk(s)
              </p>
            )}
          </DialogHeader>
          <div className="max-h-[70vh] overflow-y-auto">
            {chunksLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
              </div>
            ) : !chunks?.length ? (
              <p className="text-sm text-[var(--text-low)]">Aucun chunk disponible.</p>
            ) : (
              chunks.map((chunk) => (
                <div key={chunk.id} className="mb-4">
                  <span className="block text-xs text-[var(--text-low)] mb-1">
                    Chunk #{chunk.chunk_index + 1}
                  </span>
                  <div className="p-3 bg-[var(--bg-elevated)] rounded-[var(--radius-md,6px)] font-mono text-xs whitespace-pre-wrap break-words text-[var(--text-high)]">
                    {chunk.content}
                  </div>
                  {chunk.chunk_index < chunks.length - 1 && <Separator className="mt-4" />}
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
