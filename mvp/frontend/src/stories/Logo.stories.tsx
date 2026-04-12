/**
 * Logo.stories.tsx
 * Visual regression stories for the Logo component.
 * Verifies: token-aligned colors, collapsed/expanded states, dark + light modes.
 */
import type { Meta, StoryObj } from '@storybook/react';

/**
 * Logo uses useVerticalNav and useSettings hooks from Sneat.
 * In Storybook, we render the visual output directly as a controlled snapshot.
 */
import { Sparkles } from 'lucide-react';

function LogoPreview({
  collapsed = false,
  color,
}: {
  collapsed?: boolean;
  color?: string;
}) {
  return (
    <div className="flex items-center">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
        <Sparkles className="h-4 w-4 text-[var(--accent)]" />
      </div>
      {!collapsed && (
        <span
          style={{
            color: color ?? 'var(--text-high)',
            fontSize: '1.75rem',
            lineHeight: 1,
            fontWeight: 700,
            letterSpacing: '0.15px',
            marginInlineStart: 8,
          }}
        >
          SaaS-IA
        </span>
      )}
    </div>
  );
}

const meta = {
  title: 'Layout/Logo',
  component: LogoPreview,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Logo component. Icon uses --bg-elevated + --border + --accent tokens. Text uses --text-high. No hardcoded colors.',
      },
    },
  },
} satisfies Meta<typeof LogoPreview>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Expanded: Story = {
  decorators: [
    (Story) => (
      <div style={{ background: 'var(--bg-surface)', padding: 24, borderRadius: 8 }}>
        <Story />
      </div>
    ),
  ],
};

export const Collapsed: Story = {
  args: { collapsed: true },
  decorators: [
    (Story) => (
      <div style={{ background: 'var(--bg-surface)', padding: 24, borderRadius: 8 }}>
        <Story />
      </div>
    ),
  ],
};

export const LightMode: Story = {
  decorators: [
    (Story) => (
      <div
        data-mode="light"
        data-mui-color-scheme="light"
        style={{ background: 'var(--bg-surface)', padding: 24, borderRadius: 8 }}
      >
        <Story />
      </div>
    ),
  ],
};

export const CustomColor: Story = {
  args: { color: 'var(--accent)' },
  decorators: [
    (Story) => (
      <div style={{ background: 'var(--bg-app)', padding: 24, borderRadius: 8 }}>
        <Story />
      </div>
    ),
  ],
};
