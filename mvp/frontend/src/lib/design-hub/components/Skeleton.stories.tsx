import type { Meta, StoryObj } from '@storybook/react';
import { Skeleton } from './Skeleton';

const meta = {
  title: 'Components/Skeleton',
  component: Skeleton,
  tags: ['autodocs'],
} satisfies Meta<typeof Skeleton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Line: Story = {
  render: () => (
    <Skeleton style={{ height: '16px', width: '240px' }} />
  ),
};

export const Card: Story = {
  render: () => (
    <Skeleton style={{ height: '128px', width: '320px' }} />
  ),
};

export const List: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '280px' }}>
      <Skeleton style={{ height: '16px', width: '100%' }} />
      <Skeleton style={{ height: '16px', width: '80%' }} />
      <Skeleton style={{ height: '16px', width: '60%' }} />
    </div>
  ),
};
