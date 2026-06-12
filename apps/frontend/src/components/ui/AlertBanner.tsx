import { cn } from '../../lib/utils'
import { AlertTriangle, AlertCircle, CheckCircle2, Info, X } from 'lucide-react'

export type AlertVariant = 'info' | 'warning' | 'danger' | 'success'

interface AlertBannerProps {
  variant?: AlertVariant
  title: string
  description?: string
  icon?: React.ReactNode
  onDismiss?: () => void
  className?: string
}

const variantConfig: Record<AlertVariant, { icon: typeof Info; style: string }> = {
  info: { icon: Info, style: 'bg-info-bg border-info-border text-info' },
  warning: { icon: AlertTriangle, style: 'bg-warning-bg border-warning-border text-warning' },
  danger: { icon: AlertCircle, style: 'bg-destructive/15 border-destructive/30 text-red-600' },
  success: { icon: CheckCircle2, style: 'bg-success-bg border-success-border text-success' },
}

export function AlertBanner({
  variant = 'info',
  title,
  description,
  icon,
  onDismiss,
  className,
}: AlertBannerProps) {
  const config = variantConfig[variant]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'relative flex items-start gap-3 rounded-xl border p-4',
        config.style,
        className
      )}
    >
      {icon ?? <Icon className="mt-0.5 h-5 w-5 shrink-0" />}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{title}</p>
        {description && <p className="text-sm opacity-90 mt-1">{description}</p>}
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="shrink-0 opacity-60 hover:opacity-100 transition-opacity"
          aria-label="关闭"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
