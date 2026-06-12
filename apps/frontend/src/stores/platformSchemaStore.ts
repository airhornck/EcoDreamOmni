import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface FieldConstraint {
  name: string
  label: string
  type: string
  required: boolean
  min?: number | string
  max?: number | string
  min_chars?: number
  max_chars?: number
  max_count?: number
  default?: unknown
  supported?: string[]
  description?: string
}

export interface ContentFormat {
  format_name: string
  fields: FieldConstraint[]
}

export interface PlatformSchema {
  id: string
  platform_id: string
  display_name: string
  version: string
  content_dna: Record<string, unknown>[]
  audit_rules: Record<string, unknown>[]
  content_formats: ContentFormat[]
}

export interface ValidateResult {
  passed: boolean
  errors: Array<{ field: string; message: string; severity: string }>
  platform_id: string
  format_name: string
}

export interface SyncResult {
  platform_id: string
  status: string
  message?: string
}

interface PlatformSchemaState {
  schemas: PlatformSchema[]
  isLoading: boolean
  error: string | null
  selectedPlatformId: string
  selectedFormatName: string
  validateResult: ValidateResult | null
  validateLoading: boolean
  syncLoading: boolean
  syncResults: SyncResult[] | null
  fetchSchemas: () => Promise<void>
  validateContent: (payload: {
    platform_id: string
    format_name: string
    content: Record<string, unknown>
    strict?: boolean
  }) => Promise<void>
  clearValidate: () => void
  syncFromYaml: (platformId?: string) => Promise<void>
}

export const usePlatformSchemaStore = create<PlatformSchemaState>((set, get) => ({
  schemas: [],
  isLoading: false,
  error: null,
  selectedPlatformId: 'xiaohongshu',
  selectedFormatName: '',
  validateResult: null,
  validateLoading: false,
  syncLoading: false,
  syncResults: null,

  fetchSchemas: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/platform-schemas', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取平台规范失败: ${res.status}`)
      const data = await res.json()
      const schemas = data.schemas || []
      set({ schemas, isLoading: false })
      // 自动选择第一个格式
      if (schemas.length > 0) {
        const first = schemas[0]
        if (first.content_formats.length > 0) {
          set({ selectedFormatName: first.content_formats[0].format_name })
        }
      }
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  validateContent: async (payload) => {
    set({ validateLoading: true, validateResult: null })
    try {
      const res = await fetch('/api/platform-schemas/validate', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ ...payload, strict: payload.strict ?? true }),
      })
      if (!res.ok) throw new Error('验证失败')
      const data = await res.json()
      set({ validateResult: data, validateLoading: false })
    } catch (err) {
      set({ validateLoading: false, error: err instanceof Error ? err.message : '验证失败' })
    }
  },

  clearValidate: () => set({ validateResult: null }),

  syncFromYaml: async (platformId) => {
    set({ syncLoading: true, syncResults: null })
    try {
      const url = platformId
        ? `/api/platform-schemas/sync-from-yaml?platform_id=${encodeURIComponent(platformId)}`
        : '/api/platform-schemas/sync-from-yaml'
      const res = await fetch(url, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('同步失败')
      const data = await res.json()
      set({ syncResults: data, syncLoading: false })
      await get().fetchSchemas()
    } catch (err) {
      set({ syncLoading: false, error: err instanceof Error ? err.message : '同步失败' })
    }
  },
}))
