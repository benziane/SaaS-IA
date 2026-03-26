import type { Meta, StoryObj } from '@storybook/react';
import { Input } from './Input';

const meta = {
  title: 'Components/Input',
  component: Input,
  tags: ['autodocs'],
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { placeholder: 'Enter text...' },
};

export const Disabled: Story = {
  args: { placeholder: 'Disabled', disabled: true },
};

export const Password: Story = {
  args: { type: 'password', placeholder: 'Password' },
};
