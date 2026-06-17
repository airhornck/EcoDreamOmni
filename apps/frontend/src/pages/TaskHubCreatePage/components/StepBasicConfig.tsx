import type { PlatformSchema, AccountOption } from '../../../stores/taskHubStore'

interface StepBasicConfigProps {
  name: string
  platform: string
  contentFormat: string
  accountId: string
  priority: number
  errors: Record<string, string>
  platformSchemas: PlatformSchema[]
  availableContentFormats: Array<{ format_name: string }>
  filteredAccounts: AccountOption[]
  onPlatformChange: (platformId: string) => void
  onContentFormatChange: (formatName: string) => void
  onUpdateField: (key: string, value: unknown) => void
  onSave?: () => void
  onCancel?: () => void
  onClear?: () => void
}

export function StepBasicConfig({
  name,
  platform,
  contentFormat,
  accountId,
  priority,
  errors,
  platformSchemas,
  availableContentFormats,
  filteredAccounts,
  onPlatformChange,
  onContentFormatChange,
  onUpdateField,
  onSave,
  onCancel,
  onClear,
}: StepBasicConfigProps) {
  return (
    <div className="space-y-5">
      <h3 className="text-base font-semibold">基础配置</h3>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">
          任务名称 <span className="text-destructive">*</span>
        </label>
        <input
          type="text"
          placeholder="输入任务名称"
          value={name}
          onChange={(e) => onUpdateField('name', e.target.value)}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        />
        {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">
          目标平台 <span className="text-destructive">*</span>
        </label>
        <select
          value={platform}
          onChange={(e) => onPlatformChange(e.target.value)}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        >
          <option value="">选择平台</option>
          {platformSchemas.map((s) => (
            <option key={s.platform_id} value={s.platform_id}>
              {s.display_name}
            </option>
          ))}
        </select>
        {errors.platform && <p className="text-xs text-destructive">{errors.platform}</p>}
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">
          内容格式 <span className="text-destructive">*</span>
        </label>
        <select
          value={contentFormat}
          onChange={(e) => onContentFormatChange(e.target.value)}
          disabled={!platform || availableContentFormats.length === 0}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm disabled:opacity-50"
        >
          <option value="">
            {platform
              ? availableContentFormats.length > 0
                ? '选择内容格式'
                : '该平台暂无格式数据'
              : '请先选择平台'}
          </option>
          {availableContentFormats.map((cf) => (
            <option key={cf.format_name} value={cf.format_name}>
              {cf.format_name}
            </option>
          ))}
        </select>
        {errors.contentFormat && (
          <p className="text-xs text-destructive">{errors.contentFormat}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">
          目标账号 <span className="text-destructive">*</span>
        </label>
        <select
          value={accountId}
          onChange={(e) => onUpdateField('accountId', e.target.value)}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        >
          <option value="">{platform ? '选择账号' : '请先选择平台'}</option>
          {filteredAccounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.username} ({a.platform})
            </option>
          ))}
        </select>
        {errors.accountId && <p className="text-xs text-destructive">{errors.accountId}</p>}
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">优先级</label>
        <select
          value={priority}
          onChange={(e) => onUpdateField('priority', Number(e.target.value))}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        >
          <option value={0}>P0 — 最高</option>
          <option value={25}>P1 — 高</option>
          <option value={50}>P2 — 普通</option>
          <option value={75}>P3 — 低</option>
          <option value={100}>P4 — 最低</option>
        </select>
      </div>

      {(onSave || onCancel || onClear) && (
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
          {onClear && (
            <button
              type="button"
              onClick={onClear}
              className="px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              清除
            </button>
          )}
          {onSave && (
            <button
              type="button"
              onClick={onSave}
              className="px-3 py-1.5 rounded-md text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              暂存节点
            </button>
          )}
        </div>
      )}
    </div>
  )
}
