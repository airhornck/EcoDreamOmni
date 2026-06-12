import { useAlertStream } from '../hooks/useAlertStream'
import { AlertBanner } from './ui/AlertBanner'
import { Wifi, WifiOff } from 'lucide-react'

export function AlertStreamBanner() {
  const { alerts, isConnected, error, dismissAlert } = useAlertStream()

  return (
    <div className="space-y-2">
      {/* Connection status bar */}
      <div className="flex items-center gap-2 px-5 py-2 border-b border-border">
        {isConnected ? (
          <Wifi className="w-3.5 h-3.5 text-success" />
        ) : (
          <WifiOff className="w-3.5 h-3.5 text-muted-foreground" />
        )}
        <span className={`text-xs ${isConnected ? 'text-success' : 'text-muted-foreground'}`}>
          {isConnected ? '实时告警已连接' : '实时告警未连接'}
        </span>
        {error && <span className="text-xs text-destructive ml-2">{error}</span>}
      </div>

      {/* Streamed alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2 px-5 pb-4">
          {alerts.map((alert) => (
            <AlertBanner
              key={alert.id}
              variant={alert.level === 'emergency' ? 'danger' : alert.level}
              title={alert.title}
              description={alert.message}
              onDismiss={() => dismissAlert(alert.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
