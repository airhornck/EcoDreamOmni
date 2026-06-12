import { Monitor, Info } from 'lucide-react'
import { Card, CardContent } from '../../../components/ui/Card'
import { Badge } from '../../../components/ui/Badge'
import type { Agent } from '../../../types/api'
import type { AccountOption, PersonaOption } from '../../../stores/taskHubStore'

interface StepPublishConfirmProps {
  name: string
  platform: string
  contentFormat: string
  accountId: string
  personaId: string
  agentId: string
  priority: number
  scheduleMode: string
  scheduledAt: string
  cronSchedule: string
  cronDateStart: string
  cronDateEnd: string
  cronTime: string
  cronMode: string
  platformDisplayName: string
  accounts: AccountOption[]
  personas: PersonaOption[]
  agents: Agent[]
  onUpdateField: (key: string, value: unknown) => void
  onSave?: () => void
  onCancel?: () => void
}

export function StepPublishConfirm({
  name,
  platform,
  contentFormat,
  accountId,
  personaId,
  agentId,
  priority,
  scheduleMode,
  scheduledAt,
  cronSchedule,
  cronDateStart,
  cronDateEnd,
  cronTime,
  cronMode,
  platformDisplayName,
  accounts,
  personas,
  agents,
  onUpdateField,
  onSave,
  onCancel,
}: StepPublishConfirmProps) {
  return (
    <div className="space-y-5">
      <h3 className="text-base font-semibold">发布确认</h3>

      {/* 执行方式 */}
      <div className="space-y-2">
        <label className="text-sm font-medium">执行方式</label>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name="scheduleMode"
              checked={scheduleMode === 'immediate'}
              onChange={() => onUpdateField('scheduleMode', 'immediate')}
            />
            立即执行
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name="scheduleMode"
              checked={scheduleMode === 'scheduled'}
              onChange={() => onUpdateField('scheduleMode', 'scheduled')}
            />
            定时执行
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name="scheduleMode"
              checked={scheduleMode === 'cron'}
              onChange={() => onUpdateField('scheduleMode', 'cron')}
            />
            循环执行
          </label>
        </div>
        {scheduleMode === 'scheduled' && (
          <input
            type="datetime-local"
            value={scheduledAt}
            onChange={(e) => onUpdateField('scheduledAt', e.target.value)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm mt-2"
          />
        )}
        {scheduleMode === 'cron' && (
          <CronScheduler
            cronSchedule={cronSchedule}
            cronDateStart={cronDateStart}
            cronDateEnd={cronDateEnd}
            cronTime={cronTime}
            cronMode={cronMode}
            onUpdateField={onUpdateField}
          />
        )}
      </div>

      {/* 系统注入摘要 */}
      {platform && (
        <div className="space-y-2 pt-2 border-t border-border">
          <label className="text-sm font-medium flex items-center gap-1.5">
            <Monitor className="w-3.5 h-3.5" />
            系统注入摘要
          </label>
          <div className="p-3 rounded-lg bg-secondary/30 text-xs space-y-1.5">
            <div className="flex items-start gap-1.5">
              <Info className="w-3.5 h-3.5 text-muted-foreground mt-0.5 shrink-0" />
              <span className="text-muted-foreground">
                <strong>BrandKnowledge：</strong>宠物健康知识库已加载，内容生成时将自动注入品牌合规约束
              </span>
            </div>
            <div className="flex items-start gap-1.5">
              <Info className="w-3.5 h-3.5 text-muted-foreground mt-0.5 shrink-0" />
              <span className="text-muted-foreground">
                <strong>PlatformRule：</strong>
                {platform === 'xiaohongshu' && '小红书 L3 日配额检查已启用，L4 动态风控已启用'}
                {platform === 'douyin' && '抖音内容审核规则已加载，带货内容需标注'}
                {platform === 'wechat_channels' && '视频号直播规范已加载，医疗内容限制已启用'}
                {platform === 'bilibili' && '哔哩哔哩创作公约已加载，分区投稿规范已启用'}
                {!['xiaohongshu', 'douyin', 'wechat_channels', 'bilibili'].includes(platform) && '平台规则已加载'}
              </span>
            </div>
            {contentFormat && (
              <div className="flex items-start gap-1.5">
                <Info className="w-3.5 h-3.5 text-muted-foreground mt-0.5 shrink-0" />
                <span className="text-muted-foreground">
                  <strong>PlatformSchema：</strong>内容格式「{contentFormat}」字段约束已加载，发布前将自动校验
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 配置汇总 */}
      <div className="space-y-2 pt-2 border-t border-border">
        <label className="text-sm font-medium">配置汇总</label>
        <Card>
          <CardContent className="p-4 space-y-2 text-sm">
            <SummaryRow label="任务名称" value={name} />
            <SummaryRow label="目标平台" value={platformDisplayName} />
            <SummaryRow label="内容格式" value={contentFormat || '-'} />
            <SummaryRow
              label="目标账号"
              value={accounts.find((a) => a.id === accountId)?.username || accountId}
            />
            <SummaryRow
              label="Persona"
              value={personas.find((p) => p.id === personaId)?.name || personaId}
            />
            <SummaryRow
              label="执行 Agent"
              value={agents.find((a) => a.id === agentId)?.name || agentId || '-'}
            />
            <div className="flex justify-between">
              <span className="text-muted-foreground">优先级</span>
              <Badge variant="default">P{priority}</Badge>
            </div>
            <SummaryRow
              label="执行方式"
              value={
                scheduleMode === 'immediate'
                  ? '立即执行'
                  : scheduleMode === 'scheduled'
                  ? `定时: ${scheduledAt}`
                  : cronMode === 'custom' && cronDateStart && cronDateEnd
                  ? `循环: ${cronDateStart}~${cronDateEnd} ${cronTime}`
                  : `循环: ${cronSchedule}`
              }
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            取消
          </button>
        )}
        {onSave && (
          <button
            type="button"
            onClick={onSave}
            className="px-3 py-1.5 rounded-md text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            激活流水线并部署
          </button>
        )}
      </div>
    </div>
  )
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

function CronScheduler({
  cronSchedule,
  cronDateStart,
  cronDateEnd,
  cronTime,
  cronMode,
  onUpdateField,
}: {
  cronSchedule: string
  cronDateStart: string
  cronDateEnd: string
  cronTime: string
  cronMode: string
  onUpdateField: (key: string, value: unknown) => void
}) {
  const presets = [
    { label: '每天早9点', value: '0 9 * * *' },
    { label: '每晚8点', value: '0 20 * * *' },
    { label: '每周一早9点', value: '0 9 * * 1' },
    { label: '每月1号早9点', value: '0 9 1 * *' },
    { label: '每小时', value: '0 * * * *' },
  ]

  return (
    <div className="space-y-3 mt-2">
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-1.5 text-xs">
          <input
            type="radio"
            name="cronMode"
            checked={cronMode === 'preset'}
            onChange={() => onUpdateField('cronMode', 'preset')}
          />
          固定循环
        </label>
        <label className="flex items-center gap-1.5 text-xs">
          <input
            type="radio"
            name="cronMode"
            checked={cronMode === 'custom'}
            onChange={() => onUpdateField('cronMode', 'custom')}
          />
          自定义循环
        </label>
      </div>

      {cronMode === 'preset' && (
        <div className="flex flex-wrap gap-1.5">
          {presets.map((preset) => (
            <button
              key={preset.value}
              type="button"
              onClick={() => onUpdateField('cronSchedule', preset.value)}
              className={`px-2 py-1 rounded-md text-xs border transition-colors ${
                cronSchedule === preset.value
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-background border-border hover:bg-secondary'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      )}

      {cronMode === 'custom' && (
        <div className="space-y-2 p-3 rounded-lg bg-secondary/20 border border-border">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground shrink-0">日期范围</label>
            <input
              type="date"
              value={cronDateStart}
              onChange={(e) => onUpdateField('cronDateStart', e.target.value)}
              className="flex-1 h-8 px-2 rounded-lg border border-border bg-background text-xs"
            />
            <span className="text-xs text-muted-foreground">至</span>
            <input
              type="date"
              value={cronDateEnd}
              onChange={(e) => onUpdateField('cronDateEnd', e.target.value)}
              className="flex-1 h-8 px-2 rounded-lg border border-border bg-background text-xs"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground shrink-0">执行时间</label>
            <input
              type="time"
              value={cronTime}
              onChange={(e) => {
                onUpdateField('cronTime', e.target.value)
                const [hour, min] = e.target.value.split(':')
                onUpdateField('cronSchedule', `${min} ${hour} * * *`)
              }}
              className="h-8 px-2 rounded-lg border border-border bg-background text-xs"
            />
          </div>
          <div className="text-[10px] text-muted-foreground">
            Cron: <code className="text-foreground">{cronSchedule || '请选择时间'}</code>
            {cronDateStart && cronDateEnd && (
              <span> · 范围: {cronDateStart} ~ {cronDateEnd}</span>
            )}
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        格式：分 时 日 月 周（如 <code>0 9 * * 1</code> 表示每周一上午9点）
      </p>
    </div>
  )
}
