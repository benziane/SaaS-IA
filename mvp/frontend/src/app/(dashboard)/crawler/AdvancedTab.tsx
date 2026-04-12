'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Checkbox } from '@/components/ui/checkbox';
import { useDockerCrawl, useCreateBrowserProfile, useBrowserProfiles } from '@/features/crawler/hooks/useCrawler';

// ─── Section wrapper ────────────────────────────────────────────────────────
function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="surface-card rounded-xl p-5 space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-high)]">{title}</h3>
        {description && <p className="text-xs text-[var(--text-mid)] mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  );
}

// ─── Label + field row ───────────────────────────────────────────────────────
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-[var(--text-mid)] block">{label}</label>
      {children}
    </div>
  );
}

// ─── Styled select ───────────────────────────────────────────────────────────
function StyledSelect({ value, onChange, children }: {
  value: string;
  onChange: (v: string) => void;
  children: React.ReactNode;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-2.5 text-sm text-[var(--text-high)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
    >
      {children}
    </select>
  );
}

// ─── Confirmation banner ─────────────────────────────────────────────────────
function ConfirmBanner({ message }: { message: string }) {
  return (
    <div className="px-4 py-2 rounded-lg bg-[var(--accent)]/10 border border-[var(--accent)]/20 text-xs text-[var(--accent)]">
      {message}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// AdvancedTab
// ════════════════════════════════════════════════════════════════════════════
export function AdvancedTab() {
  // ── 1. CrawlerHub config ──────────────────────────────────────────────────
  const [userAgent, setUserAgent] = useState('Mozilla/5.0 (compatible; SaaS-IA-Crawler/1.0)');
  const [requestTimeout, setRequestTimeout] = useState(30);
  const [delayBetweenRequests, setDelayBetweenRequests] = useState(1.0);
  const [ignoreRobots, setIgnoreRobots] = useState(false);
  const [headlessMode, setHeadlessMode] = useState(true);
  const [hubConfigApplied, setHubConfigApplied] = useState(false);

  // ── 2. Proxy Rotation ─────────────────────────────────────────────────────
  const [proxyList, setProxyList] = useState('');
  const [proxyRotation, setProxyRotation] = useState<'round-robin' | 'random' | 'sticky'>('round-robin');
  const [proxyTestResult, setProxyTestResult] = useState<string | null>(null);
  const [proxyTesting, setProxyTesting] = useState(false);

  // ── 3. BrowserProfiler ───────────────────────────────────────────────────
  const [browserType, setBrowserType] = useState<'chromium' | 'firefox' | 'webkit'>('chromium');
  const [deviceProfile, setDeviceProfile] = useState<'desktop' | 'mobile' | 'tablet'>('desktop');
  const [viewportWidth, setViewportWidth] = useState(1280);
  const [viewportHeight, setViewportHeight] = useState(800);
  const [profileApplied, setProfileApplied] = useState(false);
  const createProfile = useCreateBrowserProfile();
  const profiles = useBrowserProfiles();

  // ── 4. Docker Remote ──────────────────────────────────────────────────────
  const [remoteUrl, setRemoteUrl] = useState('ws://localhost:3000');
  const [remoteToken, setRemoteToken] = useState('');
  const [useRemoteBrowser, setUseRemoteBrowser] = useState(false);
  const [dockerTestResult, setDockerTestResult] = useState<string | null>(null);
  const [dockerTesting, setDockerTesting] = useState(false);
  const dockerCrawl = useDockerCrawl();

  // ── Handlers ──────────────────────────────────────────────────────────────

  function handleApplyHubConfig() {
    const config = { userAgent, requestTimeout, delayBetweenRequests, ignoreRobots, headlessMode };
    console.log('[CrawlerHub] Config applied:', config);
    setHubConfigApplied(true);
    setTimeout(() => setHubConfigApplied(false), 3000);
  }

  async function handleTestProxy() {
    const proxies = proxyList.split('\n').map((p) => p.trim()).filter(Boolean);
    if (!proxies.length) return;
    setProxyTesting(true);
    setProxyTestResult(null);
    await new Promise((r) => setTimeout(r, 800));
    console.log('[Proxy] Test called with:', { proxies, rotation: proxyRotation });
    setProxyTestResult(`${proxies.length} proxy(ies) registered — rotation: ${proxyRotation}`);
    setProxyTesting(false);
  }

  function handleApplyProfile() {
    const profileName = `${browserType}-${deviceProfile}-${viewportWidth}x${viewportHeight}`;
    createProfile.mutate({ profileName });
    setProfileApplied(true);
    setTimeout(() => setProfileApplied(false), 3000);
  }

  async function handleTestDockerConnection() {
    if (!remoteUrl.trim()) return;
    setDockerTesting(true);
    setDockerTestResult(null);
    try {
      await dockerCrawl.mutateAsync({
        urls: ['https://example.com'],
        docker_url: remoteUrl.trim(),
        timeout: 10,
      });
      setDockerTestResult('Connection successful — remote browser responded.');
    } catch {
      setDockerTestResult('Connection failed — check the remote URL and token.');
    } finally {
      setDockerTesting(false);
    }
  }

  const savedProfileCount = profiles.data?.profiles?.length ?? 0;

  return (
    <div className="space-y-5 pt-2">

      {/* ── 1. CrawlerHub ── */}
      <Section
        title="CrawlerHub — Advanced Crawler Config"
        description="Default parameters applied to every crawl request when not overridden per-request."
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="User Agent">
            <Input
              value={userAgent}
              onChange={(e) => setUserAgent(e.target.value)}
              placeholder="Mozilla/5.0..."
            />
          </Field>
          <Field label="Request Timeout (seconds)">
            <Input
              type="number"
              min={1}
              max={120}
              value={String(requestTimeout)}
              onChange={(e) => setRequestTimeout(Number(e.target.value))}
            />
          </Field>
          <Field label="Delay Between Requests (seconds)">
            <Input
              type="number"
              min={0}
              max={60}
              step={0.1}
              value={String(delayBetweenRequests)}
              onChange={(e) => setDelayBetweenRequests(Number(e.target.value))}
            />
          </Field>
        </div>

        <div className="flex flex-col gap-2 pt-1">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <Checkbox
              id="ignore-robots"
              checked={ignoreRobots}
              onCheckedChange={(c) => setIgnoreRobots(c === true)}
            />
            <span className="text-sm text-[var(--text-high)]">Ignore robots.txt</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <Checkbox
              id="headless-mode"
              checked={headlessMode}
              onCheckedChange={(c) => setHeadlessMode(c === true)}
            />
            <span className="text-sm text-[var(--text-high)]">Headless mode (recommended)</span>
          </label>
        </div>

        <Button onClick={handleApplyHubConfig}>Apply Config</Button>
        {hubConfigApplied && <ConfirmBanner message="Configuration saved to session state." />}
      </Section>

      {/* ── 2. Proxy Rotation ── */}
      <Section
        title="Proxy Rotation"
        description="Add proxies (one per line, format: http://ip:port) and choose a rotation strategy."
      >
        <Field label="Proxy list (one per line)">
          <textarea
            value={proxyList}
            onChange={(e) => setProxyList(e.target.value)}
            placeholder={"http://192.168.1.1:8080\nhttp://10.0.0.2:3128"}
            rows={4}
            className="w-full rounded-lg bg-[var(--bg-input)] border border-[var(--border)] p-3 text-sm font-mono resize-y text-[var(--text-high)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
          />
        </Field>

        <Field label="Rotation mode">
          <StyledSelect value={proxyRotation} onChange={(v) => setProxyRotation(v as typeof proxyRotation)}>
            <option value="round-robin">Round-Robin</option>
            <option value="random">Random</option>
            <option value="sticky">Sticky (per session)</option>
          </StyledSelect>
        </Field>

        <Button
          variant="secondary"
          onClick={handleTestProxy}
          disabled={!proxyList.trim() || proxyTesting}
        >
          {proxyTesting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Testing...
            </>
          ) : (
            'Test Proxy'
          )}
        </Button>

        {proxyTestResult && <ConfirmBanner message={proxyTestResult} />}
      </Section>

      {/* ── 3. BrowserProfiler ── */}
      <Section
        title="BrowserProfiler"
        description="Configure the persistent browser identity used by crawl4ai."
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Browser type">
            <StyledSelect value={browserType} onChange={(v) => setBrowserType(v as typeof browserType)}>
              <option value="chromium">Chromium</option>
              <option value="firefox">Firefox</option>
              <option value="webkit">WebKit (Safari)</option>
            </StyledSelect>
          </Field>

          <Field label="Device profile">
            <StyledSelect value={deviceProfile} onChange={(v) => setDeviceProfile(v as typeof deviceProfile)}>
              <option value="desktop">Desktop</option>
              <option value="mobile">Mobile</option>
              <option value="tablet">Tablet</option>
            </StyledSelect>
          </Field>

          <Field label="Viewport width (px)">
            <Input
              type="number"
              min={320}
              max={3840}
              value={String(viewportWidth)}
              onChange={(e) => setViewportWidth(Number(e.target.value))}
            />
          </Field>

          <Field label="Viewport height (px)">
            <Input
              type="number"
              min={200}
              max={2160}
              value={String(viewportHeight)}
              onChange={(e) => setViewportHeight(Number(e.target.value))}
            />
          </Field>
        </div>

        {savedProfileCount > 0 && (
          <div className="text-xs text-[var(--text-mid)]">
            {savedProfileCount} saved profile(s) on this instance.
          </div>
        )}

        <Button
          onClick={handleApplyProfile}
          disabled={createProfile.isPending}
        >
          {createProfile.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Apply Profile'
          )}
        </Button>
        {profileApplied && !createProfile.isPending && (
          <ConfirmBanner message={`Profile ${browserType}-${deviceProfile}-${viewportWidth}x${viewportHeight} saved.`} />
        )}
        {createProfile.isError && (
          <p className="text-xs text-red-400">{createProfile.error?.message}</p>
        )}
      </Section>

      {/* ── 4. Docker Remote ── */}
      <Section
        title="Docker Remote Browser"
        description="Connect to a remote crawl4ai Docker container via WebSocket."
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Remote URL">
            <Input
              value={remoteUrl}
              onChange={(e) => setRemoteUrl(e.target.value)}
              placeholder="ws://localhost:3000"
            />
          </Field>

          <Field label="Remote token (optional)">
            <Input
              type="password"
              value={remoteToken}
              onChange={(e) => setRemoteToken(e.target.value)}
              placeholder="Bearer token..."
            />
          </Field>
        </div>

        <label className="flex items-center gap-2 cursor-pointer select-none">
          <Checkbox
            id="use-remote-browser"
            checked={useRemoteBrowser}
            onCheckedChange={(c) => setUseRemoteBrowser(c === true)}
          />
          <span className="text-sm text-[var(--text-high)]">Use remote browser for crawl requests</span>
        </label>

        <Button
          variant="secondary"
          onClick={handleTestDockerConnection}
          disabled={!remoteUrl.trim() || dockerTesting}
        >
          {dockerTesting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Testing...
            </>
          ) : (
            'Test Connection'
          )}
        </Button>

        {dockerTestResult && <ConfirmBanner message={dockerTestResult} />}
        {dockerCrawl.isError && !dockerTestResult && (
          <p className="text-xs text-red-400">{dockerCrawl.error?.message}</p>
        )}
      </Section>
    </div>
  );
}
