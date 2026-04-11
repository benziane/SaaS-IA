'use client';

import { useRouter } from 'next/navigation';
import { Sun, Moon, Monitor, Globe, User, Key, CreditCard, Settings } from 'lucide-react';

import { useSettings } from '@core/hooks/useSettings';
import { Button } from '@/lib/design-hub/components/Button';

type ThemeMode = 'light' | 'dark' | 'system';

const THEME_TILES: { mode: ThemeMode; label: string; Icon: typeof Sun }[] = [
  { mode: 'light',  label: 'Light',  Icon: Sun },
  { mode: 'dark',   label: 'Dark',   Icon: Moon },
  { mode: 'system', label: 'System', Icon: Monitor },
];

export default function SettingsPage() {
  const router = useRouter();
  const { settings, updateSettings } = useSettings();

  const currentMode = (settings.mode as ThemeMode) ?? 'system';

  return (
    <div className="p-5 space-y-5 animate-enter max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-11 h-11 rounded-xl shrink-0"
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
        >
          <Settings className="w-5 h-5 text-[var(--accent)]" />
        </div>
        <div>
          <h4 className="text-[var(--text-high)] text-lg font-bold leading-tight">Settings</h4>
          <p className="text-[var(--text-low)] text-sm">Application preferences</p>
        </div>
      </div>

      {/* Section 1 — Appearance */}
      <div className="surface-card p-5 space-y-4">
        <h6 className="text-[var(--text-high)] text-sm font-semibold">Appearance</h6>
        <div>
          <p className="text-[var(--text-mid)] text-xs mb-3">Theme</p>
          <div className="flex gap-3">
            {THEME_TILES.map(({ mode, label, Icon }) => {
              const isActive = currentMode === mode;
              return (
                <button
                  key={mode}
                  onClick={() => updateSettings({ mode })}
                  className={[
                    'flex flex-col items-center gap-2 flex-1 py-4 rounded-xl border transition-all duration-200',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]',
                    isActive
                      ? 'border-[var(--accent)] bg-[var(--accent)]/5'
                      : 'border-[var(--border)] bg-[var(--bg-elevated)] hover:border-[var(--accent)]/40',
                  ].join(' ')}
                >
                  <Icon
                    className={`w-5 h-5 ${isActive ? 'text-[var(--accent)]' : 'text-[var(--text-mid)]'}`}
                  />
                  <span
                    className={`text-xs font-medium ${isActive ? 'text-[var(--accent)]' : 'text-[var(--text-mid)]'}`}
                  >
                    {label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Section 2 — Language */}
      <div className="surface-card p-5 space-y-4">
        <h6 className="text-[var(--text-high)] text-sm font-semibold">Language</h6>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--bg-elevated)]">
              <Globe className="w-4 h-4 text-[var(--text-mid)]" />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--text-high)]">English</p>
              <p className="text-xs text-[var(--text-low)]">More languages coming soon</p>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3 — Account */}
      <div className="surface-card p-5 space-y-4">
        <h6 className="text-[var(--text-high)] text-sm font-semibold">Account</h6>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="outline"
            size="md"
            onClick={() => router.push('/profile')}
            className="flex-1 justify-start"
          >
            <User className="w-4 h-4" />
            Manage Profile
          </Button>
          <Button
            variant="outline"
            size="md"
            onClick={() => router.push('/api-keys')}
            className="flex-1 justify-start"
          >
            <Key className="w-4 h-4" />
            API Keys
          </Button>
          <Button
            variant="outline"
            size="md"
            onClick={() => router.push('/billing')}
            className="flex-1 justify-start"
          >
            <CreditCard className="w-4 h-4" />
            Billing
          </Button>
        </div>
      </div>
    </div>
  );
}
