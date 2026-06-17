import { Sparkles, ShieldCheck } from 'lucide-react'
import { Badge } from '../../../components/ui/Badge'
import type { Agent } from '../../../types/api'

function AgentConstraintTags({ config }: { config: Record<string, unknown> }) {
  const snapshot = config?.platform_format_snapshot as Record<string, unknown> | undefined
  const safety = config?.safety_injection as Record<string, unknown> | undefined
  const tags: string[] = []

  if (snapshot?.platform_id && snapshot?.format_name) {
    tags.push(`${snapshot.platform_id} · ${snapshot.format_name}`)
  }

  const titleConstraints = snapshot?.title_constraints as Record<string, unknown> | undefined
  const bodyConstraints = snapshot?.body_constraints as Record<string, unknown> | undefined
  if (titleConstraints?.max_length) {
    tags.push(`标题≤${titleConstraints.max_length}字`)
  }
  if (bodyConstraints?.recommended) {
    tags.push(`正文${bodyConstraints.recommended}`)
  }

  const preCheck = safety?.pre_check_agents as string[] | undefined
  const postCheck = safety?.post_check_agents as string[] | undefined
  if (preCheck?.length || postCheck?.length) {
    const checks = [...(preCheck || []), ...(postCheck || [])]
    tags.push(`合规预检:${checks.join('/')}`)
  }

  if (tags.length === 0) return null
  return (
    <div className="mt-2 flex flex-wrap gap-1">
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] bg-secondary text-secondary-foreground"
        >
          <ShieldCheck className="w-3 h-3" />
          {tag}
        </span>
      ))}
    </div>
  )
}

interface StepAgentSelectProps {
  agents: Agent[]
  selectedAgentId: string
  recommendedAgentId: string | null
  platform: string
  contentFormat: string
  safetyConstraintCount?: number
  error?: string
  onSelect: (agentId: string) => void
  onSave?: () => void
  onClear?: () => void
}

export function StepAgentSelect({
  agents,
  selectedAgentId,
  recommendedAgentId,
  platform,
  contentFormat,
  safetyConstraintCount = 0,
  error,
  onSelect,
  onSave,
  onClear,
}: StepAgentSelectProps) {
  const filteredAgents = agents.filter(
    (a) =>
      a.status?.toUpperCase() === 'ACTIVE' &&
      (!platform || a.supported_platforms?.includes(platform)) &&
      (!contentFormat || a.supported_formats?.includes(contentFormat))
  )

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold">选择执行 Agent</h3>
        {recommendedAgentId && (
          <Badge variant="default" className="text-[10px] gap-0.5">
            <Sparkles className="w-3 h-3" />
            平台+格式最优匹配
          </Badge>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        系统根据 <strong>{platform || '全部平台'}</strong> +{' '}
        <strong>{contentFormat || '全部格式'}</strong> 筛选了以下可用 Agent
        {safetyConstraintCount > 0 && (
          <span className="ml-2 text-primary">
            · 已绑定 {safetyConstraintCount} 条安全约束
          </span>
        )}
      </p>

      {/* Agent 卡片网格 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {filteredAgents.map((agent) => {
          const isRecommended = recommendedAgentId === agent.id
          const isSelected = selectedAgentId === agent.id
          return (
            <button
              key={agent.id}
              type="button"
              onClick={() => onSelect(agent.id)}
              className={`relative text-left rounded-xl border p-4 transition-all ${
                isSelected
                  ? 'border-purple-500 bg-purple-50/50 shadow-sm'
                  : 'border-border bg-background hover:border-purple-300 hover:shadow-sm'
              }`}
            >
              {isRecommended && (
                <span className="absolute -top-2 -right-2 px-2 py-0.5 rounded-full text-[10px] font-medium text-white bg-purple-600">
                  ✨ 最优匹配
                </span>
              )}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center text-lg bg-purple-100 text-purple-700 shrink-0">
                  🤖
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{agent.name}</p>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                    {agent.description}
                  </p>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-3 text-[10px] text-muted-foreground">
                <span>成功率 {(agent.success_rate * 100).toFixed(0)}%</span>
                <span>近1h {agent.recent_tasks_1h} 任务</span>
              </div>
              <AgentConstraintTags config={agent.config || {}} />
              <div className="mt-2 flex flex-wrap gap-1">
                {agent.skills?.slice(0, 3).map((skill) => (
                  <span
                    key={skill}
                    className="px-1.5 py-0.5 rounded text-[10px] bg-secondary text-secondary-foreground"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </button>
          )
        })}
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {(onSave || onClear) && (
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
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

      {filteredAgents.length === 0 && (
        <div className="rounded-lg border border-dashed p-4 text-center space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            {agents.length === 0 ? '🤖 暂无可用 Agent' : '🔍 暂无匹配的 Agent'}
          </p>
          <p className="text-xs text-muted-foreground">
            {agents.length === 0
              ? '系统中未找到任何 Agent。请确认后端服务已启动且数据库种子已注入。'
              : `当前筛选条件：平台「${platform || '未选择'}」+ 格式「${contentFormat || '未选择'}」。请检查平台与格式组合是否正确，或联系管理员配置对应 Agent。`}
          </p>
          {agents.length > 0 && (
            <div className="text-[10px] text-muted-foreground bg-muted rounded p-2 text-left">
              <p className="font-medium mb-1">系统中已有的 Agent（供调试）：</p>
              <div className="space-y-1">
                {agents.map((a) => (
                  <div key={a.id} className="flex items-center gap-2">
                    <span className={a.status?.toUpperCase() === 'ACTIVE' ? 'text-green-500' : 'text-red-500'}>
                      {a.status?.toUpperCase() === 'ACTIVE' ? '●' : '○'}
                    </span>
                    <span>{a.name}</span>
                    <span className="text-muted-foreground">[{a.supported_platforms?.join(', ') || '无'} / {a.supported_formats?.join(', ') || '无'}]</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
