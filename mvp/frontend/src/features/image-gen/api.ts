import apiClient from '@/lib/apiClient';
import type { GeneratedImage, GenerateImageRequest, ImageProject } from './types';

export const generateImage = async (data: GenerateImageRequest): Promise<GeneratedImage> => (await apiClient.post('/api/images/generate', data)).data;
export const generateThumbnail = async (data: { source_type: string; source_id?: string; text?: string; style?: string }) => (await apiClient.post('/api/images/thumbnail', data)).data as GeneratedImage;
export const listImages = async (): Promise<GeneratedImage[]> => (await apiClient.get('/api/images')).data;
export const deleteImage = async (id: string): Promise<void> => { await apiClient.delete(`/api/images/${id}`); };
export const createImageProject = async (data: { name: string; description?: string }): Promise<ImageProject> => (await apiClient.post('/api/images/projects', data)).data;
export const listImageProjects = async (): Promise<ImageProject[]> => (await apiClient.get('/api/images/projects')).data;
export const listStyles = async () => (await apiClient.get('/api/images/styles')).data;
