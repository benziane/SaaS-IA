import type { Meta, StoryObj } from '@storybook/react';
import { Textarea } from './Textarea';

const meta = {
  title: 'Components/Textarea',
  component: Textarea,
  tags: ['autodocs'],
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: 'Write your message here…',
    style: { width: '320px' },
  },
};

export const Disabled: Story = {
  args: {
    placeholder: 'This field is disabled',
    disabled: true,
    style: { width: '320px' },
  },
};

export const WithRows: Story = {
  args: {
    placeholder: 'Describe your project in detail…',
    rows: 6,
    style: { width: '320px' },
  },
};
