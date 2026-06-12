import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardContent, CardHeader, CardFooter } from './Card';
import { Button } from './Button';

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  tags: ['autodocs'],
  argTypes: {
    hover: { control: 'boolean' },
    shadow: { control: 'select', options: ['none', 'sm', 'md'] },
  },
};

export default meta;
type Story = StoryObj<typeof Card>;

export const Default: Story = {
  args: {
    children: <CardContent>这是卡片内容区域</CardContent>,
  },
};

export const WithHeader: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <h3 className="text-sm font-semibold">卡片标题</h3>
      </CardHeader>
      <CardContent>卡片正文内容</CardContent>
      <CardFooter>
        <Button size="sm">确认</Button>
      </CardFooter>
    </Card>
  ),
};

export const Hoverable: Story = {
  args: {
    hover: true,
    shadow: 'sm',
    children: <CardContent>悬停查看效果</CardContent>,
  },
};
