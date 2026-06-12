import { Clock, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Task } from '../../types';

interface TaskItemProps {
  task: Task;
  className?: string;
}

const statusConfig: Record<Task['status'], { icon: typeof Clock; label: string; color: string }> = {
  pending: { icon: Clock, label: '待处理', color: 'text-slate-400' },
  running: { icon: Loader2, label: '执行中', color: 'text-blue-500' },
  completed: { icon: CheckCircle, label: '已完成', color: 'text-emerald-500' },
  failed: { icon: AlertCircle, label: '失败', color: 'text-red-500' },
};

export function TaskItem({ task, className }: TaskItemProps) {
  const config = statusConfig[task.status];
  const Icon = config.icon;

  return (
    <div className={cn('flex items-center gap-3 px-4 py-3', className)}>
      <Icon className={cn('w-4 h-4 shrink-0', config.color, task.status === 'running' && 'animate-spin')} />
      <span className="text-sm text-foreground flex-1">{task.title}</span>
      <span className={cn(
        'text-xs px-2 py-0.5 rounded-full font-medium',
        task.status === 'completed' ? 'bg-emerald-50 text-emerald-600' :
        task.status === 'running' ? 'bg-blue-50 text-blue-600' :
        task.status === 'failed' ? 'bg-red-50 text-red-600' :
        'bg-slate-50 text-slate-500'
      )}>
        {config.label}
      </span>
    </div>
  );
}
