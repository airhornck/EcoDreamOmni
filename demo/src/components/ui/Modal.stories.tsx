import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';

const meta: Meta<typeof Modal> = {
  title: 'UI/Modal',
  component: Modal,
  tags: ['autodocs'],
  argTypes: {
    maxWidth: { control: 'select', options: ['sm', 'md', 'lg', 'xl'] },
  },
};

export default meta;
type Story = StoryObj<typeof Modal>;

export const Default: Story = {
  render: () => {
    const [open, setOpen] = useState(true);
    return (
      <>
        <Button onClick={() => setOpen(true)}>打开弹窗</Button>
        <Modal isOpen={open} onClose={() => setOpen(false)} title="示例弹窗">
          <div className="p-6">
            <p className="text-sm text-muted-foreground">这是弹窗内容区域。</p>
          </div>
        </Modal>
      </>
    );
  },
};
