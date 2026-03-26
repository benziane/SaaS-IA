import type { Meta, StoryObj } from '@storybook/react';
import { Alert, AlertTitle, AlertDescription } from './Alert';

const meta = {
  title: 'Components/Alert',
  component: Alert,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'info', 'success', 'warning', 'destructive'],
    },
  },
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Alert>
      <AlertTitle>Default Alert</AlertTitle>
      <AlertDescription>A standard notification.</AlertDescription>
    </Alert>
  ),
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <Alert variant="default"><AlertTitle>Default</AlertTitle><AlertDescription>Standard notification.</AlertDescription></Alert>
      <Alert variant="info"><AlertTitle>Info</AlertTitle><AlertDescription>Something informational.</AlertDescription></Alert>
      <Alert variant="success"><AlertTitle>Success</AlertTitle><AlertDescription>Action completed!</AlertDescription></Alert>
      <Alert variant="warning"><AlertTitle>Warning</AlertTitle><AlertDescription>Check your input.</AlertDescription></Alert>
      <Alert variant="destructive"><AlertTitle>Error</AlertTitle><AlertDescription>Something went wrong.</AlertDescription></Alert>
    </div>
  ),
};
