import type { Meta, StoryObj } from '@storybook/react';
import { StatusBadge } from './StatusBadge';

const meta: Meta<typeof StatusBadge> = {
  title: 'Common/StatusBadge',
  component: StatusBadge,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof StatusBadge>;

export const Draft: Story = { args: { status: 'draft' } };
export const Reviewing: Story = { args: { status: 'reviewing' } };
export const Approved: Story = { args: { status: 'approved' } };
export const Published: Story = { args: { status: 'published' } };
export const Rejected: Story = { args: { status: 'rejected' } };

export const AllStatuses: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <StatusBadge status="draft" />
      <StatusBadge status="reviewing" />
      <StatusBadge status="approved" />
      <StatusBadge status="published" />
      <StatusBadge status="rejected" />
    </div>
  ),
};
