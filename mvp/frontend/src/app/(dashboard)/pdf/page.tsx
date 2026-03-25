'use client';

import { useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import DownloadIcon from '@mui/icons-material/Download';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import KeyIcon from '@mui/icons-material/Key';
import TableChartIcon from '@mui/icons-material/TableChart';

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

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error'> = {
  uploading: 'default',
  processing: 'info',
  ready: 'success',
  failed: 'error',
};

export default function PDFPage() {
  const { data: pdfs, isLoading } = usePDFs();
  const uploadMutation = useUploadPDF();
  const deleteMutation = useDeletePDF();

  const [activePDF, setActivePDF] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [tab, setTab] = useState(0);
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
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PictureAsPdfIcon color="error" /> PDF Processor
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload PDFs, get AI summaries, ask questions (RAG), extract tables, and export
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Left panel: PDF list */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Your PDFs</Typography>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<UploadFileIcon />}
                  onClick={() => fileRef.current?.click()}
                  disabled={uploadMutation.isPending}
                >
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </Button>
                <input ref={fileRef} type="file" accept=".pdf" hidden onChange={handleUpload} />
              </Box>

              {uploadMutation.isError && (
                <Alert severity="error" sx={{ mb: 1 }}>
                  {uploadMutation.error?.message || 'Upload failed'}
                </Alert>
              )}

              {isLoading ? (
                <CircularProgress size={24} />
              ) : !pdfs?.length ? (
                <Typography variant="body2" color="text.secondary">
                  No PDFs uploaded yet. Upload your first PDF to get started.
                </Typography>
              ) : (
                pdfs.map((pdf) => (
                  <Card
                    key={pdf.id}
                    variant="outlined"
                    sx={{
                      mb: 1,
                      cursor: 'pointer',
                      bgcolor: activePDF === pdf.id ? 'action.selected' : undefined,
                    }}
                    onClick={() => { setActivePDF(pdf.id); setTab(0); }}
                  >
                    <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ overflow: 'hidden' }}>
                          <Typography variant="body2" noWrap fontWeight="bold">
                            {pdf.filename}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {pdf.num_pages} pages | {pdf.file_size_kb} KB
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Chip
                            label={pdf.status}
                            size="small"
                            color={STATUS_COLORS[pdf.status] || 'default'}
                          />
                          <IconButton
                            size="small"
                            onClick={(e) => { e.stopPropagation(); toggleCompare(pdf.id); }}
                            color={selectedForCompare.includes(pdf.id) ? 'primary' : 'default'}
                          >
                            <CompareArrowsIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(pdf.id); }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))
              )}

              {selectedForCompare.length >= 2 && (
                <Button
                  variant="outlined"
                  fullWidth
                  sx={{ mt: 1 }}
                  startIcon={<CompareArrowsIcon />}
                  onClick={() => compareMutation.mutate({ pdfIds: selectedForCompare })}
                  disabled={compareMutation.isPending}
                >
                  Compare {selectedForCompare.length} PDFs
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right panel: PDF details */}
        <Grid item xs={12} md={8}>
          {!activePDF ? (
            <Card>
              <CardContent>
                <Typography variant="body1" color="text.secondary" textAlign="center" py={6}>
                  Select a PDF from the list to view details, generate summaries, or ask questions.
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {pdfDetail?.filename || 'Loading...'}
                </Typography>

                <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
                  <Tab label="Summary" />
                  <Tab label="Ask (RAG)" />
                  <Tab label="Pages" />
                  <Tab label="Export" />
                </Tabs>

                {/* Summary tab */}
                {tab === 0 && (
                  <Box>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                      {['executive', 'detailed', 'bullet_points'].map((style) => (
                        <Button
                          key={style}
                          variant="outlined"
                          size="small"
                          startIcon={<AutoAwesomeIcon />}
                          onClick={() => summarizeMutation.mutate(style)}
                          disabled={summarizeMutation.isPending}
                        >
                          {style.replace('_', ' ')}
                        </Button>
                      ))}
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<KeyIcon />}
                        onClick={() => keywordsMutation.mutate()}
                        disabled={keywordsMutation.isPending}
                      >
                        Keywords
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<TableChartIcon />}
                        onClick={() => tablesMutation.mutate()}
                        disabled={tablesMutation.isPending}
                      >
                        Tables
                      </Button>
                    </Box>

                    {summarizeMutation.isPending && <CircularProgress size={24} />}
                    {summarizeMutation.data && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Summary ({summarizeMutation.data.style})
                        </Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {summarizeMutation.data.summary}
                        </Typography>
                      </Box>
                    )}

                    {pdfDetail?.summary && !summarizeMutation.data && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>Previous Summary</Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {pdfDetail.summary}
                        </Typography>
                      </Box>
                    )}

                    {keywordsMutation.data && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>Keywords</Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {keywordsMutation.data.keywords.map((kw, i) => (
                            <Chip key={i} label={kw} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}

                    {pdfDetail?.keywords?.length > 0 && !keywordsMutation.data && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>Keywords</Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {pdfDetail.keywords.map((kw, i) => (
                            <Chip key={i} label={kw} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}

                    {tablesMutation.data && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Tables ({tablesMutation.data.total} found)
                        </Typography>
                        {tablesMutation.data.tables.map((t, i) => (
                          <Box key={i} sx={{ mb: 1 }}>
                            <Typography variant="caption">
                              Page {t.page}, Table {t.table_index + 1} ({t.row_count} rows)
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}
                  </Box>
                )}

                {/* RAG Query tab */}
                {tab === 1 && (
                  <Box>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="Ask a question about this PDF..."
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
                      />
                      <IconButton
                        color="primary"
                        onClick={handleQuery}
                        disabled={queryMutation.isPending || !question.trim()}
                      >
                        <SendIcon />
                      </IconButton>
                    </Box>

                    {queryMutation.isPending && <CircularProgress size={24} />}
                    {queryMutation.data && (
                      <Box>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                          {queryMutation.data.answer}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Confidence: {(queryMutation.data.confidence * 100).toFixed(1)}% |{' '}
                          {queryMutation.data.sources.length} source(s)
                        </Typography>
                        {queryMutation.data.sources.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Divider sx={{ my: 1 }} />
                            <Typography variant="subtitle2" gutterBottom>Sources</Typography>
                            {queryMutation.data.sources.map((s, i) => (
                              <Card key={i} variant="outlined" sx={{ mb: 0.5, p: 1 }}>
                                <Typography variant="caption" color="text.secondary">
                                  Chunk {s.chunk_index} (relevance: {(s.relevance * 100).toFixed(1)}%)
                                </Typography>
                                <Typography variant="body2" fontSize="0.8rem">
                                  {s.text}
                                </Typography>
                              </Card>
                            ))}
                          </Box>
                        )}
                      </Box>
                    )}
                  </Box>
                )}

                {/* Pages tab */}
                {tab === 2 && (
                  <Box>
                    {pdfDetail?.pages?.length ? (
                      pdfDetail.pages.map((page) => (
                        <Card key={page.page_number} variant="outlined" sx={{ mb: 1, p: 1 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Page {page.page_number}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{ whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto', fontSize: '0.8rem' }}
                          >
                            {page.text || '(no text)'}
                          </Typography>
                        </Card>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No page content available.
                      </Typography>
                    )}
                  </Box>
                )}

                {/* Export tab */}
                {tab === 3 && (
                  <Box>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      {['markdown', 'txt', 'json'].map((fmt) => (
                        <Button
                          key={fmt}
                          variant="outlined"
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => exportMutation.mutate(fmt)}
                          disabled={exportMutation.isPending}
                        >
                          {fmt.toUpperCase()}
                        </Button>
                      ))}
                    </Box>

                    {exportMutation.isPending && <CircularProgress size={24} />}
                    {exportMutation.data && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Exported as {exportMutation.data.format} ({exportMutation.data.filename})
                        </Typography>
                        <TextField
                          fullWidth
                          multiline
                          minRows={8}
                          maxRows={20}
                          value={exportMutation.data.content}
                          InputProps={{ readOnly: true }}
                          sx={{ '& .MuiInputBase-input': { fontFamily: 'monospace', fontSize: '0.8rem' } }}
                        />
                      </Box>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Compare results */}
          {compareMutation.data && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Comparison ({compareMutation.data.comparison_type})
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, mb: 1, flexWrap: 'wrap' }}>
                  {compareMutation.data.documents.map((d) => (
                    <Chip key={d.id} label={`${d.filename} (${d.num_pages}p)`} size="small" />
                  ))}
                </Box>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {compareMutation.data.comparison}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
