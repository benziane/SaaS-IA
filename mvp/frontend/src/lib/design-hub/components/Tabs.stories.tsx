import type { Meta, StoryObj } from '@storybook/react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';

const meta = {
  title: 'Components/Tabs',
  component: Tabs,
  tags: ['autodocs'],
} satisfies Meta<typeof Tabs>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Tabs defaultValue="overview" style={{ width: '400px' }}>
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="analytics">Analytics</TabsTrigger>
        <TabsTrigger value="settings">Settings</TabsTrigger>
      </TabsList>
      <TabsContent value="overview">
        <p style={{ fontSize: '14px', color: 'var(--text-mid)', padding: '12px 0' }}>
          Overview content — summary of key metrics and activity.
        </p>
      </TabsContent>
      <TabsContent value="analytics">
        <p style={{ fontSize: '14px', color: 'var(--text-mid)', padding: '12px 0' }}>
          Analytics content — charts and usage statistics.
        </p>
      </TabsContent>
      <TabsContent value="settings">
        <p style={{ fontSize: '14px', color: 'var(--text-mid)', padding: '12px 0' }}>
          Settings content — configure preferences and options.
        </p>
      </TabsContent>
    </Tabs>
  ),
};

export const TwoTabs: Story = {
  render: () => (
    <Tabs defaultValue="account" style={{ width: '320px' }}>
      <TabsList>
        <TabsTrigger value="account">Account</TabsTrigger>
        <TabsTrigger value="security">Security</TabsTrigger>
      </TabsList>
      <TabsContent value="account">
        <p style={{ fontSize: '14px', color: 'var(--text-mid)', padding: '12px 0' }}>
          Manage your account details and preferences.
        </p>
      </TabsContent>
      <TabsContent value="security">
        <p style={{ fontSize: '14px', color: 'var(--text-mid)', padding: '12px 0' }}>
          Update your password and security settings.
        </p>
      </TabsContent>
    </Tabs>
  ),
};
