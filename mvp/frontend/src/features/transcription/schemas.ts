/**
 * Transcription Schemas - Grade S++
 * Zod validation schemas for transcription
 */

import { z } from 'zod';

/* ========================================================================
   VALIDATION RULES
   ======================================================================== */

const YOUTUBE_URL_REGEX =
  /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{11}([?&].*)?$/;

/* ========================================================================
   TRANSCRIPTION CREATE SCHEMA
   ======================================================================== */

export const LANGUAGE_OPTIONS = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'fr', label: 'French' },
  { value: 'en', label: 'English' },
  { value: 'ar', label: 'Arabic' },
  { value: 'es', label: 'Spanish' },
  { value: 'de', label: 'German' },
] as const;

export const transcriptionCreateSchema = z.object({
  video_url: z
    .string()
    .min(1, 'YouTube URL is required')
    .url('Invalid URL format')
    .regex(YOUTUBE_URL_REGEX, 'Invalid YouTube URL. Please provide a valid YouTube video URL')
    .trim(),
  language: z
    .string()
    .optional()
    .default('auto'),
});

// React Hook Form values correspond to the input shape (before Zod defaults are applied).
export type TranscriptionCreateSchema = z.input<typeof transcriptionCreateSchema>;

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  transcriptionCreateSchema,
};

