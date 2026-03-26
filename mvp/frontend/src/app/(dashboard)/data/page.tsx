'use client';

import { useRef, useState } from 'react';
import { BarChart3, Loader2, Upload, Sparkles, Trash2, Send } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Separator } from '@/lib/design-hub/components/Separator';

import {
  useAnalyses, useAskData, useAutoAnalyze, useDatasets, useDeleteDataset, useUploadDataset,
} from '@/features/data-analyst/hooks/useDataAnalyst';

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive'> = {
  uploading: 'secondary', processing: 'default', ready: 'success', failed: 'destructive',
  pending: 'secondary', analyzing: 'default', completed: 'success',
};

export default function DataPage() {
  const { data: datasets, isLoading } = useDatasets();
  const uploadMutation = useUploadDataset();
  const deleteMutation = useDeleteDataset();

  const [activeDataset, setActiveDataset] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: analyses } = useAnalyses(activeDataset);
  const askMutation = useAskData(activeDataset || '');
  const autoMutation = useAutoAnalyze(activeDataset || '');

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleAsk = () => {
    if (!question.trim() || !activeDataset) return;
    askMutation.mutate({ question });
    setQuestion('');
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-high)] flex items-center gap-2">
          <BarChart3 className="h-7 w-7 text-[var(--accent)]" /> Data Analyst
        </h1>
        <p className="text-sm text-[var(--text-mid)]">
          Upload datasets, ask questions in natural language, get AI-powered insights and charts
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Datasets */}
        <div className="md:col-span-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-[var(--text-high)]">Datasets</h3>
                <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()}>
                  <Upload className="h-4 w-4 mr-1" /> Upload
                </Button>
              </div>
              <input type="file" ref={fileRef} accept=".csv,.json,.xlsx,.tsv" onChange={handleUpload} style={{ display: 'none' }} />
              {uploadMutation.isPending && (
                <Alert variant="info" className="mb-2">
                  <AlertDescription>Uploading...</AlertDescription>
                </Alert>
              )}

              {isLoading ? <Skeleton className="h-[200px] w-full" /> : !datasets?.length ? (
                <div className="text-center py-8">
                  <Upload className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                  <p className="text-sm text-[var(--text-mid)]">Upload a CSV, JSON, or Excel file</p>
                </div>
              ) : (
                datasets.map((d) => (
                  <Card
                    key={d.id}
                    className={`mb-2 border cursor-pointer transition-colors ${
                      activeDataset === d.id
                        ? 'border-[var(--accent)] bg-[var(--bg-elevated)]'
                        : 'border-[var(--border)] hover:bg-[var(--bg-elevated)]'
                    }`}
                    onClick={() => setActiveDataset(d.id)}
                  >
                    <CardContent className="py-3 px-4">
                      <div className="flex justify-between items-center">
                        <h4 className="text-sm font-medium text-[var(--text-high)]">{d.name}</h4>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-red-400 hover:text-red-300"
                          onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(d.id); }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="flex gap-1 mt-1">
                        <Badge variant="outline">{d.file_type}</Badge>
                        <Badge variant="outline">{d.row_count} rows</Badge>
                        <Badge variant="outline">{d.column_count} cols</Badge>
                        <Badge variant={STATUS_VARIANTS[d.status] || 'secondary'}>{d.status}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Analysis */}
        <div className="md:col-span-8">
          {activeDataset ? (
            <Card>
              <CardContent className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-[var(--text-high)]">Analysis</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => autoMutation.mutate('standard')}
                    disabled={autoMutation.isPending}
                  >
                    {autoMutation.isPending
                      ? <Loader2 className="h-4 w-4 animate-spin mr-1" />
                      : <Sparkles className="h-4 w-4 mr-1" />
                    }
                    Auto-Analyze
                  </Button>
                </div>

                <div className="flex gap-2 mb-6">
                  <Input
                    placeholder="Ask a question about your data..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleAsk(); }}
                    className="flex-1"
                  />
                  <Button
                    variant="default"
                    size="icon"
                    onClick={handleAsk}
                    disabled={!question.trim() || askMutation.isPending}
                  >
                    {askMutation.isPending
                      ? <Loader2 className="h-4 w-4 animate-spin" />
                      : <Send className="h-4 w-4" />
                    }
                  </Button>
                </div>

                <Separator className="mb-4" />

                {!analyses?.length ? (
                  <p className="text-sm text-[var(--text-mid)] text-center py-8">
                    Ask a question or click &ldquo;Auto-Analyze&rdquo; to get started
                  </p>
                ) : (
                  analyses.map((a) => (
                    <Card key={a.id} className="mb-4 border border-[var(--border)]">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-center mb-2">
                          <h4 className="text-sm font-medium text-[var(--accent)]">{a.question}</h4>
                          <Badge variant={STATUS_VARIANTS[a.status] || 'secondary'}>{a.status}</Badge>
                        </div>
                        {a.answer && (
                          <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap mb-2">{a.answer}</p>
                        )}
                        {a.insights.length > 0 && (
                          <div className="mb-2 space-y-1">
                            {a.insights.map((ins, i) => (
                              <Alert key={i} variant="info" className="py-2">
                                <AlertDescription className="text-xs">[{ins.category}] {ins.insight}</AlertDescription>
                              </Alert>
                            ))}
                          </div>
                        )}
                        {a.charts.length > 0 && (
                          <div className="flex gap-1 flex-wrap">
                            {a.charts.map((c, i) => (
                              <Badge key={i} variant="outline">{c.type}: {c.title}</Badge>
                            ))}
                          </div>
                        )}
                        {a.error && (
                          <Alert variant="destructive" className="mt-2">
                            <AlertDescription>{a.error}</AlertDescription>
                          </Alert>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-16 px-6">
                <BarChart3 className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-[var(--text-mid)]">Select a dataset to start analyzing</h3>
                <p className="text-sm text-[var(--text-mid)]">Upload CSV, JSON, or Excel files and ask questions in natural language</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
