'use client';

import { useEffect, useState } from 'react';

import { Package2 } from 'lucide-react';
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

function ModuleCardSkeleton() {
  return (
    <div className="surface-card p-5 h-full">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <Skeleton className="h-5 w-3/5 mb-2" />
          <Skeleton className="h-3 w-1/3" />
        </div>
        <Skeleton className="h-6 w-[70px] rounded" />
      </div>
      <Skeleton className="h-4 w-full mb-1" />
      <Skeleton className="h-4 w-4/5 mb-4" />
      <Skeleton className="h-3 w-2/5 mb-2" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  );
}

/* ========================================================================
   MODULE CARD
   ======================================================================== */

function ModuleCard({ module }: { module: ModuleInfo }) {
  return (
    <div className="surface-card p-5 h-full flex flex-col">
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="text-base font-semibold text-[var(--text-high)]">{module.name}</p>
          <p className="text-xs text-[var(--text-mid)]">v{module.version}</p>
        </div>
        <Badge variant={module.enabled !== false ? 'success' : 'secondary'}>
          {module.enabled !== false ? 'Enabled' : 'Disabled'}
        </Badge>
      </div>
      <div className="flex-1">
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
      </div>
    </div>
  );
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function ModulesPage() {
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
    <div className="p-5 space-y-5 animate-enter">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Package2 className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Platform Modules</h1>
          <p className="text-xs text-[var(--text-mid)]">Active modules and system status</p>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load modules: {error}</AlertDescription>
        </Alert>
      )}

      {/* Module Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
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
        <div className="surface-card p-5 mt-5">
          <div className="py-12 text-center">
            <Package2 className="h-8 w-8 text-[var(--text-low)] mx-auto mb-3" />
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-1">
              No modules registered
            </h2>
            <p className="text-sm text-[var(--text-mid)]">
              Backend modules will appear here once they are registered with the platform.
            </p>
            <a
              href="/monitoring"
              className="text-xs text-[var(--accent)] hover:underline mt-1 inline-block"
            >
              Check backend status →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
