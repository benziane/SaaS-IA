import type { Meta, StoryObj } from '@storybook/react';
import { Separator } from './Separator';

const meta = {
  title: 'Components/Separator',
  component: Separator,
  tags: ['autodocs'],
} satisfies Meta<typeof Separator>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Horizontal: Story = {
  render: () => (
    <div style={{ width: '300px' }}>
      <p style={{ fontSize: '14px', color: 'var(--text-mid)', marginBottom: '12px' }}>Section above</p>
      <Separator />
      <p style={{ fontSize: '14px', color: 'var(--text-mid)', marginTop: '12px' }}>Section below</p>
    </div>
  ),
};

export const Vertical: Story = {
  render: () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', height: '32px' }}>
      <span style={{ fontSize: '14px', color: 'var(--text-mid)' }}>Home</span>
      <Separator orientation="vertical" />
      <span style={{ fontSize: '14px', color: 'var(--text-mid)' }}>Projects</span>
      <Separator orientation="vertical" />
      <span style={{ fontSize: '14px', color: 'var(--text-mid)' }}>Settings</span>
    </div>
  ),
};
