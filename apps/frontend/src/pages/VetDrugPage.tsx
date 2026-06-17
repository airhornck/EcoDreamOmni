import { useEffect, useState } from 'react'
import { useVetDrugStore, type VetDrug } from '../stores/vetDrugStore'
import { usePageCopilot } from '../hooks/usePageCopilot'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { Pill, Plus, Trash2, AlertTriangle, CheckCircle2, ShieldCheck, Upload, Calendar } from 'lucide-react'

const statusColors: Record<string, string> = {
  ACTIVE: 'bg-success/15 text-success',
  EXPIRED: 'bg-destructive/15 text-destructive',
  REVOKED: 'bg-muted text-foreground',
}

interface VetDrugForm {
  status: string
  approval_number?: string
  product_name?: string
  generic_name?: string
  manufacturer?: string
  ingredients?: string
  indications?: string
  usage_dosage?: string
  issue_date?: string
  expiry_date?: string
}

export function VetDrugPage() {
  const { drugs, isLoading, error, fetchDrugs, createDrug, deleteDrug, validateClaim } = useVetDrugStore()
  const [showCreate, setShowCreate] = useState(false)
  const [showValidate, setShowValidate] = useState(false)
  const [filterStatus, setFilterStatus] = useState('')
  const [validateResult, setValidateResult] = useState<{ valid: boolean; violations?: string[]; approved_indications?: string[] } | null>(null)
  const [form, setForm] = useState<VetDrugForm>({ status: 'ACTIVE' })

  useEffect(() => {
    fetchDrugs(filterStatus ? { status: filterStatus } : {})
  }, [fetchDrugs, filterStatus])

  const handleCreate = async () => {
    if (!form.approval_number?.trim() || !form.product_name?.trim()) return
    const success = await createDrug({
      approval_number: form.approval_number,
      product_name: form.product_name,
      generic_name: form.generic_name || undefined,
      manufacturer: form.manufacturer || undefined,
      ingredients: form.ingredients || undefined,
      indications: form.indications || undefined,
      usage_dosage: form.usage_dosage || undefined,
      issue_date: form.issue_date || undefined,
      expiry_date: form.expiry_date || undefined,
      status: form.status || 'ACTIVE',
    } as Record<string, unknown>)
    if (success) {
      setShowCreate(false)
      setForm({ status: 'active' })
    }
  }

  const [validateForm, setValidateForm] = useState({ approval_number: '', indications: '' })
  const [expiryWarnings, setExpiryWarnings] = useState<VetDrug[]>([])
  const [showWarnings, setShowWarnings] = useState(false)

  const loadExpiryWarnings = async () => {
    const warnings = await useVetDrugStore.getState().fetchExpiryWarnings(90)
    setExpiryWarnings(warnings)
  }

  // Copilot 联动（放在 setShowWarnings/loadExpiryWarnings 声明之后）
  usePageCopilot(
    [
      {
        id: 'vet-create',
        type: 'decision',
        title: '➕ 新增兽药批文',
        description: '录入新的兽药批准文号及产品信息',
        priority: 1,
        actions: [{ id: 'create_drug', label: '新增', variant: 'primary' }],
      },
      {
        id: 'vet-validate',
        type: 'decision',
        title: '🛡️ 宣称校验',
        description: '校验产品宣称适应症是否在批文范围内',
        priority: 2,
        actions: [{ id: 'validate_claim', label: '校验', variant: 'primary' }],
      },
      {
        id: 'vet-expiry',
        type: 'info',
        title: '⏰ 到期预警',
        description: '查看 90 天内即将过期或已失效的批文',
        priority: 3,
        actions: [{ id: 'expiry_warnings', label: '查看', variant: 'secondary' }],
      },
      {
        id: 'vet-import',
        type: 'decision',
        title: '📤 CSV 批量导入',
        description: '通过 CSV 批量导入兽药批文数据',
        priority: 4,
        actions: [{ id: 'bulk_import', label: '导入', variant: 'secondary' }],
      },
    ],
    async (_cardId, actionId) => {
      if (actionId === 'create_drug') {
        setShowCreate(true)
      } else if (actionId === 'validate_claim') {
        setShowValidate(true)
      } else if (actionId === 'expiry_warnings') {
        setShowWarnings(true)
        await loadExpiryWarnings()
      } else if (actionId === 'bulk_import') {
        const input = document.querySelector('input[type="file"]') as HTMLInputElement | null
        input?.click()
      }
    }
  )

  const handleValidate = async () => {
    if (!validateForm.approval_number.trim() || !validateForm.indications.trim()) return
    const indications = validateForm.indications.split(/[\n,，]/).map(s => s.trim()).filter(Boolean)
    const result = await validateClaim(validateForm.approval_number, indications)
    setValidateResult(result)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="兽药批文库"
        subtitle="兽药批文真源：批文录入、宣称校验、到期预警、产品关联"
        action={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => { setShowWarnings(true); loadExpiryWarnings() }}>
              <Calendar className="w-4 h-4" />
              到期预警
            </Button>
            <Button variant="outline" onClick={() => setShowValidate(true)}>
              <ShieldCheck className="w-4 h-4" />
              宣称校验
            </Button>
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={async (e) => {
                  const f = e.target.files?.[0]
                  if (!f) return
                  const result = await useVetDrugStore.getState().bulkImport(f)
                  alert(`导入完成: ${result.imported} 条成功${result.errors.length > 0 ? `, ${result.errors.length} 条失败` : ''}`)
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
              新增批文
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
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="">全部状态</option>
              <option value="ACTIVE">有效</option>
              <option value="EXPIRED">已过期</option>
              <option value="REVOKED">已撤销</option>
            </select>
            <Button variant="ghost" size="sm" onClick={() => setFilterStatus('')}>
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Expiry Warnings */}
      {showWarnings && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <Calendar className="w-4 h-4 text-amber-500" />
              批文到期预警（90天内）
            </h3>
            <Button variant="ghost" size="sm" onClick={() => setShowWarnings(false)}>关闭</Button>
          </CardHeader>
          <CardContent>
            {expiryWarnings.length === 0 ? (
              <p className="text-sm text-muted-foreground">暂无即将到期的批文</p>
            ) : (
              <div className="space-y-2">
                {expiryWarnings.map((d) => (
                  <div key={d.id} className="flex items-center justify-between p-2 rounded bg-amber-50 text-sm">
                    <span>{d.approval_number} — {d.product_name}</span>
                    <span className="text-amber-700">有效期至: {d.expiry_date?.slice(0, 10)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Validate Claim */}
      {showValidate && (
        <Card>
          <CardHeader><h3 className="text-base font-semibold">功效宣称合规校验</h3></CardHeader>
          <CardContent className="space-y-3">
            <select
              className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
              value={validateForm.approval_number}
              onChange={(e) => setValidateForm({ ...validateForm, approval_number: e.target.value })}
            >
              <option value="">选择批文号...</option>
              {drugs.map(d => (
                <option key={d.id} value={d.approval_number}>{d.approval_number} — {d.product_name}</option>
              ))}
            </select>
            <textarea
              placeholder="输入需要校验的功效宣称（每行一条，或逗号分隔）..."
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              value={validateForm.indications}
              onChange={(e) => setValidateForm({ ...validateForm, indications: e.target.value })}
            />
            <div className="flex justify-between items-center">
              <Button variant="ghost" onClick={() => { setShowValidate(false); setValidateResult(null); setValidateForm({ approval_number: '', indications: '' }) }}>
                取消
              </Button>
              <Button onClick={handleValidate}>
                <ShieldCheck className="w-4 h-4" />
                校验
              </Button>
            </div>
            {validateResult && (
              <div className={`p-3 rounded-lg text-sm ${validateResult.valid ? 'bg-success/15 text-success' : 'bg-destructive/15 text-destructive'}`}>
                <div className="flex items-center gap-2">
                  {validateResult.valid ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                  <span className="font-medium">{validateResult.valid ? '宣称合规' : '宣称不合规'}</span>
                </div>
                {validateResult.violations && validateResult.violations.length > 0 && (
                  <ul className="mt-1 text-xs list-disc list-inside">
                    {validateResult.violations.map((v, i) => <li key={i}>{v}</li>)}
                  </ul>
                )}
                {validateResult.approved_indications && validateResult.approved_indications.length > 0 && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    批准适应症: {validateResult.approved_indications.join('、')}
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Create Drawer */}
      {showCreate && (
        <Card>
          <CardHeader><h3 className="text-base font-semibold">新增兽药批文</h3></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                placeholder="批文号 *（如：兽药字220125001）"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.approval_number || ''}
                onChange={(e) => setForm({ ...form, approval_number: e.target.value })}
              />
              <input
                placeholder="产品名称 *"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.product_name || ''}
                onChange={(e) => setForm({ ...form, product_name: e.target.value })}
              />
              <input
                placeholder="通用名"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.generic_name || ''}
                onChange={(e) => setForm({ ...form, generic_name: e.target.value })}
              />
              <input
                placeholder="生产厂家"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.manufacturer || ''}
                onChange={(e) => setForm({ ...form, manufacturer: e.target.value })}
              />
              <input
                type="date"
                placeholder="签发日期"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.issue_date || ''}
                onChange={(e) => setForm({ ...form, issue_date: e.target.value })}
              />
              <input
                type="date"
                placeholder="有效期至"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.expiry_date || ''}
                onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
              />
            </div>
            <textarea
              placeholder="有效成分"
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              value={form.ingredients || ''}
              onChange={(e) => setForm({ ...form, ingredients: e.target.value })}
            />
            <textarea
              placeholder="适应症"
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              value={form.indications || ''}
              onChange={(e) => setForm({ ...form, indications: e.target.value })}
            />
            <textarea
              placeholder="用法用量"
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              value={form.usage_dosage || ''}
              onChange={(e) => setForm({ ...form, usage_dosage: e.target.value })}
            />
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
          <Pill className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">批文列表 ({drugs.length})</h2>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && drugs.length === 0 && (
            <EmptyState icon={Pill} title="暂无批文" description="录入第一条兽药批文信息" />
          )}
          <div className="space-y-2">
            {drugs.map((drug) => (
              <div key={drug.id} className="p-4 rounded-lg border border-border hover:border-primary/30 transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Pill className="w-4 h-4 text-muted-foreground" />
                      <h3 className="text-sm font-medium text-foreground">{drug.product_name}</h3>
                      <Badge className={statusColors[drug.status] || 'bg-muted'}>
                        {drug.status === 'ACTIVE' ? '有效' : drug.status === 'EXPIRED' ? '已过期' : '已撤销'}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-1 text-xs text-muted-foreground">
                      <span>批文号: {drug.approval_number}</span>
                      {drug.generic_name && <span>通用名: {drug.generic_name}</span>}
                      {drug.manufacturer && <span>厂家: {drug.manufacturer}</span>}
                      {drug.expiry_date && (
                        <span className={new Date(drug.expiry_date) < new Date() ? 'text-red-500' : ''}>
                          有效期至: {drug.expiry_date.slice(0, 10)}
                        </span>
                      )}
                    </div>
                    {drug.indications && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-1">适应症: {drug.indications}</p>
                    )}
                  </div>
                  <button onClick={() => deleteDrug(drug.id)} className="p-1.5 hover:bg-destructive/10 rounded ml-2">
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
