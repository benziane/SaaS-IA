'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createCrew, createCrewFromTemplate, deleteCrew, listCrewRuns, listCrews, listCrewTemplates, runCrew } from '../api';
import type { Crew, CrewCreateRequest, CrewRun, CrewTemplate } from '../types';

export function useCrews() {
  return useQuery<Crew[]>({ queryKey: ['crews'], queryFn: listCrews });
}
export function useCreateCrew() {
  const qc = useQueryClient();
  return useMutation<Crew, Error, CrewCreateRequest>({ mutationFn: createCrew, onSuccess: () => qc.invalidateQueries({ queryKey: ['crews'] }) });
}
export function useDeleteCrew() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({ mutationFn: deleteCrew, onSuccess: () => qc.invalidateQueries({ queryKey: ['crews'] }) });
}
export function useRunCrew() {
  const qc = useQueryClient();
  return useMutation<CrewRun, Error, { id: string; instruction: string; inputData?: Record<string, unknown> }>({
    mutationFn: ({ id, instruction, inputData }) => runCrew(id, instruction, inputData),
    onSuccess: (_, v) => { qc.invalidateQueries({ queryKey: ['crews'] }); qc.invalidateQueries({ queryKey: ['crew-runs', v.id] }); },
  });
}
export function useCrewRuns(crewId: string | null) {
  return useQuery<CrewRun[]>({ queryKey: ['crew-runs', crewId], queryFn: () => listCrewRuns(crewId!), enabled: !!crewId });
}
export function useCrewTemplates(category?: string) {
  return useQuery<CrewTemplate[]>({ queryKey: ['crew-templates', category], queryFn: () => listCrewTemplates(category) });
}
export function useCreateFromTemplate() {
  const qc = useQueryClient();
  return useMutation<Crew, Error, { templateId: string; name?: string }>({
    mutationFn: ({ templateId, name }) => createCrewFromTemplate(templateId, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['crews'] }),
  });
}
