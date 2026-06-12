import type { Agent } from '../../../types/api'
import type { AccountOption, PersonaOption } from '../../../stores/taskHubStore'

interface StepSummaryItemProps {
  label?: string
  value: string | undefined
  fallback?: string
}

function StepSummaryItem({ label, value, fallback = '未选择' }: StepSummaryItemProps) {
  const displayValue = value?.trim() ? value : fallback
  return (
    <div className="bg-muted rounded px-2 py-1 truncate" title={displayValue}>
      {label ? `${label} ${displayValue}` : displayValue}
    </div>
  )
}

export interface Step1SummaryProps {
  name: string
  platformDisplayName: string
  contentFormat: string
  account?: AccountOption | null
  priority: number
}

export function Step1Summary({ name, platformDisplayName, contentFormat, account, priority }: Step1SummaryProps) {
  const priorityMap: Record<number, string> = {
    0: 'P0',
    25: 'P1',
    50: 'P2',
    75: 'P3',
    100: 'P4',
  }
  return (
    <div className="space-y-1">
      <StepSummaryItem value={name || '未填写任务名称'} />
      <StepSummaryItem label="🌐" value={platformDisplayName} />
      <StepSummaryItem label="📄" value={contentFormat} />
      <StepSummaryItem label="👤" value={account?.username || account?.id} />
      <StepSummaryItem label="⚡" value={`优先级 ${priorityMap[priority] ?? `P${priority}`}`} />
    </div>
  )
}

export interface Step2SummaryProps {
  persona?: PersonaOption | null
  elementCount: number
  variableCount: number
}

export function Step2Summary({ persona, elementCount, variableCount }: Step2SummaryProps) {
  return (
    <div className="space-y-1">
      <StepSummaryItem label="👤" value={persona?.name || persona?.id} />
      <StepSummaryItem label="⚡" value={`已选择 ${elementCount} 个策略元素`} />
      <StepSummaryItem label="🧮" value={`已生成 ${variableCount} 组变量`} />
    </div>
  )
}

export interface Step3SummaryProps {
  agent?: Agent | null
  recommendedAgent?: Agent | null
}

export function Step3Summary({ agent, recommendedAgent }: Step3SummaryProps) {
  return (
    <div className="space-y-1">
      <StepSummaryItem label="🤖" value={agent?.name || agent?.id} fallback="未选择 Agent" />
      {recommendedAgent && recommendedAgent.id !== agent?.id && (
        <StepSummaryItem label="✨" value={`推荐 ${recommendedAgent.name}`} />
      )}
    </div>
  )
}

export interface Step4SummaryProps {
  scheduleMode: string
  scheduledAt: string
  cronSchedule: string
  cronDateStart: string
  cronDateEnd: string
  cronTime: string
  cronMode: string
}

export function Step4Summary({
  scheduleMode,
  scheduledAt,
  cronSchedule,
  cronDateStart,
  cronDateEnd,
  cronTime,
  cronMode,
}: Step4SummaryProps) {
  const scheduleText =
    scheduleMode === 'immediate'
      ? '立即执行'
      : scheduleMode === 'scheduled'
      ? `定时: ${scheduledAt || '待填写'}`
      : cronMode === 'custom' && cronDateStart && cronDateEnd
      ? `循环: ${cronDateStart}~${cronDateEnd} ${cronTime}`
      : `循环: ${cronSchedule || '待配置'}`

  return (
    <div className="space-y-1">
      <StepSummaryItem label="⏰" value={scheduleText} />
      <StepSummaryItem label="📄" value="配置待确认" />
    </div>
  )
}
