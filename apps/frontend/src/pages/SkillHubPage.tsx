import { useEffect, useState } from 'react'
import { useSkillHubStore } from '../stores/skillHubStore'
import { useAgentOrchestraStore } from '../stores/agentOrchestraStore'
import { PageHeader } from '../components/common/PageHeader'
import { StatCard } from '../components/common/StatCard'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  Zap,
  Plus,
  Code,
  Search,
  Layers,
  Activity,
  Link2,
  Play,
  X,
  ChevronDown,
  ChevronUp,
  Save,
  Wrench,
} from 'lucide-react'

const LEVEL_LABELS: Record<string, string> = {
  L1: 'L1 内置',
  L2: 'L2 项目',
  L3: 'L3 用户',
  L4: 'L4 会话',
}

const LEVEL_VARIANT: Record<string, 'primary' | 'success' | 'warning' | 'info'> = {
  L1: 'primary',
  L2: 'success',
  L3: 'warning',
  L4: 'info',
}

interface ExecHistoryItem {
  skillId: string
  skillName: string
  result: string
  timestamp: number
}

export function SkillHubPage() {
  const {
    skills,
    bindings,
    isLoading,
    error,
    activeLevel,
    activeTab,
    fetchSkills,
    createSkill,
    bindSkill,
    executeSkill,
    setActiveLevel,
    setActiveTab,
    clearError,
  } = useSkillHubStore()

  const { agents, fetchAgents } = useAgentOrchestraStore()

  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', level: 'L2', code: '', tags: '', version: '1.0.0' })
  const [bindForm, setBindForm] = useState({ agentId: '', skillId: '', priority: 0 })
  const [execForm, setExecForm] = useState({ skillId: '', context: '{}' })
  const [execResult, setExecResult] = useState<string | null>(null)
  const [execHistory, setExecHistory] = useState<ExecHistoryItem[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedSkillId, setExpandedSkillId] = useState<string | null>(null)

  useEffect(() => {
    fetchSkills(activeLevel || undefined)
    fetchAgents()
  }, [fetchSkills, activeLevel, fetchAgents])

  const activeSkillsCount = skills.filter((s) => s.status === 'active').length

  const filteredSkills = skills.filter((skill) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      skill.name.toLowerCase().includes(q) ||
      skill.tags.some((tag) => tag.toLowerCase().includes(q))
    )
  })

  const handleCreate = async () => {
    await createSkill({
      name: form.name,
      description: form.description,
      level: form.level,
      code: form.code,
      tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
      version: form.version,
    })
    setShowCreate(false)
    setForm({ name: '', description: '', level: 'L2', code: '', tags: '', version: '1.0.0' })
  }

  const handleBind = async () => {
    await bindSkill(bindForm.agentId, bindForm.skillId, bindForm.priority)
    setBindForm({ agentId: '', skillId: '', priority: 0 })
  }

  const handleExecute = async () => {
    setExecResult(null)
    let parsedCtx: Record<string, unknown>
    try {
      parsedCtx = JSON.parse(execForm.context || '{}') as Record<string, unknown>
    } catch {
      setExecResult('Error: Invalid JSON in context')
      return
    }
    const res = await executeSkill(execForm.skillId, parsedCtx)
    const resultStr = JSON.stringify(res, null, 2)
    setExecResult(resultStr)
    const skill = skills.find((s) => s.id === execForm.skillId)
    setExecHistory((prev) => [
      { skillId: execForm.skillId, skillName: skill?.name || execForm.skillId, result: resultStr, timestamp: Date.now() },
      ...prev,
    ].slice(0, 5))
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="技能中心"
        subtitle="管理 Agent 技能注册、绑定与执行测试"
      />

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-center justify-between">
          <p className="text-sm text-destructive">{error}</p>
          <button onClick={clearError} className="text-sm text-destructive hover:underline">重试</button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="总技能数" value={skills.length} icon={Layers} variant="primary" />
        <StatCard label="活跃技能数" value={activeSkillsCount} icon={Activity} variant="success" />
        <StatCard label="总绑定数" value={bindings.length} icon={Link2} variant="primary" />
        <StatCard label="今日执行次数" value={execHistory.length} icon={Zap} variant="warning" />
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-secondary rounded-lg p-0.5 w-fit">
        {(['skills', 'bindings'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab === 'skills' ? '技能列表' : 'Agent 绑定'}
          </button>
        ))}
      </div>

      {activeTab === 'skills' && (
        <div className="space-y-6">
          {/* Filters + Search + Create */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 justify-between">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-muted-foreground">层级过滤：</span>
              <Button
                size="sm"
                variant={activeLevel === null ? 'primary' : 'outline'}
                onClick={() => setActiveLevel(null)}
                className="rounded-full"
              >
                全部
              </Button>
              {Object.entries(LEVEL_LABELS).map(([key, label]) => (
                <Button
                  key={key}
                  size="sm"
                  variant={activeLevel === key ? 'primary' : 'outline'}
                  onClick={() => setActiveLevel(key)}
                  className="rounded-full"
                >
                  {label}
                </Button>
              ))}
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:flex-initial">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="按名称/标签搜索"
                  className="w-full sm:w-48 pl-8 pr-3 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <Button size="sm" onClick={() => setShowCreate(!showCreate)}>
                <Plus className="w-3.5 h-3.5" />
                {showCreate ? '取消' : '创建技能'}
              </Button>
            </div>
          </div>

          {/* Create form */}
          {showCreate && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-semibold text-foreground">新建技能</h3>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">技能名称</label>
                    <input
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                      aria-label="技能名称"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">层级</label>
                    <select
                      value={form.level}
                      onChange={(e) => setForm({ ...form, level: e.target.value })}
                      className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                      aria-label="层级"
                    >
                      <option value="L1">L1 内置</option>
                      <option value="L2">L2 项目</option>
                      <option value="L3">L3 用户</option>
                      <option value="L4">L4 会话</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">版本</label>
                    <input
                      value={form.version}
                      onChange={(e) => setForm({ ...form, version: e.target.value })}
                      className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                      aria-label="版本"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">标签（逗号分隔）</label>
                    <input
                      value={form.tags}
                      onChange={(e) => setForm({ ...form, tags: e.target.value })}
                      className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                      aria-label="标签"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs font-medium text-muted-foreground mb-1">代码</label>
                    <textarea
                      value={form.code}
                      onChange={(e) => setForm({ ...form, code: e.target.value })}
                      rows={4}
                      className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono"
                      aria-label="代码"
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button size="sm" onClick={handleCreate}>
                    <Save className="w-3.5 h-3.5" />
                    保存
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Skills table */}
          <Card>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">名称</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">层级</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">版本</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">状态</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">标签</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredSkills.map((skill) => (
                    <tr key={skill.id}>
                      <td className="px-4 py-3 font-medium text-foreground">
                        <div className="flex items-center gap-2">
                          <Code className="w-3.5 h-3.5 text-muted-foreground" />
                          {skill.name}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={LEVEL_VARIANT[skill.level] || 'default'}>
                          {LEVEL_LABELS[skill.level] || skill.level}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{skill.version}</td>
                      <td className="px-4 py-3">
                        <Badge variant={skill.status === 'active' ? 'success' : 'default'}>
                          {skill.status === 'active' ? '活跃' : skill.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1 flex-wrap">
                          {skill.tags.map((tag: string) => (
                            <Badge key={tag} variant="default" className="text-[10px]">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setExecForm({ skillId: skill.id, context: '{}' })
                            setExecResult(null)
                          }}
                        >
                          <Play className="w-3 h-3" />
                          执行
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {filteredSkills.length === 0 && (
                    <tr>
                      <td colSpan={6}>
                        <EmptyState
                          icon={Layers}
                          title="暂无技能"
                          description={searchQuery ? '没有匹配搜索条件的技能' : '点击"创建技能"添加'}
                        />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* Execute panel */}
          {execForm.skillId && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-semibold text-foreground">执行技能</h3>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Context (JSON)</label>
                    <textarea
                      value={execForm.context}
                      onChange={(e) => setExecForm({ ...execForm, context: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">结果</label>
                    <pre className="w-full h-full min-h-[5rem] px-3 py-2 text-xs bg-muted rounded-md overflow-auto font-mono">
                      {execResult || '点击执行查看结果'}
                    </pre>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setExecForm({ skillId: '', context: '{}' })}
                  >
                    <X className="w-3 h-3" />
                    取消
                  </Button>
                  <Button size="sm" onClick={handleExecute}>
                    <Play className="w-3 h-3" />
                    执行
                  </Button>
                </div>

                {/* Execution History */}
                {execHistory.length > 0 && (
                  <div className="pt-4 border-t border-border">
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">最近执行记录</h4>
                    <div className="space-y-2">
                      {execHistory.map((item, idx) => (
                        <div key={idx} className="rounded-lg border border-border bg-muted/30 overflow-hidden">
                          <button
                            className="w-full flex items-center justify-between px-3 py-2 text-left"
                            onClick={() => setExpandedSkillId(expandedSkillId === `${item.skillId}-${idx}` ? null : `${item.skillId}-${idx}`)}
                          >
                            <div className="flex items-center gap-2">
                              <Badge variant="default" className="text-[10px]">{item.skillName}</Badge>
                              <span className="text-xs text-muted-foreground">
                                {new Date(item.timestamp).toLocaleTimeString('zh-CN')}
                              </span>
                            </div>
                            {expandedSkillId === `${item.skillId}-${idx}` ? (
                              <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
                            )}
                          </button>
                          {expandedSkillId === `${item.skillId}-${idx}` && (
                            <pre className="px-3 py-2 text-xs bg-muted overflow-auto font-mono border-t border-border">
                              {item.result}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'bindings' && (
        <div className="space-y-6">
          {/* Bind form */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Link2 className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">绑定 Skill 到 Agent</h3>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Agent</label>
                  <select
                    value={bindForm.agentId}
                    onChange={(e) => setBindForm({ ...bindForm, agentId: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                  >
                    <option value="">选择 Agent</option>
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Skill</label>
                  <select
                    value={bindForm.skillId}
                    onChange={(e) => setBindForm({ ...bindForm, skillId: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                  >
                    <option value="">选择技能</option>
                    {skills.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">优先级</label>
                  <input
                    type="number"
                    value={bindForm.priority}
                    onChange={(e) => setBindForm({ ...bindForm, priority: Number(e.target.value) })}
                    className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <Button size="sm" onClick={handleBind}>
                  <Link2 className="w-3.5 h-3.5" />
                  绑定
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Bindings list */}
          <Card>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Agent ID</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Skill ID</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">优先级</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {bindings.map((b) => (
                    <tr key={b.id}>
                      <td className="px-4 py-3 font-medium text-foreground">{b.agent_id}</td>
                      <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{b.skill_id}</td>
                      <td className="px-4 py-3 text-muted-foreground">{b.priority}</td>
                    </tr>
                  ))}
                  {bindings.length === 0 && (
                    <tr>
                      <td colSpan={3}>
                        <EmptyState
                          icon={Link2}
                          title="暂无绑定关系"
                          description="使用上方表单添加 Agent 与 Skill 的绑定"
                        />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
