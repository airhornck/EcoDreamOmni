import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';
import { Sparkles, Send } from 'lucide-react';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'outline', 'ghost', 'danger'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    isLoading: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = { args: { children: '主要按钮' } };
export const Secondary: Story = { args: { children: '次要按钮', variant: 'secondary' } };
export const Outline: Story = { args: { children: '边框按钮', variant: 'outline' } };
export const Ghost: Story = { args: { children: '幽灵按钮', variant: 'ghost' } };
export const Danger: Story = { args: { children: '危险按钮', variant: 'danger' } };
export const Loading: Story = { args: { children: '加载中', isLoading: true } };
export const WithIcon: Story = {
  args: { children: <><Sparkles className="w-4 h-4" /> AI 生成</> },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-3">
      <Button>primary</Button>
      <Button variant="secondary">secondary</Button>
      <Button variant="outline">outline</Button>
      <Button variant="ghost">ghost</Button>
      <Button variant="danger">danger</Button>
    </div>
  ),
};

export const AllSizes: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
};
