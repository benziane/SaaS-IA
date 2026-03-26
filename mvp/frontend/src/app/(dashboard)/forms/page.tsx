'use client';

import { useState } from 'react';
import {
  Plus, Trash2, Pencil, Copy, BarChart3, List, Upload, Sparkles,
  Ban, Link, Star, ArrowUp, ArrowDown, Loader2, FileText,
} from 'lucide-react';

import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Switch } from '@/lib/design-hub/components/Switch';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import {
  useForms,
  useCreateForm,
  useDeleteForm,
  usePublishForm,
  useCloseForm,
  useGenerateForm,
  useFormResponses,
  useFormAnalytics,
  useScoreResponse,
} from '@/features/ai-forms/hooks/useAIForms';
import type { Form, FormField } from '@/features/ai-forms/types';

const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'email', label: 'Email' },
  { value: 'number', label: 'Number' },
  { value: 'select', label: 'Select' },
  { value: 'multiselect', label: 'Multi-Select' },
  { value: 'rating', label: 'Rating' },
  { value: 'textarea', label: 'Textarea' },
  { value: 'date', label: 'Date' },
  { value: 'file', label: 'File' },
] as const;

const STYLE_OPTIONS = ['conversational', 'classic', 'quiz', 'survey'];

const STATUS_VARIANTS: Record<string, 'default' | 'success' | 'destructive'> = {
  draft: 'default',
  published: 'success',
  closed: 'destructive',
};

export default function FormsPage() {
  const { data: forms, isLoading } = useForms();
  const createMutation = useCreateForm();
  const deleteMutation = useDeleteForm();
  const publishMutation = usePublishForm();
  const closeMutation = useCloseForm();
  const generateMutation = useGenerateForm();
  const scoreMutation = useScoreResponse();

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [style, setStyle] = useState('conversational');
  const [thankYouMessage, setThankYouMessage] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [editFields, setEditFields] = useState<FormField[]>([]);

  // Generate dialog
  const [generateOpen, setGenerateOpen] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState('');
  const [generateNumFields, setGenerateNumFields] = useState(5);

  // Detail / responses dialog
  const [detailForm, setDetailForm] = useState<Form | null>(null);
  const [responsesFormId, setResponsesFormId] = useState<string | null>(null);
  const [responsesOpen, setResponsesOpen] = useState(false);

  // Analytics dialog
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [analyticsFormId, setAnalyticsFormId] = useState<string | null>(null);

  const { data: responses } = useFormResponses(responsesOpen ? responsesFormId : null);
  const { data: analytics } = useFormAnalytics(analyticsOpen ? analyticsFormId : null);

  const resetCreateForm = () => {
    setTitle('');
    setDescription('');
    setStyle('conversational');
    setThankYouMessage('');
    setIsPublic(false);
    setEditFields([]);
  };

  const handleCreate = () => {
    if (!title.trim()) return;
    createMutation.mutate(
      {
        title,
        description: description || undefined,
        fields: editFields,
        style,
        thank_you_message: thankYouMessage || undefined,
        is_public: isPublic,
      },
      {
        onSuccess: () => {
          setCreateOpen(false);
          resetCreateForm();
        },
      }
    );
  };

  const handleGenerate = () => {
    if (!generatePrompt.trim()) return;
    generateMutation.mutate(
      { prompt: generatePrompt, num_fields: generateNumFields },
      {
        onSuccess: () => {
          setGenerateOpen(false);
          setGeneratePrompt('');
          setGenerateNumFields(5);
        },
      }
    );
  };

  const handleAddField = () => {
    const newField: FormField = {
      field_id: `field_${Date.now()}`,
      type: 'text',
      label: '',
      required: false,
      options: null,
      validation: null,
      condition: null,
    };
    setEditFields([...editFields, newField]);
  };

  const handleUpdateField = (index: number, updates: Partial<FormField>) => {
    const updated = [...editFields];
    updated[index] = { ...updated[index], ...updates } as FormField;
    setEditFields(updated);
  };

  const handleRemoveField = (index: number) => {
    setEditFields(editFields.filter((_, i) => i !== index));
  };

  const handleMoveField = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= editFields.length) return;
    const updated = [...editFields];
    [updated[index], updated[newIndex]] = [updated[newIndex]!, updated[index]!];
    setEditFields(updated);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-high)] flex items-center gap-2">
            <FileText className="h-8 w-8 text-[var(--accent)]" /> AI Forms
          </h1>
          <p className="text-sm text-[var(--text-mid)]">
            Create AI-powered forms with smart validation, response analysis, and AI-generated fields
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setGenerateOpen(true)}>
            <Sparkles className="h-4 w-4 mr-2" /> AI Generate
          </Button>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" /> New Form
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-52 rounded-lg" />
          ))}
        </div>
      ) : !forms?.length ? (
        <Card>
          <CardContent className="text-center py-16 px-6">
            <FileText className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-[var(--text-mid)]">No forms yet</h3>
            <p className="text-sm text-[var(--text-mid)] mt-2 mb-4">
              Create your first AI-powered form or let AI generate one for you
            </p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" onClick={() => setGenerateOpen(true)}>
                <Sparkles className="h-4 w-4 mr-2" /> AI Generate
              </Button>
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-2" /> Create Form
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {forms.map((form) => (
            <Card
              key={form.id}
              className="flex flex-col h-full border border-[var(--border)] hover:border-[var(--accent)] transition-colors"
            >
              <CardContent className="flex-1 p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-[var(--text-high)] truncate max-w-[70%]">
                    {form.title}
                  </h3>
                  <Badge variant={STATUS_VARIANTS[form.status] || 'default'}>
                    {form.status}
                  </Badge>
                </div>

                {form.description && (
                  <p className="text-sm text-[var(--text-mid)] mb-3 line-clamp-2">
                    {form.description}
                  </p>
                )}

                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="outline" className="text-[var(--accent)]">{form.fields.length} fields</Badge>
                  <Badge variant="outline">{form.style}</Badge>
                  {form.is_public && <Badge variant="secondary">Public</Badge>}
                </div>

                <div className="flex items-center gap-1">
                  <List className="h-3.5 w-3.5 text-[var(--text-mid)]" />
                  <span className="text-xs text-[var(--text-mid)]">
                    {form.responses_count} response{form.responses_count !== 1 ? 's' : ''}
                  </span>
                </div>
              </CardContent>

              <CardFooter className="justify-end gap-1 px-4 pb-3 pt-0">
                <TooltipProvider>
                  {form.status === 'draft' && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          title="Publish"
                          className="p-1.5 rounded hover:bg-green-100 text-green-600"
                          onClick={() => publishMutation.mutate(form.id)}
                          disabled={publishMutation.isPending}
                        >
                          <Upload className="h-4 w-4" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Publish</TooltipContent>
                    </Tooltip>
                  )}
                  {form.status === 'published' && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          title="Close"
                          className="p-1.5 rounded hover:bg-yellow-100 text-yellow-600"
                          onClick={() => closeMutation.mutate(form.id)}
                          disabled={closeMutation.isPending}
                        >
                          <Ban className="h-4 w-4" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Close</TooltipContent>
                    </Tooltip>
                  )}
                  {form.share_token && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          title="Copy Share Link"
                          className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                          onClick={() => handleCopy(`${window.location.origin}/forms/public/${form.share_token}`)}
                        >
                          <Link className="h-4 w-4 text-[var(--text-mid)]" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Copy Share Link</TooltipContent>
                    </Tooltip>
                  )}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        title="Responses"
                        className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                        onClick={() => {
                          setResponsesFormId(form.id);
                          setResponsesOpen(true);
                        }}
                      >
                        <List className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Responses</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        title="Analytics"
                        className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                        onClick={() => {
                          setAnalyticsFormId(form.id);
                          setAnalyticsOpen(true);
                        }}
                      >
                        <BarChart3 className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Analytics</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        title="Details"
                        className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                        onClick={() => setDetailForm(form)}
                      >
                        <Pencil className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Details</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        title="Delete"
                        className="p-1.5 rounded hover:bg-red-100 text-red-500"
                        onClick={() => deleteMutation.mutate(form.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Delete</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Form Dialog */}
      <Dialog open={createOpen} onOpenChange={(v) => { if (!v) setCreateOpen(false); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>New Form</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <Input
              placeholder="Form Title (e.g., Customer Feedback Survey)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <Input
              placeholder="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-[var(--text-mid)] mb-1 block">Style</label>
                <Select value={style} onValueChange={setStyle}>
                  <SelectTrigger>
                    <SelectValue placeholder="Style" />
                  </SelectTrigger>
                  <SelectContent>
                    {STYLE_OPTIONS.map((s) => (
                      <SelectItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-5">
                <Switch checked={isPublic} onCheckedChange={setIsPublic} />
                <label className="text-sm text-[var(--text-high)]">Public form</label>
              </div>
            </div>
            <Input
              placeholder="Thank You Message (optional)"
              value={thankYouMessage}
              onChange={(e) => setThankYouMessage(e.target.value)}
            />

            {/* Fields Builder */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-[var(--text-high)]">Fields</p>
                <Button size="sm" variant="outline" onClick={handleAddField}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add Field
                </Button>
              </div>

              {editFields.map((field, index) => (
                <Card key={field.field_id} className="mb-2 p-3 border border-[var(--border)]">
                  <div className="grid grid-cols-12 gap-2 items-center">
                    <div className="col-span-4">
                      <Input
                        placeholder="Label"
                        value={field.label}
                        onChange={(e) => handleUpdateField(index, { label: e.target.value })}
                      />
                    </div>
                    <div className="col-span-2">
                      <Select
                        value={field.type}
                        onValueChange={(val) =>
                          handleUpdateField(index, {
                            type: val as FormField['type'],
                            options: val === 'select' || val === 'multiselect' ? field.options || [] : null,
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Type" />
                        </SelectTrigger>
                        <SelectContent>
                          {FIELD_TYPES.map((ft) => (
                            <SelectItem key={ft.value} value={ft.value}>{ft.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-2 flex items-center gap-1">
                      <Switch
                        checked={field.required}
                        onCheckedChange={(v) => handleUpdateField(index, { required: v })}
                      />
                      <span className="text-xs text-[var(--text-mid)]">Req</span>
                    </div>
                    {(field.type === 'select' || field.type === 'multiselect') && (
                      <div className="col-span-2">
                        <Input
                          placeholder="Options (comma)"
                          value={(field.options || []).join(', ')}
                          onChange={(e) =>
                            handleUpdateField(index, {
                              options: e.target.value.split(',').map((o) => o.trim()).filter(Boolean),
                            })
                          }
                        />
                      </div>
                    )}
                    <div className={`${field.type === 'select' || field.type === 'multiselect' ? 'col-span-2' : 'col-span-4'} flex justify-end gap-0.5`}>
                      <button type="button" title="Move up" className="p-1 rounded hover:bg-[var(--bg-hover)]" onClick={() => handleMoveField(index, 'up')} disabled={index === 0}>
                        <ArrowUp className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                      <button type="button" title="Move down" className="p-1 rounded hover:bg-[var(--bg-hover)]" onClick={() => handleMoveField(index, 'down')} disabled={index === editFields.length - 1}>
                        <ArrowDown className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                      <button type="button" title="Remove" className="p-1 rounded hover:bg-red-100 text-red-500" onClick={() => handleRemoveField(index)}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))}

              {editFields.length === 0 && (
                <p className="text-sm text-[var(--text-mid)] text-center py-4">
                  No fields added yet. Click &quot;Add Field&quot; to start building.
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreate}
              disabled={!title.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FileText className="h-4 w-4 mr-2" />
              )}
              Create Form
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Generate Dialog */}
      <Dialog open={generateOpen} onOpenChange={(v) => { if (!v) setGenerateOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[var(--accent)]" /> AI Form Generator
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <p className="text-sm text-[var(--text-mid)]">
              Describe the form you want and AI will generate the fields for you.
            </p>
            <Textarea
              rows={4}
              placeholder="e.g., A customer satisfaction survey for an e-commerce platform with questions about delivery, product quality, and support experience"
              value={generatePrompt}
              onChange={(e) => setGeneratePrompt(e.target.value)}
            />
            <Input
              type="number"
              placeholder="Number of fields"
              value={generateNumFields}
              onChange={(e) => setGenerateNumFields(Math.max(1, Math.min(30, parseInt(e.target.value) || 5)))}
              min={1}
              max={30}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setGenerateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleGenerate}
              disabled={!generatePrompt.trim() || generateMutation.isPending}
            >
              {generateMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4 mr-2" />
              )}
              Generate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Form Detail Dialog */}
      <Dialog open={!!detailForm} onOpenChange={(v) => { if (!v) setDetailForm(null); }}>
        {detailForm && (
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-[var(--accent)]" />
                {detailForm.title}
                <Badge variant={STATUS_VARIANTS[detailForm.status] || 'default'}>{detailForm.status}</Badge>
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 border-t border-[var(--border)] pt-4">
              {detailForm.description && (
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Description</span>
                  <p className="text-sm text-[var(--text-high)]">{detailForm.description}</p>
                </div>
              )}

              <div className="grid grid-cols-4 gap-4">
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Style</span>
                  <p className="text-sm text-[var(--text-high)]">{detailForm.style}</p>
                </div>
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Fields</span>
                  <p className="text-sm text-[var(--text-high)]">{detailForm.fields.length}</p>
                </div>
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Responses</span>
                  <p className="text-sm text-[var(--text-high)]">{detailForm.responses_count}</p>
                </div>
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Public</span>
                  <p className="text-sm text-[var(--text-high)]">{detailForm.is_public ? 'Yes' : 'No'}</p>
                </div>
              </div>

              {detailForm.share_token && (
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Share Token</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono bg-[var(--bg-surface)] px-2 py-1 rounded">
                      {detailForm.share_token}
                    </span>
                    <button type="button" title="Copy" className="p-1 rounded hover:bg-[var(--bg-hover)]" onClick={() => handleCopy(detailForm.share_token!)}>
                      <Copy className="h-4 w-4 text-[var(--text-mid)]" />
                    </button>
                  </div>
                </div>
              )}

              {detailForm.thank_you_message && (
                <div>
                  <span className="text-xs text-[var(--text-mid)]">Thank You Message</span>
                  <p className="text-sm text-[var(--text-high)]">{detailForm.thank_you_message}</p>
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-[var(--text-high)] mb-2">Fields</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)]">
                        <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Label</th>
                        <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Type</th>
                        <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Required</th>
                        <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Options</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detailForm.fields.map((field) => (
                        <tr key={field.field_id} className="border-b border-[var(--border)]">
                          <td className="py-2 px-3 text-[var(--text-high)]">{field.label}</td>
                          <td className="py-2 px-3"><Badge variant="outline">{field.type}</Badge></td>
                          <td className="py-2 px-3 text-[var(--text-high)]">{field.required ? 'Yes' : 'No'}</td>
                          <td className="py-2 px-3 text-[var(--text-mid)]">{field.options ? field.options.join(', ') : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDetailForm(null)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        )}
      </Dialog>

      {/* Responses Dialog */}
      <Dialog open={responsesOpen} onOpenChange={(v) => { if (!v) setResponsesOpen(false); }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <List className="h-5 w-5 text-[var(--accent)]" /> Form Responses
            </DialogTitle>
          </DialogHeader>
          {responses ? (
            responses.length === 0 ? (
              <p className="text-sm text-[var(--text-mid)] text-center py-8">No responses yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)]">
                      <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Submitted</th>
                      <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Answers</th>
                      <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Score</th>
                      <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Analysis</th>
                      <th className="text-left py-2 px-3 text-[var(--text-mid)] font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {responses.map((resp) => (
                      <tr key={resp.id} className="border-b border-[var(--border)]">
                        <td className="py-2 px-3 text-[var(--text-high)]">
                          {new Date(resp.submitted_at).toLocaleString()}
                        </td>
                        <td className="py-2 px-3 max-w-[300px]">
                          <span className="text-sm text-[var(--text-high)] truncate block">
                            {JSON.stringify(resp.answers)}
                          </span>
                        </td>
                        <td className="py-2 px-3">
                          {resp.score !== null ? (
                            <Badge variant={resp.score >= 0.7 ? 'success' : resp.score >= 0.4 ? 'warning' : 'destructive'}>
                              {(resp.score * 100).toFixed(0)}%
                            </Badge>
                          ) : '-'}
                        </td>
                        <td className="py-2 px-3 max-w-[200px]">
                          <span className="text-sm text-[var(--text-high)] truncate block">
                            {resp.analysis || '-'}
                          </span>
                        </td>
                        <td className="py-2 px-3">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  title="AI Score"
                                  className="p-1 rounded hover:bg-[var(--bg-hover)]"
                                  onClick={() =>
                                    scoreMutation.mutate({
                                      formId: responsesFormId!,
                                      responseId: resp.id,
                                    })
                                  }
                                  disabled={scoreMutation.isPending}
                                >
                                  <Star className="h-4 w-4 text-[var(--text-mid)]" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>AI Score</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setResponsesOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Analytics Dialog */}
      <Dialog open={analyticsOpen} onOpenChange={(v) => { if (!v) setAnalyticsOpen(false); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-[var(--accent)]" /> Form Analytics
            </DialogTitle>
          </DialogHeader>
          {analytics ? (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <Card className="border border-[var(--border)]">
                  <CardContent className="text-center p-4">
                    <p className="text-3xl font-bold text-[var(--text-high)]">{analytics.total_responses}</p>
                    <span className="text-xs text-[var(--text-mid)]">Total Responses</span>
                  </CardContent>
                </Card>
                <Card className="border border-[var(--border)]">
                  <CardContent className="text-center p-4">
                    <p className="text-3xl font-bold text-[var(--text-high)]">
                      {(analytics.completion_rate * 100).toFixed(0)}%
                    </p>
                    <span className="text-xs text-[var(--text-mid)]">Completion Rate</span>
                  </CardContent>
                </Card>
                <Card className="border border-[var(--border)]">
                  <CardContent className="text-center p-4">
                    <p className="text-3xl font-bold text-[var(--text-high)]">
                      {Object.keys(analytics.field_stats).length}
                    </p>
                    <span className="text-xs text-[var(--text-mid)]">Fields Tracked</span>
                  </CardContent>
                </Card>
              </div>

              {/* Field stats */}
              <div>
                <p className="text-sm font-medium text-[var(--text-high)] mb-2">Field Statistics</p>
                {Object.entries(analytics.field_stats).map(([fieldId, stat]) => (
                  <div key={fieldId} className="mb-3">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-[var(--text-high)]">{stat.label}</span>
                      <span className="text-xs text-[var(--text-mid)]">
                        {stat.response_count} responses ({(stat.fill_rate * 100).toFixed(0)}%)
                      </span>
                    </div>
                    <Progress value={stat.fill_rate * 100} className="h-1.5" />
                    {stat.average !== undefined && (
                      <span className="text-xs text-[var(--text-mid)]">
                        Avg: {stat.average} | Min: {stat.min} | Max: {stat.max}
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* AI Insights */}
              {analytics.ai_insights && (
                <div>
                  <p className="text-sm font-medium text-[var(--text-high)] mb-2">AI Insights</p>
                  <Card className="border border-[var(--border)]">
                    <CardContent className="p-4">
                      <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap">
                        {analytics.ai_insights}
                      </p>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          ) : (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setAnalyticsOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {createMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{createMutation.error?.message}</AlertDescription>
        </Alert>
      )}
      {generateMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{generateMutation.error?.message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
