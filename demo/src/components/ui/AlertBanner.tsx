import { cn } from '../../lib/utils';
import type { LucideIcon } from 'lucide-react';

export type AlertVariant = 'info' | 'warning' | 'danger' | 'success';

interface AlertBannerProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  variant?: AlertVariant;
  className?: string;
}

const variantStyles: Record<AlertVariant, string> = {
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  warning: 'bg-amber-50 border-amber-200 text-amber-800',
  danger: 'bg-red-50 border-red-200 text-red-800',
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
};

const iconStyles: Record<AlertVariant, string> = {
  info: 'text-blue-600',
  warning: 'text-amber-600',
  danger: 'text-red-600',
  success: 'text-emerald-600',
};

export function AlertBanner({ icon: Icon, title, description, variant = 'info', className }: AlertBannerProps) {
  return (
    <div className={cn('p-4 rounded-xl border flex items-start gap-3', variantStyles[variant], className)}>
      {Icon && <Icon className={cn('w-5 h-5 shrink-0 mt-0.5', iconStyles[variant])} />}
      <div>
        <p className="text-sm font-medium">{title}</p>
        {description && <p className="text-xs opacity-80 mt-0.5">{description}</p>}
      </div>
    </div>
  );
}
