/**
 * Custom hooks for transcription management
 */
import { useState, useEffect, useCallback } from 'react';
import useSWR from 'swr';
import { transcriptionApi } from '@/lib/api';
import { Transcription, TranscriptionList, TranscriptionStats } from '@/types/transcription';

/**
 * Hook for fetching transcription by ID with auto-refresh
 */
export const useTranscription = (id: number | null, autoRefresh: boolean = false) => {
  const { data, error, mutate } = useSWR<Transcription>(
    id ? `/transcriptions/${id}` : null,
    () => id ? transcriptionApi.getById(id) : null,
    {
      refreshInterval: autoRefresh ? 3000 : 0, // Refresh every 3 seconds if autoRefresh is true
      revalidateOnFocus: false,
    }
  );

  return {
    transcription: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
};

/**
 * Hook for fetching transcription list
 */
export const useTranscriptionList = (params?: {
  page?: number;
  page_size?: number;
  status?: string;
  language?: string;
}) => {
  const { data, error, mutate } = useSWR<TranscriptionList>(
    ['/transcriptions', params],
    () => transcriptionApi.list(params)
  );

  return {
    transcriptions: data?.transcriptions || [],
    total: data?.total || 0,
    page: data?.page || 1,
    pageSize: data?.page_size || 20,
    totalPages: data?.total_pages || 1,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
};

/**
 * Hook for fetching statistics
 */
export const useTranscriptionStats = () => {
  const { data, error, mutate } = useSWR<TranscriptionStats>(
    '/transcriptions/stats',
    () => transcriptionApi.getStats()
  );

  return {
    stats: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  };
};

/**
 * Hook for creating transcription
 */
export const useCreateTranscription = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(async (youtubeUrl: string, language: string = 'auto') => {
    setIsLoading(true);
    setError(null);

    try {
      const transcription = await transcriptionApi.create(youtubeUrl, language);
      return transcription;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create transcription';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    create,
    isLoading,
    error,
  };
};

/**
 * Hook for video preview
 */
export const useVideoPreview = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const preview = useCallback(async (url: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const videoInfo = await transcriptionApi.preview(url);
      return videoInfo;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to preview video';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    preview,
    isLoading,
    error,
  };
};
