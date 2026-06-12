import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface VetDrug {
  id: string
  approval_number: string
  product_name: string
  generic_name?: string
  english_name?: string
  manufacturer?: string
  ingredients?: string
  indications?: string
  usage_dosage?: string
  issue_date?: string
  expiry_date?: string
  status: 'ACTIVE' | 'EXPIRED' | 'REVOKED'
  brand_knowledge_id?: string
  created_at: string
  updated_at: string
}

interface VetDrugState {
  drugs: VetDrug[]
  isLoading: boolean
  error: string | null
  fetchDrugs: (filters?: Record<string, string>) => Promise<void>
  createDrug: (data: Partial<VetDrug>) => Promise<boolean>
  updateDrug: (id: string, data: Partial<VetDrug>) => Promise<boolean>
  deleteDrug: (id: string) => Promise<boolean>
  validateClaim: (approvalNumber: string, claimedIndications: string[]) => Promise<{ valid: boolean; violations: string[]; approved_indications: string[] }>
  bulkImport: (file: File) => Promise<{ imported: number; errors: unknown[] }>
  fetchExpiryWarnings: (days?: number) => Promise<VetDrug[]>
}

export const useVetDrugStore = create<VetDrugState>((set, get) => ({
  drugs: [],
  isLoading: false,
  error: null,

  fetchDrugs: async (filters = {}) => {
    set({ isLoading: true, error: null })
    try {
      const qs = new URLSearchParams(filters).toString()
      const res = await fetch(`/api/vetdrug/drugs?${qs}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取失败: ${res.status}`)
      const data = await res.json()
      set({ drugs: data.items || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createDrug: async (data) => {
    try {
      const res = await fetch('/api/vetdrug/drugs', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchDrugs()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  updateDrug: async (id, data) => {
    try {
      const res = await fetch(`/api/vetdrug/drugs/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('更新失败')
      await get().fetchDrugs()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  deleteDrug: async (id) => {
    try {
      const res = await fetch(`/api/vetdrug/drugs/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchDrugs()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },

  validateClaim: async (approvalNumber, claimedIndications) => {
    try {
      const res = await fetch('/api/vetdrug/validate-claim', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          approval_number: approvalNumber,
          claimed_indications: claimedIndications,
          claimed_effects: [],
        }),
      })
      if (!res.ok) throw new Error('校验失败')
      return await res.json()
    } catch (err) {
      return { valid: false, violations: [err instanceof Error ? err.message : '校验失败'], approved_indications: [] }
    }
  },

  bulkImport: async (file) => {
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/vetdrug/bulk-import', {
        method: 'POST',
        headers: authHeaders(false),
        body: form,
      })
      if (!res.ok) throw new Error('导入失败')
      const data = await res.json()
      await get().fetchDrugs()
      return { imported: data.imported_count || 0, errors: data.errors || [] }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '导入失败' })
      return { imported: 0, errors: [{ error: err instanceof Error ? err.message : '导入失败' }] }
    }
  },

  fetchExpiryWarnings: async (days = 90) => {
    try {
      const res = await fetch(`/api/vetdrug/expiry-warnings?days_ahead=${days}`, { headers: authHeaders() })
      if (!res.ok) throw new Error('获取预警失败')
      const data = await res.json()
      return data.warnings || []
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取预警失败' })
      return []
    }
  },
}))
