import { useEffect, useState } from 'react'
import { useLlmCockpitStore } from '../stores/llmCockpitStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { AlertBanner } from '../components/ui/AlertBanner'
import {
  Cpu,
  Globe,
  BarChart3,
  ScrollText,
  Plus,
  Eye,
  EyeOff,
  Trash2,
  Edit2,
  RotateCcw,
  CheckCircle2,
  Search,
  Loader2,
} from 'lucide-react'

const PROVIDERS = {
  domestic: [
    { value: 'deepseek', label: 'DeepSeek' },
    { value: 'aliyun', label: '阿里云' },
    { value: 'baidu', label: '百度' },
    { value: 'zhipu', label: '智谱' },
    { value: 'kimi', label: 'Kimi' },
    { value: 'xunfei', label: '讯飞' },
  ],
  overseas: [
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'google', label: 'Google' },
  ],
}

const TAB_META = [
  { key: 'models' as const, label: '模型管理', icon: Cpu },
  { key: 'scopes' as const, label: '应用范围', icon: Globe },
  { key: 'costs' as const, label: '成本看板', icon: BarChart3 },
  { key: 'logs' as const, label: '调用日志', icon: ScrollText },
]

export function LlmCockpitPage() {
  const {
    models,
    scopeConfigs,
    costSummary,
    usageLogs,
    isLoading,
    error,
    activeTab,
    fetchModels,
    fetchScopeConfigs,
    fetchCostSummary,
    fetchUsageLogs,
    createModel,
    deleteModel,
    testConnectivity,
    setNodeOverride,
    removeNodeOverride,
    setActiveTab,
    clearError,
  } = useLlmCockpitStore()

  const [showModelDrawer, setShowModelDrawer] = useState(false)
  const [modelForm, setModelForm] = useState({
    provider: '',
    model_name: '',
    api_key: '',
    endpoint_base_url: '',
    status: 'active' as 'active' | 'inactive',
  })
  const [showApiKey, setShowApiKey] = useState(false)
  const [testingId, setTestingId] = useState<string | null>(null)

  const [editScopeNode, setEditScopeNode] = useState<string | null>(null)
  const [scopeForm, setScopeForm] = useState({ model_id: '', temperature: 0.7, timeout_seconds: 30 })

  const [logFilters, setLogFilters] = useState<Record<string, string>>({})

  useEffect(() => {
    fetchModels()
  }, [fetchModels])

  useEffect(() => {
    if (activeTab === 'scopes') fetchScopeConfigs()
    if (activeTab === 'costs') fetchCostSummary(7)
    if (activeTab === 'logs') fetchUsageLogs()
  }, [activeTab, fetchScopeConfigs, fetchCostSummary, fetchUsageLogs])

  const handleCreateModel = async () => {
    if (!modelForm.provider || !modelForm.model_name || !modelForm.api_key) return
    const model = await createModel(modelForm)
    if (model) {
      setShowModelDrawer(false)
      setModelForm({ provider: '', model_name: '', api_key: '', endpoint_base_url: '', status: 'active' })
    }
  }

  const handleTest = async (id: string) => {
    setTestingId(id)
    await testConnectivity(id)
    setTestingId(null)
  }

  const globalScope = scopeConfigs.find((s) => s.scope_type === 'global')
  const nodeScopes = scopeConfigs.filter((s) => s.scope_type === 'node')

  return (
    <div className="space-y-6">
      <PageHeader title="LLM Cockpit" subtitle="模型管理、应用范围、成本监控与调用日志" />

      {error && (
        <AlertBanner variant="danger" title="操作失败" description={error} onDismiss={clearError} />
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        {TAB_META.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === t.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {isLoading && activeTab !== 'models' && (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">加载中...</p>
        </div>
      )}

      {/* Models Tab */}
      {activeTab === 'models' && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">已注册模型 ({models.length})</h2>
            <Button
              size="sm"
              onClick={() => {
                setShowModelDrawer(true)
                setModelForm({ provider: '', model_name: '', api_key: '', endpoint_base_url: '', status: 'active' })
              }}
            >
              <Plus className="w-4 h-4" />
              注册模型
            </Button>
          </div>

          {showModelDrawer && (
            <Card>
              <CardHeader>
                <h3 className="text-base font-semibold">注册新模型</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">厂家</label>
                    <select
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                      value={modelForm.provider}
                      onChange={(e) => setModelForm({ ...modelForm, provider: e.target.value })}
                    >
                      <option value="">选择厂家</option>
                      <optgroup label="国内">
                        {PROVIDERS.domestic.map((p) => (
                          <option key={p.value} value={p.value}>
                            {p.label}
                          </option>
                        ))}
                      </optgroup>
                      <optgroup label="国外">
                        {PROVIDERS.overseas.map((p) => (
                          <option key={p.value} value={p.value}>
                            {p.label}
                          </option>
                        ))}
                      </optgroup>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">模型名</label>
                    <input
                      type="text"
                      placeholder="如 deepseek-chat"
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                      value={modelForm.model_name}
                      onChange={(e) => setModelForm({ ...modelForm, model_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        placeholder="sk-..."
                        className="w-full h-10 px-3 pr-10 rounded-lg border border-border bg-background text-sm"
                        value={modelForm.api_key}
                        onChange={(e) => setModelForm({ ...modelForm, api_key: e.target.value })}
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">API 端点（可选）</label>
                    <input
                      type="text"
                      placeholder="https://api.example.com/v1"
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                      value={modelForm.endpoint_base_url}
                      onChange={(e) => setModelForm({ ...modelForm, endpoint_base_url: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1 md:col-span-2">
                    <label className="text-xs font-medium text-muted-foreground">状态</label>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 text-sm cursor-pointer">
                        <input
                          type="radio"
                          name="model-status"
                          checked={modelForm.status === 'active'}
                          onChange={() => setModelForm({ ...modelForm, status: 'active' })}
                        />
                        启用
                      </label>
                      <label className="flex items-center gap-2 text-sm cursor-pointer">
                        <input
                          type="radio"
                          name="model-status"
                          checked={modelForm.status === 'inactive'}
                          onChange={() => setModelForm({ ...modelForm, status: 'inactive' })}
                        />
                        停用
                      </label>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setShowModelDrawer(false)}>
                    取消
                  </Button>
                  <Button size="sm" onClick={handleCreateModel}>
                    保存并测试连通性
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">厂家</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">模型名</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">API Key</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">端点</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">状态</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {models.map((m) => (
                  <tr key={m.id} className="hover:bg-muted/50">
                    <td className="px-4 py-3 text-foreground font-medium">{m.provider}</td>
                    <td className="px-4 py-3 text-muted-foreground">{m.model_name}</td>
                    <td className="px-4 py-3 text-muted-foreground font-mono">{m.api_key_masked}</td>
                    <td className="px-4 py-3 text-muted-foreground truncate max-w-[200px]">
                      {m.endpoint_base_url ?? '-'}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={m.status === 'active' ? 'success' : 'default'}>
                        {m.status === 'active' ? '启用' : '停用'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleTest(m.id)}
                          className="p-1.5 hover:bg-primary/10 rounded text-primary"
                          title="测试连通性"
                        >
                          {testingId === m.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => deleteModel(m.id)}
                          className="p-1.5 hover:bg-destructive/10 rounded text-destructive"
                          title="删除"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {models.length === 0 && !isLoading && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8">
                      <EmptyState icon={Cpu} title="暂无注册模型" description="注册你的第一个 LLM 模型" />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Scopes Tab */}
      {activeTab === 'scopes' && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">应用范围配置</h2>

          {globalScope && (
            <Card>
              <CardHeader>
                <h3 className="text-base font-semibold">全局默认</h3>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                  <div>
                    <div className="text-xs text-muted-foreground">当前模型</div>
                    <div className="text-sm font-medium text-foreground">{globalScope.model_name}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">温度</div>
                    <div className="text-sm font-medium text-foreground">{globalScope.temperature}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">超时</div>
                    <div className="text-sm font-medium text-foreground">{globalScope.timeout_seconds}s</div>
                  </div>
                  <div className="text-right">
                    <Badge variant="primary">全局默认</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">节点名称</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">节点类型</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">当前模型</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">来源</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">温度</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {nodeScopes.map((s) => (
                  <tr key={s.id} className="hover:bg-muted/50">
                    <td className="px-4 py-3 text-foreground font-medium">{s.node_id ?? '-'}</td>
                    <td className="px-4 py-3 text-muted-foreground">{s.node_type ?? '-'}</td>
                    <td className="px-4 py-3 text-foreground">{s.model_name}</td>
                    <td className="px-4 py-3">
                      <Badge variant={s.source === 'override' ? 'warning' : 'default'}>
                        {s.source === 'override' ? '覆盖' : '全局默认'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{s.temperature}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => {
                            setEditScopeNode(s.node_id || s.id)
                            setScopeForm({
                              model_id: s.model_id,
                              temperature: s.temperature,
                              timeout_seconds: s.timeout_seconds,
                            })
                          }}
                          className="p-1.5 hover:bg-primary/10 rounded text-primary"
                          title="编辑"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        {s.source === 'override' && (
                          <button
                            onClick={() => removeNodeOverride(s.id)}
                            className="p-1.5 hover:bg-destructive/10 rounded text-destructive"
                            title="恢复全局默认"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {nodeScopes.length === 0 && !isLoading && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8">
                      <EmptyState
                        icon={Globe}
                        title="暂无节点覆盖配置"
                        description="所有节点均使用全局默认模型"
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {editScopeNode && (
            <Card>
              <CardHeader>
                <h3 className="text-base font-semibold">编辑节点覆盖</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">模型</label>
                    <select
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                      value={scopeForm.model_id}
                      onChange={(e) => setScopeForm({ ...scopeForm, model_id: e.target.value })}
                    >
                      <option value="">选择模型</option>
                      {models.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.model_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">温度</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                      value={scopeForm.temperature}
                      onChange={(e) => setScopeForm({ ...scopeForm, temperature: Number(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-muted-foreground">超时(秒)</label>
                    <input
                      type="number"
                      min="1"
                      className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                      value={scopeForm.timeout_seconds}
                      onChange={(e) => setScopeForm({ ...scopeForm, timeout_seconds: Number(e.target.value) })}
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setEditScopeNode(null)}>
                    取消
                  </Button>
                  <Button
                    size="sm"
                    onClick={async () => {
                      const success = await setNodeOverride(
                        editScopeNode,
                        scopeForm.model_id,
                        scopeForm.temperature,
                        scopeForm.timeout_seconds
                      )
                      if (success) setEditScopeNode(null)
                    }}
                  >
                    保存
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </section>
      )}

      {/* Costs Tab */}
      {activeTab === 'costs' && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">成本看板</h2>

          {costSummary && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="py-5">
                    <div className="text-xs text-muted-foreground">今日调用次数</div>
                    <div className="text-2xl font-bold text-foreground mt-1">
                      {costSummary.total_calls.toLocaleString()}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="py-5">
                    <div className="text-xs text-muted-foreground">总 Token 数</div>
                    <div className="text-2xl font-bold text-foreground mt-1">
                      {(costSummary.total_input_tokens + costSummary.total_output_tokens).toLocaleString()}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="py-5">
                    <div className="text-xs text-muted-foreground">预估成本 (CNY)</div>
                    <div className="text-2xl font-bold text-foreground mt-1">
                      ¥{costSummary.estimated_cost_cny.toFixed(2)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <h3 className="text-base font-semibold">按模型占比</h3>
                  </CardHeader>
                  <CardContent>
                    {costSummary.by_model.length === 0 ? (
                      <EmptyState icon={BarChart3} title="暂无数据" />
                    ) : (
                      <div className="space-y-3">
                        {costSummary.by_model.map((item) => {
                          const max = Math.max(...costSummary.by_model.map((i) => i.cost_cny), 0.01)
                          const pct = (item.cost_cny / max) * 100
                          return (
                            <div key={item.model_id}>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-foreground font-medium">{item.model_name}</span>
                                <span className="text-muted-foreground">
                                  ¥{item.cost_cny.toFixed(2)} ({item.calls}次)
                                </span>
                              </div>
                              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-primary rounded-full transition-all"
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <h3 className="text-base font-semibold">TOP10 节点排行</h3>
                  </CardHeader>
                  <CardContent>
                    {costSummary.by_node.length === 0 ? (
                      <EmptyState icon={BarChart3} title="暂无数据" />
                    ) : (
                      <div className="space-y-2">
                        {costSummary.by_node.slice(0, 10).map((item, idx) => (
                          <div key={item.node_id} className="flex items-center gap-3 text-sm">
                            <span className="w-5 text-center text-muted-foreground font-mono">{idx + 1}</span>
                            <span className="flex-1 truncate text-foreground">{item.node_id}</span>
                            <span className="text-muted-foreground">{item.calls}次</span>
                            <span className="text-foreground font-medium w-16 text-right">
                              ¥{item.cost_cny.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <h3 className="text-base font-semibold">近7日趋势</h3>
                </CardHeader>
                <CardContent>
                  {costSummary.trend.length === 0 ? (
                    <EmptyState icon={BarChart3} title="暂无趋势数据" />
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-end gap-2 h-32">
                        {costSummary.trend.map((t) => {
                          const maxCalls = Math.max(...costSummary.trend.map((d) => d.calls), 1)
                          const height = (t.calls / maxCalls) * 100
                          return (
                            <div key={t.date} className="flex-1 flex flex-col items-center gap-1">
                              <div
                                className="w-full bg-primary/20 rounded-t relative group"
                                style={{ height: `${height}%` }}
                              >
                                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-foreground text-background text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                  {t.calls}次 / ¥{t.cost_cny.toFixed(2)}
                                </div>
                              </div>
                              <span className="text-[10px] text-muted-foreground">{t.date.slice(5)}</span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {!costSummary && !isLoading && (
            <EmptyState icon={BarChart3} title="暂无成本数据" description="请稍后刷新查看" />
          )}
        </section>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-foreground">调用日志</h2>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="节点ID"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={logFilters.node_id || ''}
                onChange={(e) => setLogFilters({ ...logFilters, node_id: e.target.value })}
              />
              <select
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={logFilters.status || ''}
                onChange={(e) => setLogFilters({ ...logFilters, status: e.target.value })}
              >
                <option value="">全部状态</option>
                <option value="success">成功</option>
                <option value="error">失败</option>
                <option value="timeout">超时</option>
              </select>
              <Button size="sm" onClick={() => fetchUsageLogs(logFilters)}>
                <Search className="w-4 h-4" />
                查询
              </Button>
            </div>
          </div>

          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">时间</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">模型</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">节点</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Region</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Tokens</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">延迟</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">状态</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {usageLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-muted/50">
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{log.created_at}</td>
                    <td className="px-4 py-3 text-foreground font-medium">{log.model_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{log.node_id}</td>
                    <td className="px-4 py-3 text-muted-foreground">{log.provider_region}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {log.input_tokens}+{log.output_tokens}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{log.latency_ms}ms</td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={
                          log.status === 'success' ? 'success' : log.status === 'timeout' ? 'warning' : 'danger'
                        }
                      >
                        {log.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
                {usageLogs.length === 0 && !isLoading && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8">
                      <EmptyState
                        icon={ScrollText}
                        title="暂无调用日志"
                        description="调整筛选条件或稍后查看"
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
