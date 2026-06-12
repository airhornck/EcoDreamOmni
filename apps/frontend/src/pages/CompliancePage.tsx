import { useEffect, useMemo, useState } from 'react'
import { useComplianceStore } from '../stores/complianceStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { AlertBanner } from '../components/ui/AlertBanner'
import {
  ShieldCheck,
  ScanLine,
  AlertTriangle,
  CheckCircle,
  Info,
  History,
  BookOpen,
  Filter,
  Search,
  Trash2,
  ChevronDown,
  ChevronUp,
  Wand2,
  FileText,
  BarChart3,
  ShieldAlert,
  Shield,
  Activity,
} from 'lucide-react'

const levelLabels: Record<string, string> = {
  l1: 'L1 法律红线',
  l2: 'L2 平台规则',
  l3: 'L3 账号策略',
  l4: 'L4 动态风控',
}

const levelVariants: Record<string, 'danger' | 'warning' | 'info' | 'default'> = {
  l1: 'danger',
  l2: 'warning',
  l3: 'info',
  l4: 'default',
}

const levelFilters = [
  { key: 'all', label: '全部' },
  { key: 'l1', label: 'L1' },
  { key: 'l2', label: 'L2' },
  { key: 'l3', label: 'L3' },
  { key: 'l4', label: 'L4' },
]

function applyFixes(text: string, violations: Array<{ matched: string; replacement?: string }>): string {
  let result = text
  const replacements = violations
    .filter((v) => v.replacement && v.matched)
    .map((v) => ({ matched: v.matched, replacement: v.replacement! }))

  // Apply replacements from end to start to preserve positions
  const positions: Array<{ start: number; end: number; replacement: string }> = []
  for (const { matched, replacement } of replacements) {
    let idx = result.indexOf(matched)
    while (idx !== -1) {
      positions.push({ start: idx, end: idx + matched.length, replacement })
      idx = result.indexOf(matched, idx + 1)
    }
  }

  positions.sort((a, b) => b.start - a.start)
  for (const pos of positions) {
    result = result.slice(0, pos.start) + pos.replacement + result.slice(pos.end)
  }
  return result
}

export function CompliancePage() {
  const {
    rules,
    results,
    stats,
    history,
    isLoading,
    error,
    activeTab,
    levelFilter,
    searchQuery,
    fetchRules,
    checkContent,
    batchCheck,
    fetchStats,
    fetchHistory,
    clearHistory,
    setActiveTab,
    setLevelFilter,
    setSearchQuery,
  } = useComplianceStore()

  const [text, setText] = useState('')
  const [batchText, setBatchText] = useState('')
  const [checking, setChecking] = useState(false)
  const [batchChecking, setBatchChecking] = useState(false)
  const [fixedTexts, setFixedTexts] = useState<Record<string, string>>({})
  const [expandedHistory, setExpandedHistory] = useState<Set<string>>(new Set())
  const [dismissedError, setDismissedError] = useState(false)

  useEffect(() => {
    fetchRules()
    fetchStats()
    fetchHistory()
  }, [fetchRules, fetchStats, fetchHistory])

  const handleCheck = async () => {
    if (!text.trim()) return
    setChecking(true)
    await checkContent(text)
    setChecking(false)
    setText('')
    await fetchStats()
    await fetchHistory()
  }

  const handleBatchCheck = async () => {
    const lines = batchText
      .split(/[\n,]/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
    if (lines.length === 0) return
    setBatchChecking(true)
    const items = lines.map((text) => ({ text }))
    await batchCheck(items)
    setBatchChecking(false)
    setBatchText('')
    await fetchStats()
    await fetchHistory()
  }

  const handleApplyFix = (resultId: string, originalText: string, violations: Array<{ matched: string; replacement?: string }>) => {
    const fixed = applyFixes(originalText, violations)
    setFixedTexts((prev) => ({ ...prev, [resultId]: fixed }))
  }

  const toggleHistory = (id: string) => {
    setExpandedHistory((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleClearHistory = async () => {
    await clearHistory()
    await fetchHistory()
  }

  const filteredRules = useMemo(() => {
    let list = rules
    if (levelFilter !== 'all') {
      list = list.filter((r) => r.level === levelFilter)
    }
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      list = list.filter(
        (r) =>
          r.category.toLowerCase().includes(q) ||
          r.description.toLowerCase().includes(q) ||
          r.rule_id.toLowerCase().includes(q)
      )
    }
    return list
  }, [rules, levelFilter, searchQuery])

  const batchResultSummary = useMemo(() => {
    const batchResults = results.filter((r) => r.original_text)
    if (batchResults.length === 0) return null
    const total = batchResults.length
    const pass = batchResults.filter((r) => r.violations.length === 0).length
    const fail = total - pass
    return { total, pass, fail }
  }, [results])

  const latestResults = useMemo(() => {
    // Show up to 5 latest results that have original_text (batch) or not (single)
    return results.slice(0, 5)
  }, [results])

  return (
    <div className="space-y-6">
      <PageHeader
        title="合规审核"
        subtitle="四层风控体系：L1法律红线 / L2平台规则 / L3账号策略 / L4动态风控"
      />

      {error && !dismissedError && (
        <AlertBanner
          variant="danger"
          title="错误"
          description={error}
          onDismiss={() => setDismissedError(true)}
        />
      )}

      {/* 四层风控统计看板 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 text-center">
          <ShieldAlert className="w-5 h-5 mx-auto mb-2 text-red-600" />
          <div className="text-2xl font-bold text-foreground tracking-tight">
            {stats?.l1?.today ?? 0}
          </div>
          <div className="text-xs text-muted-foreground mt-1">L1 法律红线</div>
          <div className="text-xs text-muted-foreground mt-1">
            累计拦截 {stats?.l1?.total ?? 0}
          </div>
        </Card>
        <Card className="p-4 text-center">
          <Shield className="w-5 h-5 mx-auto mb-2 text-warning" />
          <div className="text-2xl font-bold text-foreground tracking-tight">
            {stats?.l2?.today ?? 0}
          </div>
          <div className="text-xs text-muted-foreground mt-1">L2 平台规则</div>
          <div className="text-xs text-muted-foreground mt-1">
            累计命中 {stats?.l2?.total ?? 0}
          </div>
        </Card>
        <Card className="p-4 text-center">
          <FileText className="w-5 h-5 mx-auto mb-2 text-info" />
          <div className="text-2xl font-bold text-foreground tracking-tight">
            {stats?.l3?.today ?? 0}
          </div>
          <div className="text-xs text-muted-foreground mt-1">L3 账号策略</div>
        </Card>
        <Card className="p-4 text-center">
          <Activity className="w-5 h-5 mx-auto mb-2 text-primary" />
          <div className="text-2xl font-bold text-foreground tracking-tight">
            {stats?.l4?.today ?? 0}
          </div>
          <div className="text-xs text-muted-foreground mt-1">L4 动态风控</div>
        </Card>
      </div>

      {/* 内容合规扫描 */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ScanLine className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold">内容合规扫描</h3>
          </div>
          <div className="flex items-center gap-1 bg-secondary rounded-lg p-1">
            <button
              onClick={() => setActiveTab('single')}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                activeTab === 'single'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              单条扫描
            </button>
            <button
              onClick={() => setActiveTab('batch')}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                activeTab === 'batch'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              批量扫描
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {activeTab === 'single' ? (
            <>
              <textarea
                placeholder="粘贴需要审核的内容文本..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <div className="flex justify-end">
                <Button onClick={handleCheck} isLoading={checking}>
                  <ShieldCheck className="w-4 h-4" />
                  开始扫描
                </Button>
              </div>
            </>
          ) : (
            <>
              <textarea
                placeholder="每行输入一条内容，支持换行或逗号分隔..."
                value={batchText}
                onChange={(e) => setBatchText(e.target.value)}
                rows={6}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">
                  共 {batchText.split(/[\n,]/).filter((s) => s.trim().length > 0).length} 条内容
                </span>
                <Button onClick={handleBatchCheck} isLoading={batchChecking}>
                  <BarChart3 className="w-4 h-4" />
                  批量扫描
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* 扫描结果 */}
      {latestResults.length > 0 && (
        <Card>
          <CardHeader className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-warning" />
            <h3 className="text-base font-semibold">扫描结果</h3>
            {batchResultSummary && (
              <Badge variant="primary" className="ml-2">
                总{batchResultSummary.total}/通过{batchResultSummary.pass}/问题{batchResultSummary.fail}
              </Badge>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            {latestResults.map((result) => (
              <div
                key={result.evidence_id}
                className="p-4 rounded-lg border border-border bg-secondary/20"
              >
                <div className="flex items-center gap-2 mb-2">
                  {result.violations.length === 0 ? (
                    <CheckCircle className="w-4 h-4 text-success" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-warning" />
                  )}
                  <span className="text-sm font-medium">
                    {result.violations.length === 0
                      ? '合规通过'
                      : `发现 ${result.violations.length} 项问题`}
                  </span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    {new Date(result.checked_at).toLocaleString('zh-CN')}
                  </span>
                </div>

                {result.original_text && (
                  <p className="text-xs text-muted-foreground mb-2 truncate">
                    原文：{result.original_text}
                  </p>
                )}

                {result.violations.map((v, idx) => (
                  <div
                    key={idx}
                    className="mt-2 p-3 rounded-lg bg-destructive/5 border border-destructive/10"
                  >
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <Badge variant={levelVariants[v.level] || 'default'}>
                        {levelLabels[v.level] || v.level}
                      </Badge>
                      <span className="text-xs font-medium">{v.category}</span>
                      <span className="text-xs text-muted-foreground ml-auto">
                        规则 {v.rule_id}
                      </span>
                    </div>
                    <p className="text-sm text-foreground">{v.message}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      命中：「{v.matched}」
                    </p>
                    {v.suggestion && (
                      <p className="text-xs text-primary mt-1">建议：{v.suggestion}</p>
                    )}
                  </div>
                ))}

                {result.violations.some((v) => v.replacement) && result.original_text && (
                  <div className="mt-3 flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() =>
                        handleApplyFix(result.evidence_id, result.original_text!, result.violations)
                      }
                    >
                      <Wand2 className="w-3 h-3" />
                      一键应用建议
                    </Button>
                  </div>
                )}

                {fixedTexts[result.evidence_id] && (
                  <div className="mt-3 p-3 rounded-lg bg-success-bg border border-success-border">
                    <p className="text-xs font-medium text-success mb-1">修复后内容：</p>
                    <p className="text-sm text-foreground">{fixedTexts[result.evidence_id]}</p>
                  </div>
                )}

                {result.suggestions.length > 0 && result.violations.length === 0 && (
                  <div className="mt-2 space-y-1">
                    {result.suggestions.map((s, idx) => (
                      <p
                        key={idx}
                        className="text-xs text-muted-foreground flex items-center gap-1"
                      >
                        <Info className="w-3 h-3" /> {s}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 扫描历史记录 */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold">扫描历史记录</h3>
          </div>
          <Button size="sm" variant="ghost" onClick={handleClearHistory}>
            <Trash2 className="w-3 h-3" />
            清空历史
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading && history.length === 0 && (
            <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />
          )}
          {!isLoading && history.length === 0 && (
            <EmptyState icon={History} title="暂无扫描历史" description="完成扫描后将在此显示记录" />
          )}
          <div className="space-y-2">
            {history.map((item) => (
              <div
                key={item.id}
                className="p-3 rounded-lg border border-border hover:border-primary/30 transition-all cursor-pointer"
                onClick={() => toggleHistory(item.id)}
              >
                <div className="flex items-center gap-2">
                  {item.status === 'pass' ? (
                    <CheckCircle className="w-4 h-4 text-success shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-warning shrink-0" />
                  )}
                  <span className="text-sm font-medium flex-1 truncate">
                    {item.content_preview}
                  </span>
                  <Badge variant={item.status === 'pass' ? 'success' : 'warning'}>
                    {item.status === 'pass' ? '通过' : '问题'}
                  </Badge>
                  <span className="text-xs text-muted-foreground shrink-0">
                    命中 {item.violation_count} 条
                  </span>
                  {expandedHistory.has(item.id) ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
                  )}
                </div>
                {expandedHistory.has(item.id) && (
                  <div className="mt-2 pt-2 border-t border-border">
                    <p className="text-xs text-muted-foreground">
                      扫描时间：{new Date(item.checked_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 合规规则库 */}
      <Card>
        <CardHeader className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold">合规规则库</h3>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 sm:items-center justify-between">
            <div className="flex items-center gap-1">
              <Filter className="w-3 h-3 text-muted-foreground mr-1" />
              {levelFilters.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setLevelFilter(f.key)}
                  className={`px-2 py-1 text-xs rounded-md font-medium transition-colors ${
                    levelFilter === f.key
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <div className="relative">
              <Search className="w-3 h-3 text-muted-foreground absolute left-2 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="搜索规则分类或描述..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-7 pr-3 py-1.5 text-xs rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-ring w-full sm:w-56"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && filteredRules.length === 0 && (
            <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />
          )}
          {!isLoading && filteredRules.length === 0 && (
            <EmptyState icon={BookOpen} title="暂无规则数据" description="未找到匹配的规则，请调整筛选条件" />
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredRules.map((rule) => (
              <div
                key={rule.rule_id}
                className="p-3 rounded-lg border border-border hover:border-primary/30 transition-all"
              >
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <Badge variant={levelVariants[rule.level] || 'default'}>
                    {levelLabels[rule.level] || rule.level}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{rule.action}</span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    命中 {rule.hit_count ?? 0} 次
                  </span>
                </div>
                <p className="text-sm font-medium text-foreground">{rule.category}</p>
                <p className="text-xs text-muted-foreground mt-1">{rule.description}</p>
                <p className="text-xs text-muted-foreground mt-1">规则 ID：{rule.rule_id}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
