import apiClient from '@/lib/apiClient';
import type { GeneratedVideo, GenerateVideoRequest, VideoProject } from './types';

export const generateVideo = async (data: GenerateVideoRequest): Promise<GeneratedVideo> => (await apiClient.post('/api/videos/generate', data)).data;
export const generateClips = async (data: { transcription_id: string; max_clips?: number; format?: string }) => (await apiClient.post('/api/videos/clips', data)).data as GeneratedVideo[];
export const generateAvatar = async (data: { text: string; avatar_style?: string; background?: string }) => (await apiClient.post('/api/videos/avatar', data)).data as GeneratedVideo;
export const listVideos = async (): Promise<GeneratedVideo[]> => (await apiClient.get('/api/videos')).data;
export const deleteVideo = async (id: string): Promise<void> => { await apiClient.delete(`/api/videos/${id}`); };
export const createVideoProject = async (data: { name: string; description?: string }): Promise<VideoProject> => (await apiClient.post('/api/videos/projects', data)).data;
export const listVideoProjects = async (): Promise<VideoProject[]> => (await apiClient.get('/api/videos/projects')).data;
export const listVideoTypes = async () => (await apiClient.get('/api/videos/types')).data;
