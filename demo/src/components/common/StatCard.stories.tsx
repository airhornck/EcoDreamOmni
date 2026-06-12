import type { Meta, StoryObj } from '@storybook/react';
import { StatCard } from './StatCard';
import { BarChart3, CheckCircle2, TrendingUp, AlertTriangle } from 'lucide-react';

const meta: Meta<typeof StatCard> = {
  title: 'Common/StatCard',
  component: StatCard,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['default', 'primary', 'success', 'warning', 'danger'] },
  },
};

export default meta;
type Story = StoryObj<typeof StatCard>;

export const Default: Story = {
  args: { label: '已发布', value: 156, icon: BarChart3, variant: 'default' },
};

export const Success: Story = {
  args: { label: '覆盖率', value: '83%', icon: CheckCircle2, variant: 'success' },
};

export const Warning: Story = {
  args: { label: '待审核', value: 8, icon: AlertTriangle, variant: 'warning' },
};

export const Grid: Story = {
  render: () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard label="待生成" value={12} icon={BarChart3} variant="primary" />
      <StatCard label="已发布" value={156} icon={CheckCircle2} variant="success" />
      <StatCard label="互动增长" value="+23%" icon={TrendingUp} variant="primary" />
      <StatCard label="平均健康分" value={87} icon={CheckCircle2} variant="default" />
    </div>
  ),
};
