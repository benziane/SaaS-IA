/**
 * Feature Flags hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteFeatureFlag,
  getUserFlags,
  killModule,
  listFeatureFlags,
  restoreModule,
  setFeatureFlag,
} from '../api';
import type {
  FeatureFlag,
  FeatureFlagList,
  FeatureFlagUpdate,
  FeatureFlagUserResolved,
  KillSwitchResponse,
} from '../types';

const QUERY_KEY = ['feature-flags'];

export function useFeatureFlags() {
  return useQuery<FeatureFlagList>({
    queryKey: QUERY_KEY,
    queryFn: listFeatureFlags,
    refetchInterval: 15000,
  });
}

export function useSetFeatureFlag() {
  const qc = useQueryClient();
  return useMutation<FeatureFlag, Error, { name: string; data: FeatureFlagUpdate }>({
    mutationFn: ({ name, data }) => setFeatureFlag(name, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useDeleteFeatureFlag() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteFeatureFlag,
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useUserFlags(userId: string) {
  return useQuery<FeatureFlagUserResolved>({
    queryKey: ['feature-flags', 'user', userId],
    queryFn: () => getUserFlags(userId),
    enabled: !!userId,
  });
}

export function useKillModule() {
  const qc = useQueryClient();
  return useMutation<KillSwitchResponse, Error, string>({
    mutationFn: killModule,
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useRestoreModule() {
  const qc = useQueryClient();
  return useMutation<KillSwitchResponse, Error, string>({
    mutationFn: restoreModule,
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}
