import { useEffect } from 'react'
import { useDashboardStore } from '../stores/dashboardStore'
import { Card, CardContent, CardHeader } from './ui/Card'
import { Heart } from 'lucide-react'

function healthColor(score: number): string {
  if (score >= 80) return 'bg-success'
  if (score >= 60) return 'bg-warning'
  if (score >= 40) return 'bg-warning/150'
  return 'bg-destructive/150'
}

function healthTextColor(score: number): string {
  if (score >= 80) return 'text-success'
  if (score >= 60) return 'text-warning'
  if (score >= 40) return 'text-orange-600'
  return 'text-red-600'
}

export function AccountHealth() {
  const { accountPool, fetchAccountPool } = useDashboardStore()

  useEffect(() => {
    fetchAccountPool()
  }, [fetchAccountPool])

  return (
    <Card>
      <CardHeader className="flex items-center gap-2">
        <Heart className="w-4 h-4 text-primary" />
        <h2 className="text-base font-semibold text-foreground">账号健康</h2>
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid grid-cols-5 gap-4 px-5 py-2 text-xs font-medium text-muted-foreground border-b border-border">
          <span>账号</span>
          <span>阶段</span>
          <span>状态</span>
          <span className="col-span-2">健康分</span>
        </div>
        <div className="divide-y divide-border">
          {accountPool.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-muted-foreground">暂无账号数据</div>
          )}
          {accountPool.map((acc) => (
            <div key={acc.id} className="grid grid-cols-5 gap-4 px-5 py-3 items-center">
              <span className="text-sm font-medium text-foreground truncate">{acc.nickname}</span>
              <span className="text-xs text-muted-foreground">{acc.lifecycle_phase}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-muted-foreground w-fit">{acc.status}</span>
              <div className="col-span-2 flex items-center gap-2">
                <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${healthColor(acc.health_score)}`}
                    style={{ width: `${acc.health_score}%` }}
                  />
                </div>
                <span className={`text-sm font-semibold ${healthTextColor(acc.health_score)}`}>
                  {acc.health_score}
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
