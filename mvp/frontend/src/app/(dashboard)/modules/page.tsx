/**
 * Platform Modules Page - Grade S++
 * Admin view of all registered backend modules and their status
 */

'use client';

import { useEffect, useState } from 'react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';

import { apiClient, extractErrorMessage } from '@/lib/apiClient';

/* ========================================================================
   TYPES
   ======================================================================== */

interface ModuleInfo {
  name: string;
  version: string;
  description: string;
  enabled?: boolean;
  prefix: string;
  dependencies: string[];
  tags?: string[];
}

/* ========================================================================
   LOADING SKELETON
   ======================================================================== */

function ModuleCardSkeleton(): JSX.Element {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <Skeleton className="h-5 w-3/5 mb-2" />
            <Skeleton className="h-3 w-1/3" />
          </div>
          <Skeleton className="h-6 w-[70px] rounded" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full mb-1" />
        <Skeleton className="h-4 w-4/5 mb-4" />
        <Skeleton className="h-3 w-2/5 mb-2" />
        <Skeleton className="h-3 w-1/2" />
      </CardContent>
    </Card>
  );
}

/* ========================================================================
   MODULE CARD
   ======================================================================== */

function ModuleCard({ module }: { module: ModuleInfo }): JSX.Element {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-base">{module.name}</CardTitle>
            <CardDescription>v{module.version}</CardDescription>
          </div>
          <Badge variant={module.enabled !== false ? 'success' : 'secondary'}>
            {module.enabled !== false ? 'Enabled' : 'Disabled'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-sm text-[var(--text-mid)] mb-4">
          {module.description}
        </p>

        <span className="text-xs text-[var(--text-low)] block mb-1">
          API Prefix
        </span>
        <code className="text-sm font-mono bg-[var(--bg-elevated)] px-2 py-1 rounded inline-block mb-4">
          {module.prefix}
        </code>

        {module.dependencies.length > 0 && (
          <>
            <span className="text-xs text-[var(--text-low)] block mb-1">
              Dependencies
            </span>
            <div className="flex flex-wrap gap-1">
              {module.dependencies.map((dep) => (
                <Badge key={dep} variant="outline" className="text-xs border-blue-500/30 text-blue-400">
                  {dep}
                </Badge>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function ModulesPage(): JSX.Element {
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchModules(): Promise<void> {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.get<{ count: number; modules: ModuleInfo[] }>('/api/modules');
        if (!cancelled) {
          setModules(response.data.modules ?? []);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(extractErrorMessage(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchModules();

    return () => {
      cancelled = true;
    };
  }, []);

  /* ========================================================================
     RENDER
     ======================================================================== */

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--text-high)] mb-1">
          Platform Modules
        </h1>
        <p className="text-[var(--text-mid)]">
          Overview of all registered backend modules and their current status.
        </p>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>Failed to load modules: {error}</AlertDescription>
        </Alert>
      )}

      {/* Module Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {loading
          ? Array.from({ length: 3 }).map((_, index) => (
              <ModuleCardSkeleton key={index} />
            ))
          : modules.map((mod) => (
              <ModuleCard key={mod.name} module={mod} />
            ))}
      </div>

      {/* Empty State */}
      {!loading && !error && modules.length === 0 && (
        <Card className="mt-6">
          <CardContent className="py-12 text-center">
            <h2 className="text-lg font-semibold text-[var(--text-mid)] mb-1">
              No modules registered
            </h2>
            <p className="text-sm text-[var(--text-mid)]">
              Backend modules will appear here once they are registered with the platform.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
