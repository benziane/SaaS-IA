'use client';

import { useRef, useState } from 'react';
import {
  FileText, Upload, Sparkles, Trash2, Send, Download, GitCompareArrows,
  Key, Table2, Loader2,
} from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';

import {
  useComparePDFs,
  useDeletePDF,
  useExportPDF,
  useExtractKeywords,
  useExtractTables,
  usePDF,
  usePDFs,
  useQueryPDF,
  useSummarizePDF,
  useUploadPDF,
} from '@/features/pdf-processor/hooks/usePDFProcessor';

const STATUS_VARIANTS: Record<string, 'default' | 'secondary' | 'success' | 'destructive'> = {
  uploading: 'default',
  processing: 'secondary',
  ready: 'success',
  failed: 'destructive',
};

export default function PDFPage() {
  const { data: pdfs, isLoading } = usePDFs();
  const uploadMutation = useUploadPDF();
  const deleteMutation = useDeletePDF();

  const [activePDF, setActivePDF] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [tab, setTab] = useState('summary');
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: pdfDetail } = usePDF(activePDF);
  const queryMutation = useQueryPDF(activePDF || '');
  const summarizeMutation = useSummarizePDF(activePDF || '');
  const keywordsMutation = useExtractKeywords(activePDF || '');
  const exportMutation = useExportPDF(activePDF || '');
  const tablesMutation = useExtractTables(activePDF || '');
  const compareMutation = useComparePDFs();

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleQuery = () => {
    if (!question.trim() || !activePDF) return;
    queryMutation.mutate(question);
    setQuestion('');
  };

  const toggleCompare = (id: string) => {
    setSelectedForCompare((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 5 ? [...prev, id] : prev
    );
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-[var(--text-high)] flex items-center gap-2">
          <FileText className="h-8 w-8 text-red-500" /> PDF Processor
        </h1>
        <p className="text-sm text-[var(--text-mid)]">
          Upload PDFs, get AI summaries, ask questions (RAG), extract tables, and export
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left panel: PDF list */}
        <div className="md:col-span-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-[var(--text-high)]">Your PDFs</h3>
                <Button
                  size="sm"
                  onClick={() => fileRef.current?.click()}
                  disabled={uploadMutation.isPending}
                >
                  <Upload className="h-3.5 w-3.5 mr-1" />
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </Button>
                <input ref={fileRef} type="file" accept=".pdf" hidden onChange={handleUpload} />
              </div>

              {uploadMutation.isError && (
                <Alert variant="destructive" className="mb-2">
                  <AlertDescription>{uploadMutation.error?.message || 'Upload failed'}</AlertDescription>
                </Alert>
              )}

              {isLoading ? (
                <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
              ) : !pdfs?.length ? (
                <p className="text-sm text-[var(--text-mid)]">
                  No PDFs uploaded yet. Upload your first PDF to get started.
                </p>
              ) : (
                pdfs.map((pdf) => (
                  <Card
                    key={pdf.id}
                    className={`mb-2 cursor-pointer border border-[var(--border)] transition-colors ${
                      activePDF === pdf.id ? 'bg-[var(--bg-surface)]' : ''
                    }`}
                    onClick={() => { setActivePDF(pdf.id); setTab('summary'); }}
                  >
                    <CardContent className="py-2 px-3">
                      <div className="flex justify-between items-center">
                        <div className="overflow-hidden">
                          <p className="text-sm font-bold text-[var(--text-high)] truncate">{pdf.filename}</p>
                          <span className="text-xs text-[var(--text-mid)]">
                            {pdf.num_pages} pages | {pdf.file_size_kb} KB
                          </span>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <Badge variant={STATUS_VARIANTS[pdf.status] || 'default'}>{pdf.status}</Badge>
                          <button
                            type="button"
                            title="Compare"
                            className={`p-1 rounded hover:bg-[var(--bg-hover)] ${selectedForCompare.includes(pdf.id) ? 'text-[var(--accent)]' : 'text-[var(--text-mid)]'}`}
                            onClick={(e) => { e.stopPropagation(); toggleCompare(pdf.id); }}
                          >
                            <GitCompareArrows className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            title="Delete"
                            className="p-1 rounded hover:bg-red-100 text-red-500"
                            onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(pdf.id); }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}

              {selectedForCompare.length >= 2 && (
                <Button
                  variant="outline"
                  className="w-full mt-2"
                  onClick={() => compareMutation.mutate({ pdfIds: selectedForCompare })}
                  disabled={compareMutation.isPending}
                >
                  <GitCompareArrows className="h-4 w-4 mr-2" />
                  Compare {selectedForCompare.length} PDFs
                </Button>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right panel: PDF details */}
        <div className="md:col-span-8">
          {!activePDF ? (
            <Card>
              <CardContent className="text-center py-12 px-6">
                <p className="text-[var(--text-mid)]">
                  Select a PDF from the list to view details, generate summaries, or ask questions.
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">
                  {pdfDetail?.filename || 'Loading...'}
                </h3>

                <Tabs value={tab} onValueChange={setTab} className="mb-4">
                  <TabsList>
                    <TabsTrigger value="summary">Summary</TabsTrigger>
                    <TabsTrigger value="rag">Ask (RAG)</TabsTrigger>
                    <TabsTrigger value="pages">Pages</TabsTrigger>
                    <TabsTrigger value="export">Export</TabsTrigger>
                  </TabsList>

                  {/* Summary tab */}
                  <TabsContent value="summary">
                    <div className="flex gap-2 mb-4 flex-wrap">
                      {['executive', 'detailed', 'bullet_points'].map((style) => (
                        <Button
                          key={style}
                          variant="outline"
                          size="sm"
                          onClick={() => summarizeMutation.mutate(style)}
                          disabled={summarizeMutation.isPending}
                        >
                          <Sparkles className="h-3.5 w-3.5 mr-1" />
                          {style.replace('_', ' ')}
                        </Button>
                      ))}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => keywordsMutation.mutate()}
                        disabled={keywordsMutation.isPending}
                      >
                        <Key className="h-3.5 w-3.5 mr-1" /> Keywords
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => tablesMutation.mutate()}
                        disabled={tablesMutation.isPending}
                      >
                        <Table2 className="h-3.5 w-3.5 mr-1" /> Tables
                      </Button>
                    </div>

                    {summarizeMutation.isPending && <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />}
                    {summarizeMutation.data && (
                      <div className="mt-2">
                        <p className="text-sm font-medium text-[var(--text-high)] mb-1">
                          Summary ({summarizeMutation.data.style})
                        </p>
                        <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap">
                          {summarizeMutation.data.summary}
                        </p>
                      </div>
                    )}

                    {pdfDetail?.summary && !summarizeMutation.data && (
                      <div className="mt-2">
                        <p className="text-sm font-medium text-[var(--text-high)] mb-1">Previous Summary</p>
                        <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap">{pdfDetail.summary}</p>
                      </div>
                    )}

                    {keywordsMutation.data && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-[var(--text-high)] mb-1">Keywords</p>
                        <div className="flex gap-1 flex-wrap">
                          {keywordsMutation.data.keywords.map((kw, i) => (
                            <Badge key={i} variant="outline">{kw}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {(pdfDetail?.keywords?.length ?? 0) > 0 && !keywordsMutation.data && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-[var(--text-high)] mb-1">Keywords</p>
                        <div className="flex gap-1 flex-wrap">
                          {pdfDetail?.keywords?.map((kw, i) => (
                            <Badge key={i} variant="outline">{kw}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {tablesMutation.data && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-[var(--text-high)] mb-1">
                          Tables ({tablesMutation.data.total} found)
                        </p>
                        {tablesMutation.data.tables.map((t, i) => (
                          <div key={i} className="mb-1">
                            <span className="text-xs text-[var(--text-mid)]">
                              Page {t.page}, Table {t.table_index + 1} ({t.row_count} rows)
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>

                  {/* RAG Query tab */}
                  <TabsContent value="rag">
                    <div className="flex gap-2 mb-4">
                      <Input
                        placeholder="Ask a question about this PDF..."
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
                      />
                      <button
                        type="button"
                        title="Send"
                        className="p-2 rounded text-[var(--accent)] hover:bg-[var(--bg-hover)] disabled:opacity-40"
                        onClick={handleQuery}
                        disabled={queryMutation.isPending || !question.trim()}
                      >
                        <Send className="h-5 w-5" />
                      </button>
                    </div>

                    {queryMutation.isPending && <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />}
                    {queryMutation.data && (
                      <div>
                        <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap mb-2">
                          {queryMutation.data.answer}
                        </p>
                        <span className="text-xs text-[var(--text-mid)]">
                          Confidence: {(queryMutation.data.confidence * 100).toFixed(1)}% |{' '}
                          {queryMutation.data.sources.length} source(s)
                        </span>
                        {queryMutation.data.sources.length > 0 && (
                          <div className="mt-2">
                            <Separator className="my-2" />
                            <p className="text-sm font-medium text-[var(--text-high)] mb-1">Sources</p>
                            {queryMutation.data.sources.map((s, i) => (
                              <Card key={i} className="mb-1 border border-[var(--border)] p-2">
                                <span className="text-xs text-[var(--text-mid)]">
                                  Chunk {s.chunk_index} (relevance: {(s.relevance * 100).toFixed(1)}%)
                                </span>
                                <p className="text-[0.8rem] text-[var(--text-high)]">
                                  {s.text}
                                </p>
                              </Card>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </TabsContent>

                  {/* Pages tab */}
                  <TabsContent value="pages">
                    {pdfDetail?.pages?.length ? (
                      pdfDetail.pages.map((page) => (
                        <Card key={page.page_number} className="mb-2 border border-[var(--border)] p-3">
                          <p className="text-sm font-medium text-[var(--text-high)] mb-1">
                            Page {page.page_number}
                          </p>
                          <p className="text-[0.8rem] text-[var(--text-high)] whitespace-pre-wrap max-h-48 overflow-auto">
                            {page.text || '(no text)'}
                          </p>
                        </Card>
                      ))
                    ) : (
                      <p className="text-sm text-[var(--text-mid)]">No page content available.</p>
                    )}
                  </TabsContent>

                  {/* Export tab */}
                  <TabsContent value="export">
                    <div className="flex gap-2 mb-4">
                      {['markdown', 'txt', 'json'].map((fmt) => (
                        <Button
                          key={fmt}
                          variant="outline"
                          size="sm"
                          onClick={() => exportMutation.mutate(fmt)}
                          disabled={exportMutation.isPending}
                        >
                          <Download className="h-3.5 w-3.5 mr-1" /> {fmt.toUpperCase()}
                        </Button>
                      ))}
                    </div>

                    {exportMutation.isPending && <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />}
                    {exportMutation.data && (
                      <div>
                        <p className="text-sm font-medium text-[var(--text-high)] mb-1">
                          Exported as {exportMutation.data.format} ({exportMutation.data.filename})
                        </p>
                        <Textarea
                          className="font-mono text-xs"
                          rows={10}
                          value={exportMutation.data.content}
                          readOnly
                        />
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}

          {/* Compare results */}
          {compareMutation.data && (
            <Card className="mt-4">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-[var(--text-high)] mb-2">
                  Comparison ({compareMutation.data.comparison_type})
                </h3>
                <div className="flex gap-1 mb-2 flex-wrap">
                  {compareMutation.data.documents.map((d) => (
                    <Badge key={d.id}>{d.filename} ({d.num_pages}p)</Badge>
                  ))}
                </div>
                <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap">
                  {compareMutation.data.comparison}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
