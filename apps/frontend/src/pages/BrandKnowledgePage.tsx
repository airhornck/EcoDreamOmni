import { useEffect, useState } from 'react'
import { useBrandKnowledgeStore } from '../stores/brandKnowledgeStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { BookOpen, Plus, Trash2, FileText, Tag, AlertTriangle, HelpCircle, Upload } from 'lucide-react'
import { authHeaders } from '../lib/api'

const typeLabels: Record<string, string> = {
  BRAND_INFO: '品牌信息',
  PRODUCT_INFO: '产品信息',
  FAQ: 'FAQ',
  PROHIBITED_CLAIM: '禁用语',
}

const typeIcons: Record<string, React.ElementType> = {
  BRAND_INFO: BookOpen,
  PRODUCT_INFO: FileText,
  FAQ: HelpCircle,
  PROHIBITED_CLAIM: AlertTriangle,
}

const typeColors: Record<string, string> = {
  BRAND_INFO: 'bg-info/15 text-info',
  PRODUCT_INFO: 'bg-success/15 text-success',
  FAQ: 'bg-purple-100 text-purple-700',
  PROHIBITED_CLAIM: 'bg-destructive/15 text-destructive',
}

interface BrandKnowledgeForm {
  entry_type: string
  name?: string
  content?: string
  product_id?: string
  brand_name?: string
  prohibited_claims?: string
  required_disclaimers?: string
}

export function BrandKnowledgePage() {
  const { entries, isLoading, error, fetchEntries, createEntry, deleteEntry } = useBrandKnowledgeStore()
  const [showCreate, setShowCreate] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [search, setSearch] = useState('')
  const [form, setForm] = useState<BrandKnowledgeForm>({ entry_type: 'BRAND_INFO' })

  useEffect(() => {
    fetchEntries(filterType ? { entry_type: filterType } : {})
  }, [fetchEntries, filterType])

  const filtered = entries.filter((e) =>
    !search || e.name.toLowerCase().includes(search.toLowerCase()) || e.content.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async () => {
    if (!form.name?.trim() || !form.content?.trim()) return
    const success = await createEntry({
      entry_type: form.entry_type,
      name: form.name,
      content: form.content,
      product_id: form.product_id || undefined,
      brand_name: form.brand_name || undefined,
      prohibited_claims: (form.prohibited_claims || '').split(',').map((s) => s.trim()).filter(Boolean),
      required_disclaimers: (form.required_disclaimers || '').split(',').map((s) => s.trim()).filter(Boolean),
    } as Record<string, unknown>)
    if (success) {
      setShowCreate(false)
      setForm({ entry_type: 'BRAND_INFO' })
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="品牌资料库"
        subtitle="品牌故事、产品SKU、卖点、禁用语、FAQ — 内容生成时的RAG真源"
        action={
          <div className="flex gap-2">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={async (e) => {
                  const f = e.target.files?.[0]
                  if (!f) return
                  const form = new FormData()
                  form.append('file', f)
                  try {
                    const res = await fetch('/api/brand-knowledge/bulk-import', {
                      method: 'POST',
                      headers: authHeaders(false),
                      body: form,
                    })
                    const data = await res.json()
                    alert(`导入完成: ${data.imported_count} 条成功${data.errors?.length > 0 ? `, ${data.errors.length} 条失败` : ''}`)
                    fetchEntries()
                  } catch {
                    alert('导入失败')
                  }
                  e.target.value = ''
                }}
              />
              <span className="inline-flex items-center gap-1 h-9 px-3 rounded-lg border border-border bg-background text-sm hover:bg-secondary transition-colors">
                <Upload className="w-4 h-4" />
                CSV导入
              </span>
            </label>
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="w-4 h-4" />
              新增条目
            </Button>
          </div>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-3">
            <select
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="">全部类型</option>
              <option value="BRAND_INFO">品牌信息</option>
              <option value="PRODUCT_INFO">产品信息</option>
              <option value="FAQ">FAQ</option>
              <option value="PROHIBITED_CLAIM">禁用语</option>
            </select>
            <input
              type="text"
              placeholder="搜索名称或内容..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm flex-1 min-w-[200px]"
            />
            <Button variant="ghost" size="sm" onClick={() => { setFilterType(''); setSearch('') }}>
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Create Drawer */}
      {showCreate && (
        <Card>
          <CardHeader><h3 className="text-base font-semibold">新增品牌知识条目</h3></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <select
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.entry_type || 'BRAND_INFO'}
                onChange={(e) => setForm({ ...form, entry_type: e.target.value })}
              >
                <option value="BRAND_INFO">品牌信息</option>
                <option value="PRODUCT_INFO">产品信息</option>
                <option value="FAQ">FAQ</option>
                <option value="PROHIBITED_CLAIM">禁用语</option>
              </select>
              <input
                placeholder="条目名称 *"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.name || ''}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
              <input
                placeholder="品牌名"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.brand_name || ''}
                onChange={(e) => setForm({ ...form, brand_name: e.target.value })}
              />
              <input
                placeholder="产品ID"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.product_id || ''}
                onChange={(e) => setForm({ ...form, product_id: e.target.value })}
              />
            </div>
            <textarea
              placeholder="内容 *"
              rows={4}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              value={form.content || ''}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                placeholder="禁用语清单（逗号分隔）"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.prohibited_claims || ''}
                onChange={(e) => setForm({ ...form, prohibited_claims: e.target.value })}
              />
              <input
                placeholder="必要声明（逗号分隔）"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.required_disclaimers || ''}
                onChange={(e) => setForm({ ...form, required_disclaimers: e.target.value })}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
              <Button onClick={handleCreate}>保存</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* List */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">知识条目列表 ({filtered.length})</h2>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && filtered.length === 0 && (
            <EmptyState icon={BookOpen} title="暂无条目" description="创建你的第一条品牌知识" />
          )}
          <div className="space-y-2">
            {filtered.map((entry) => {
              const Icon = typeIcons[entry.entry_type] || Tag
              return (
                <div key={entry.id} className="p-4 rounded-lg border border-border hover:border-primary/30 transition-all">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className="w-4 h-4 text-muted-foreground" />
                        <h3 className="text-sm font-medium text-foreground truncate">{entry.name}</h3>
                        <Badge className={typeColors[entry.entry_type] || 'bg-muted'}>
                          {typeLabels[entry.entry_type] || entry.entry_type}
                        </Badge>
                        {entry.is_latest && <Badge variant="default" className="bg-transparent border-border text-muted-foreground">最新</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2">{entry.content}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {entry.prohibited_claims?.map((c) => (
                          <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-destructive/15 text-red-600">{c}</span>
                        ))}
                        {entry.brand_name && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-info/15 text-blue-600">{entry.brand_name}</span>
                        )}
                      </div>
                    </div>
                    <button onClick={() => deleteEntry(entry.id)} className="p-1.5 hover:bg-destructive/10 rounded ml-2">
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
