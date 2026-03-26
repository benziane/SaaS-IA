import type { Meta, StoryObj, Decorator } from '@storybook/react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from './Tooltip';
import { Button } from './Button';

const withTooltipProvider: Decorator = (Story) => (
  <TooltipProvider>
    <Story />
  </TooltipProvider>
);

const meta: Meta<typeof Tooltip> = {
  title: 'Components/Tooltip',
  component: Tooltip,
  tags: ['autodocs'],
  decorators: [withTooltipProvider],
};

export default meta;
type Story = StoryObj<typeof Tooltip>;

export const Default: Story = {
  render: () => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover me</Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Helpful tooltip</p>
      </TooltipContent>
    </Tooltip>
  ),
};

export const LongText: Story = {
  render: () => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost">More info</Button>
      </TooltipTrigger>
      <TooltipContent style={{ maxWidth: '240px' }}>
        <p>This is a longer tooltip that provides additional context about the action. Use tooltips to clarify icon-only buttons or complex controls.</p>
      </TooltipContent>
    </Tooltip>
  ),
};
