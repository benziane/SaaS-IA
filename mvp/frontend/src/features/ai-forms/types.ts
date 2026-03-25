/**
 * AI Forms Types
 */

export interface FormField {
  field_id: string;
  type: 'text' | 'email' | 'number' | 'select' | 'multiselect' | 'rating' | 'textarea' | 'date' | 'file';
  label: string;
  required: boolean;
  options: string[] | null;
  validation: Record<string, unknown> | null;
  condition: Record<string, unknown> | null;
}

export interface Form {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  fields: FormField[];
  style: string;
  thank_you_message: string | null;
  is_public: boolean;
  share_token: string | null;
  responses_count: number;
  status: 'draft' | 'published' | 'closed';
  created_at: string;
  updated_at: string;
}

export interface FormCreateRequest {
  title: string;
  description?: string;
  fields: FormField[];
  style?: string;
  thank_you_message?: string;
  is_public?: boolean;
}

export interface FormUpdateRequest {
  title?: string;
  description?: string;
  fields?: FormField[];
  style?: string;
  thank_you_message?: string;
  is_public?: boolean;
}

export interface FormResponseItem {
  id: string;
  form_id: string;
  answers: Record<string, unknown>;
  score: number | null;
  analysis: string | null;
  submitted_at: string;
}

export interface FormResponseCreateRequest {
  answers: Record<string, unknown>;
}

export interface FormGenerateRequest {
  prompt: string;
  num_fields?: number;
}

export interface FormAnalysis {
  form_id: string;
  total_responses: number;
  completion_rate: number;
  field_stats: Record<string, FieldStat>;
  ai_insights: string | null;
}

export interface FieldStat {
  label: string;
  type: string;
  response_count: number;
  fill_rate: number;
  average?: number;
  min?: number;
  max?: number;
  option_distribution?: Record<string, number>;
}
