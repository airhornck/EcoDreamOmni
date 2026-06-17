import { useEffect, useState } from 'react'
import { useProxyStore, type ProxyEntry } from '../stores/proxyStore'
import { usePageCopilot } from '../hooks/usePageCopilot'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { Globe, Plus, Trash2, Play, Pause, Activity, CheckCircle2, XCircle } from 'lucide-react'

const protocolLabels: Record<string, string> = {
  http: 'HTTP',
  https: 'HTTPS',
  socks5: 'SOCKS5',
}

const providerLabels: Record<string, string> = {
  brightdata: 'Bright Data',
  oxylabs: 'Oxylabs',
  custom: '自定义',
}

export function ProxyConfigPage() {
  const { proxies, isLoading, error, fetchProxies, createProxy, deleteProxy, testProxy } = useProxyStore()
  const [showCreate, setShowCreate] = useState(false)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ id: string; success: boolean; msg: string } | null>(null)

  /* form state */
  const [name, setName] = useState('')
  const [provider, setProvider] = useState('custom')
  const [protocol, setProtocol] = useState('http')
  const [host, setHost] = useState('')
  const [port, setPort] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [region, setRegion] = useState('')
  const [rotationType, setRotationType] = useState('static')

  useEffect(() => {
    fetchProxies()
  }, [fetchProxies])

  const resetForm = () => {
    setName('')
    setProvider('custom')
    setProtocol('http')
    setHost('')
    setPort('')
    setUsername('')
    setPassword('')
    setRegion('')
    setRotationType('static')
  }

  const handleCreate = async () => {
    if (!name.trim() || !host.trim() || !port.trim()) return
    const success = await createProxy({
      name,
      provider,
      protocol,
      host,
      port: parseInt(port, 10),
      username,
      password,
      region,
      rotation_type: rotationType,
    })
    if (success) {
      setShowCreate(false)
      resetForm()
    }
  }

  const handleTest = async (proxy: ProxyEntry) => {
    setTestingId(proxy.id)
    setTestResult(null)
    const result = await testProxy(proxy.id)
    setTestResult({
      id: proxy.id,
      success: result.success,
      msg: result.error || '连接成功',
    })
    setTestingId(null)
  }

  const toggleActive = async (proxy: ProxyEntry) => {
    const { updateProxy } = useProxyStore.getState()
    await updateProxy(proxy.id, { is_active: !proxy.is_active })
  }

  // Copilot 联动（放在 handleTest/toggleActive 声明之后，避免 lint 访问前置变量）
  usePageCopilot(
    [
      {
        id: 'proxy-create',
        type: 'decision',
        title: '➕ 新增代理',
        description: '添加新的 HTTP/SOCKS5 代理配置',
        priority: 1,
        actions: [{ id: 'create_proxy', label: '添加', variant: 'primary' }],
      },
      {
        id: 'proxy-test',
        type: 'decision',
        title: '🧪 测试首个代理',
        description: '对列表中的第一条代理进行连通性测试',
        priority: 2,
        actions: [{ id: 'test_first_proxy', label: '测试', variant: 'secondary' }],
      },
      {
        id: 'proxy-toggle',
        type: 'decision',
        title: '🔁 切换首条代理状态',
        description: '启用/禁用列表中的第一条代理',
        priority: 3,
        actions: [{ id: 'toggle_first_proxy', label: '切换', variant: 'secondary' }],
      },
      {
        id: 'proxy-to-engine',
        type: 'info',
        title: '🚀 前往 AI 引擎',
        description: '代理管理已合并至 AI 引擎，推荐统一入口',
        priority: 4,
        actions: [{ id: 'goto_engine', label: '前往', variant: 'secondary' }],
      },
    ],
    async (_cardId, actionId) => {
      if (actionId === 'create_proxy') {
        setShowCreate(true)
      } else if (actionId === 'test_first_proxy') {
        const first = proxies[0]
        if (first) await handleTest(first)
        else alert('当前没有可测试的代理')
      } else if (actionId === 'toggle_first_proxy') {
        const first = proxies[0]
        if (first) await toggleActive(first)
        else alert('当前没有可切换的代理')
      } else if (actionId === 'goto_engine') {
        window.location.href = '/models'
      }
    }
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="代理配置"
        subtitle="管理 IP 代理服务器，为账号发布提供指纹隔离与 IP 轮换能力"
        action={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4" />
            新增代理
          </Button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      <div className="p-3 rounded-lg bg-info/10 text-info text-sm flex items-center justify-between">
        <span>代理配置已合并到「AI 引擎」，建议从左侧导航进入统一管理。</span>
        <a
          href="/models"
          className="font-medium hover:underline"
          onClick={(e) => {
            e.preventDefault()
            window.location.href = '/models'
          }}
        >
          前往 AI 引擎 →
        </a>
      </div>

      {showCreate && (
        <Card>
          <CardHeader><h3 className="text-base font-semibold">新增代理</h3></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text" placeholder="代理名称 *" value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
              <select
                value={provider} onChange={(e) => setProvider(e.target.value)}
                className="h-10 px-3 rounded-lg border border-border bg-background text-sm"
              >
                <option value="custom">自定义</option>
                <option value="brightdata">Bright Data</option>
                <option value="oxylabs">Oxylabs</option>
              </select>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <select
                value={protocol} onChange={(e) => setProtocol(e.target.value)}
                className="h-10 px-3 rounded-lg border border-border bg-background text-sm"
              >
                <option value="http">HTTP</option>
                <option value="https">HTTPS</option>
                <option value="socks5">SOCKS5</option>
              </select>
              <input
                type="text" placeholder="主机地址 *" value={host}
                onChange={(e) => setHost(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
              <input
                type="number" placeholder="端口 *" value={port}
                onChange={(e) => setPort(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text" placeholder="用户名（可选）" value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
              <input
                type="password" placeholder="密码（可选）" value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text" placeholder="区域（如 cn, us, jp）" value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
              <select
                value={rotationType} onChange={(e) => setRotationType(e.target.value)}
                className="h-10 px-3 rounded-lg border border-border bg-background text-sm"
              >
                <option value="static">静态 IP</option>
                <option value="session">会话轮换</option>
                <option value="rotating">每次请求轮换</option>
              </select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => { setShowCreate(false); resetForm() }}>取消</Button>
              <Button onClick={handleCreate}>创建</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">代理列表</h2>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && proxies.length === 0 && (
            <EmptyState icon={Globe} title="暂无代理" description="添加代理服务器以启用 IP 隔离与轮换" />
          )}
          <div className="space-y-2">
            {proxies.map((proxy) => (
              <div key={proxy.id} className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-secondary/30 transition-colors">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-foreground">{proxy.name}</span>
                    <Badge variant="info">{protocolLabels[proxy.protocol] || proxy.protocol}</Badge>
                    <Badge variant="default">{providerLabels[proxy.provider] || proxy.provider}</Badge>
                    {proxy.is_active ? (
                      <Badge variant="success">启用</Badge>
                    ) : (
                      <Badge variant="default">禁用</Badge>
                    )}
                    <Badge variant={proxy.health_status === 'healthy' ? 'success' : proxy.health_status === 'unhealthy' ? 'danger' : 'warning'}>
                      {proxy.health_status === 'healthy' ? '健康' : proxy.health_status === 'unhealthy' ? '异常' : '未知'}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {proxy.host}:{proxy.port} {proxy.region && `· ${proxy.region.toUpperCase()}`} {proxy.username && '· 需要认证'}
                    {proxy.fail_count > 0 && ` · 失败 ${proxy.fail_count} 次`}
                    {proxy.success_count > 0 && ` · 成功 ${proxy.success_count} 次`}
                  </p>
                  {testResult?.id === proxy.id && (
                    <p className={`text-xs mt-1 ${testResult.success ? 'text-success' : 'text-destructive'}`}>
                      {testResult.success ? <CheckCircle2 className="w-3 h-3 inline mr-1" /> : <XCircle className="w-3 h-3 inline mr-1" />}
                      {testResult.msg}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1 ml-3">
                  <button
                    onClick={() => toggleActive(proxy)}
                    className="p-1.5 hover:bg-secondary rounded"
                    title={proxy.is_active ? '禁用' : '启用'}
                  >
                    {proxy.is_active ? (
                      <Pause className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <Play className="w-4 h-4 text-success" />
                    )}
                  </button>
                  <button
                    onClick={() => handleTest(proxy)}
                    disabled={testingId === proxy.id}
                    className="p-1.5 hover:bg-secondary rounded disabled:opacity-50"
                    title="连通性测试"
                  >
                    <Activity className={`w-4 h-4 ${testingId === proxy.id ? 'animate-spin text-primary' : 'text-muted-foreground'}`} />
                  </button>
                  <button
                    onClick={() => deleteProxy(proxy.id)}
                    className="p-1.5 hover:bg-destructive/10 rounded"
                    title="删除"
                  >
                    <Trash2 className="w-4 h-4 text-destructive" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
