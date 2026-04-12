/**
 * DesignTokens.stories.tsx
 * Visual regression reference for the SaaS-IA design token system.
 * Verifies that all --bg-*, --text-*, --border, --accent tokens render
 * correctly in both dark (default) and light modes.
 */
import type { Meta, StoryObj } from '@storybook/react';

const TOKEN_GROUPS = [
  {
    label: 'Backgrounds',
    tokens: [
      { name: '--bg-app', label: 'bg-app' },
      { name: '--bg-surface', label: 'bg-surface' },
      { name: '--bg-elevated', label: 'bg-elevated' },
      { name: '--bg-overlay', label: 'bg-overlay' },
    ],
  },
  {
    label: 'Text',
    tokens: [
      { name: '--text-high', label: 'text-high' },
      { name: '--text-mid', label: 'text-mid' },
      { name: '--text-low', label: 'text-low' },
    ],
  },
  {
    label: 'Accent',
    tokens: [
      { name: '--accent', label: 'accent' },
      { name: '--accent-dim', label: 'accent-dim' },
      { name: '--accent-glow', label: 'accent-glow' },
    ],
  },
  {
    label: 'Borders',
    tokens: [
      { name: '--border', label: 'border' },
      { name: '--border-subtle', label: 'border-subtle' },
    ],
  },
];

function Swatch({ name, label }: { name: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 8,
          background: `var(${name})`,
          border: '1px solid var(--border)',
          flexShrink: 0,
        }}
      />
      <div>
        <div style={{ color: 'var(--text-high)', fontSize: 13, fontWeight: 500 }}>{label}</div>
        <div style={{ color: 'var(--text-low)', fontSize: 11, fontFamily: 'monospace' }}>{name}</div>
      </div>
    </div>
  );
}

function TokenShowcase() {
  return (
    <div
      style={{
        background: 'var(--bg-app)',
        minHeight: '100vh',
        padding: 32,
        fontFamily: 'Inter, sans-serif',
      }}
    >
      <h1 style={{ color: 'var(--text-high)', fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
        Design Token System
      </h1>
      <p style={{ color: 'var(--text-mid)', fontSize: 13, marginBottom: 32 }}>
        Toggle data-mode=&quot;light&quot; on &lt;html&gt; to verify light mode rendering.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 32 }}>
        {TOKEN_GROUPS.map((group) => (
          <div key={group.label}>
            <h2
              style={{
                color: 'var(--text-low)',
                fontSize: 10,
                fontWeight: 600,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                marginBottom: 16,
              }}
            >
              {group.label}
            </h2>
            {group.tokens.map((t) => (
              <Swatch key={t.name} {...t} />
            ))}
          </div>
        ))}
      </div>

      {/* Component smoke-test */}
      <div style={{ marginTop: 48 }}>
        <h2
          style={{
            color: 'var(--text-low)',
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 16,
          }}
        >
          Component Smoke Test
        </h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            style={{
              background: 'var(--accent)',
              color: 'var(--bg-app)',
              border: 'none',
              borderRadius: 6,
              padding: '8px 16px',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Primary CTA
          </button>
          <button
            style={{
              background: 'transparent',
              color: 'var(--text-high)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '8px 16px',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            Secondary
          </button>
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '12px 16px',
              color: 'var(--text-high)',
              fontSize: 13,
            }}
          >
            Surface card
          </div>
          <div
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '12px 16px',
              color: 'var(--text-mid)',
              fontSize: 13,
            }}
          >
            Elevated surface
          </div>
        </div>
      </div>
    </div>
  );
}

const meta = {
  title: 'Design System/Tokens',
  component: TokenShowcase,
  tags: ['autodocs', 'a11y'],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          'Visual reference for all design tokens. Set `data-mode="light"` on the html element to test light mode. Zero hardcoded colors — everything via CSS custom properties.',
      },
    },
  },
} satisfies Meta<typeof TokenShowcase>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DarkMode: Story = {
  parameters: {
    backgrounds: { disable: true },
  },
};

export const LightMode: Story = {
  decorators: [
    (Story) => {
      return (
        <div data-mode="light" data-mui-color-scheme="light">
          <Story />
        </div>
      );
    },
  ],
  parameters: {
    backgrounds: { disable: true },
  },
};
