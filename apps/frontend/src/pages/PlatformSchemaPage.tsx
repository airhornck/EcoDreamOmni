import { useEffect, useMemo, useState } from 'react'
import { usePlatformSchemaStore, type FieldConstraint, type PlatformSchema } from '../stores/platformSchemaStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { cn } from '../lib/utils'
import {
  LayoutTemplate, Play, Smartphone, Video, Tv, Globe,
  FileText, CheckCircle2, XCircle, AlertTriangle, RefreshCw,
  ShieldCheck, ShieldAlert,
} from 'lucide-react'

/* ── config ── */

const platformMeta: Record<string, { label: string; icon: React.ElementType }> = {
  xiaohongshu: { label: '小红书', icon: Smartphone },
  douyin: { label: '抖音', icon: Video },
  wechat_official: { label: '微信公众号', icon: FileText },
  bilibili: { label: '哔哩哔哩', icon: Tv },
}

const formatIcons: Record<string, React.ElementType> = {
  '图文': FileText,
  '视频': Video,
  '仅文字': FileText,
  '笔记': FileText,
  '文章': FileText,
  '动态': FileText,
}

/* ── helpers ── */

function formatConstraint(field: FieldConstraint): string {
  const parts: string[] = []
  if (field.min_chars !== undefined) parts.push(`最少 ${field.min_chars} 字`)
  if (field.max_chars !== undefined) parts.push(`最多 ${field.max_chars} 字`)
  if (field.min !== undefined) parts.push(`最小: ${field.min}`)
  if (field.max !== undefined) parts.push(`最大: ${field.max}`)
  if (field.max_count !== undefined) parts.push(`最多 ${field.max_count} 个`)
  if (field.supported) parts.push(`支持: ${field.supported.join(', ')}`)
  if (field.default !== undefined) parts.push(`默认: ${field.default}`)
  return parts.join('；') || '—'
}

/* ── ValidatePanel ── */

function ValidatePanel({ schema }: { schema: PlatformSchema }) {
  const { validateContent, validateResult, validateLoading, clearValidate } = usePlatformSchemaStore()
  const [formatName, setFormatName] = useState(schema.content_formats[0]?.format_name || '')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [tags, setTags] = useState('')
  const [strict, setStrict] = useState(true)

  const currentFormat = schema.content_formats.find((f) => f.format_name === formatName)

  const handleRun = () => {
    const payload: Record<string, unknown> = {}
    if (title.trim()) payload.title = title.trim()
    if (content.trim()) payload.content = content.trim()
    if (tags.trim()) payload.tags = tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean)

    validateContent({
      platform_id: schema.platform_id,
      format_name: formatName,
      content: payload,
      strict,
    })
  }

  return (
    <Card>
      <CardHeader className="flex items-center gap-2">
        <Play className="w-4 h-4 text-primary" />
        <h3 className="text-base font-semibold">格式校验</h3>
        <span className="text-xs text-muted-foreground">按平台格式规范验证内容</span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-3 flex-wrap">
          <select
            value={formatName}
            onChange={(e) => setFormatName(e.target.value)}
            className="h-10 px-3 rounded-lg border border-border bg-background text-sm"
          >
            {schema.content_formats.map((f) => (
              <option key={f.format_name} value={f.format_name}>{f.format_name}</option>
            ))}
          </select>
          <input
            type="text" placeholder="标题" value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="flex-1 min-w-[10rem] h-10 px-3 rounded-lg border border-border bg-background text-sm"
          />
        </div>
        <textarea
          placeholder="正文内容..." value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y"
        />
        <input
          type="text" placeholder="标签，用逗号分隔" value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        />
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox" checked={strict}
              onChange={(e) => setStrict(e.target.checked)}
              className="rounded"
            />
            严格模式
          </label>
          <span className="text-xs text-muted-foreground">
            格式: {currentFormat?.format_name || '—'}（{currentFormat?.fields.length || 0} 个字段）
          </span>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleRun} isLoading={validateLoading} disabled={!title.trim() && !content.trim()}>
            <Play className="w-4 h-4" />
            运行验证
          </Button>
          {validateResult && (
            <Button variant="ghost" onClick={clearValidate}>清除结果</Button>
          )}
        </div>

        {validateResult && (
          <div className="space-y-2 mt-2">
            <div className="flex items-center gap-2">
              {validateResult.passed ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-success" />
                  <span className="text-sm font-medium text-success">通过 — 内容符合格式规范</span>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-destructive" />
                  <span className="text-sm font-medium text-destructive">
                    未通过 — {validateResult.errors.length} 个错误
                  </span>
                </>
              )}
            </div>
            {validateResult.errors.length > 0 && (
              <div className="space-y-1.5">
                {validateResult.errors.map((e, i) => (
                  <div
                    key={i}
                    className={cn(
                      'p-2 rounded-lg text-xs space-y-0.5',
                      e.severity === 'error' ? 'bg-destructive/10 text-destructive' : 'bg-warning/10 text-warning'
                    )}
                  >
                    <div className="font-medium flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {e.field}
                      <Badge variant={e.severity === 'error' ? 'danger' : 'warning'} className="text-[10px] px-1 py-0">
                        {e.severity === 'error' ? '错误' : '警告'}
                      </Badge>
                    </div>
                    <div className="opacity-80">{e.message}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/* ── FormatDetail ── */

function FormatDetail({ format }: { format: { format_name: string; fields: FieldConstraint[] } }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-base font-semibold">{format.format_name}</h3>
        <Badge variant="default">{format.fields.length} 个字段</Badge>
      </div>
      <div className="rounded-lg border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/50">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-xs text-muted-foreground">字段</th>
              <th className="text-left px-3 py-2 font-medium text-xs text-muted-foreground">标签</th>
              <th className="text-left px-3 py-2 font-medium text-xs text-muted-foreground">类型</th>
              <th className="text-left px-3 py-2 font-medium text-xs text-muted-foreground">必填</th>
              <th className="text-left px-3 py-2 font-medium text-xs text-muted-foreground">约束</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {format.fields.map((field) => (
              <tr key={field.name} className="hover:bg-secondary/20">
                <td className="px-3 py-2 font-mono text-xs">{field.name}</td>
                <td className="px-3 py-2">{field.label}</td>
                <td className="px-3 py-2">
                  <Badge variant="default" className="text-[10px]">{field.type}</Badge>
                </td>
                <td className="px-3 py-2">
                  {field.required ? (
                    <Badge variant="danger" className="text-[10px]">必填</Badge>
                  ) : (
                    <Badge variant="default" className="text-[10px]">可选</Badge>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground max-w-[20rem] truncate" title={formatConstraint(field)}>
                  {formatConstraint(field)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ── Main Page ── */

export function PlatformSchemaPage() {
  const {
    schemas, isLoading, error, selectedPlatformId, syncLoading, syncResults,
    fetchSchemas, syncFromYaml,
  } = usePlatformSchemaStore()
  const [activeFormat, setActiveFormat] = useState('')

  useEffect(() => {
    fetchSchemas()
  }, [fetchSchemas])

  const selectedSchema = useMemo(
    () => schemas.find((s) => s.platform_id === selectedPlatformId) || null,
    [schemas, selectedPlatformId]
  )

  useEffect(() => {
    if (selectedSchema && selectedSchema.content_formats.length > 0) {
      const fmt = selectedSchema.content_formats[0].format_name
      requestAnimationFrame(() => setActiveFormat(fmt))
    }
  }, [selectedSchema])

  const activeFormatData = useMemo(
    () => selectedSchema?.content_formats.find((f) => f.format_name === activeFormat),
    [selectedSchema, activeFormat]
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="平台格式规范"
        subtitle="各平台 API 发布格式规范（YAML 真源驱动）"
        action={
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => syncFromYaml()}
              isLoading={syncLoading}
            >
              <RefreshCw className="w-4 h-4" />
              同步 YAML
            </Button>
          </div>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {syncResults && (
        <div className="p-3 rounded-lg bg-success/10 text-success text-sm space-y-1">
          <div className="font-medium">同步结果</div>
          {syncResults.map((r) => (
            <div key={r.platform_id} className="flex items-center gap-2 text-xs">
              <span>{r.platform_id}:</span>
              <Badge
                variant={r.status === 'synced' ? 'success' : r.status === 'error' ? 'danger' : 'default'}
                className="text-[10px]"
              >
                {r.status}
              </Badge>
              {r.message && <span className="text-muted-foreground">{r.message}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Platform Filter */}
      <div className="flex gap-2 flex-wrap">
        {schemas.map((s) => {
          const meta = platformMeta[s.platform_id] || { label: s.display_name, icon: Globe }
          const Icon = meta.icon
          const active = selectedPlatformId === s.platform_id
          return (
            <button
              key={s.platform_id}
              onClick={() => usePlatformSchemaStore.setState({ selectedPlatformId: s.platform_id })}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              )}
            >
              <Icon className="w-4 h-4" />
              {meta.label}
              <span className="text-xs opacity-70">v{s.version}</span>
            </button>
          )
        })}
      </div>

      {/* Validate Panel */}
      {selectedSchema && <ValidatePanel schema={selectedSchema} />}

      {/* Format Tabs */}
      {selectedSchema && selectedSchema.content_formats.length > 0 && (
        <Card>
          <CardHeader className="flex items-center gap-2">
            <LayoutTemplate className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold">内容格式</h2>
            <Badge variant="default">{selectedSchema.content_formats.length} 种格式</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2 border-b border-border pb-2">
              {selectedSchema.content_formats.map((f) => {
                const Icon = formatIcons[f.format_name] || FileText
                const active = activeFormat === f.format_name
                return (
                  <button
                    key={f.format_name}
                    onClick={() => setActiveFormat(f.format_name)}
                    className={cn(
                      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                      active
                        ? 'bg-primary/10 text-primary'
                        : 'text-foreground hover:bg-secondary'
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {f.format_name}
                  </button>
                )
              })}
            </div>
            {activeFormatData ? (
              <FormatDetail format={activeFormatData} />
            ) : (
              <EmptyState icon={LayoutTemplate} title="选择格式" description="点击上方标签查看字段约束详情" />
            )}
          </CardContent>
        </Card>
      )}

      {/* Schema Meta */}
      {selectedSchema && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold">内容 DNA</h3>
            </CardHeader>
            <CardContent>
              {selectedSchema.content_dna.length === 0 ? (
                <EmptyState icon={ShieldCheck} title="无内容 DNA" description="该平台未定义内容 DNA" />
              ) : (
                <div className="space-y-2">
                  {selectedSchema.content_dna.map((dna, i) => (
                    <div key={i} className="rounded-lg bg-secondary/30 p-3 text-sm space-y-1">
                      <pre className="text-xs overflow-auto">{JSON.stringify(dna, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold">审核规则</h3>
            </CardHeader>
            <CardContent>
              {selectedSchema.audit_rules.length === 0 ? (
                <EmptyState icon={ShieldAlert} title="无审核规则" description="该平台未定义审核规则" />
              ) : (
                <div className="space-y-2">
                  {selectedSchema.audit_rules.map((rule, i) => (
                    <div key={i} className="rounded-lg bg-secondary/30 p-3 text-sm space-y-1">
                      <pre className="text-xs overflow-auto">{JSON.stringify(rule, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {isLoading && (
        <div className="space-y-4">
          <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />
          <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />
        </div>
      )}

      {!isLoading && schemas.length === 0 && (
        <EmptyState
          icon={LayoutTemplate}
          title="暂无平台规范"
          description="请先点击「同步 YAML」从真源目录加载平台格式规范"
        />
      )}
    </div>
  )
}
