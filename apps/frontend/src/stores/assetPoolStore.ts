import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface Asset {
  id: string
  name: string
  type: string
  url: string
  thumbnail_url?: string
  tags: string[]
  created_at: string
}

interface AssetPoolState {
  assets: Asset[]
  isLoading: boolean
  error: string | null
  fetchAssets: () => Promise<void>
  createAsset: (data: Partial<Asset>) => Promise<boolean>
  uploadAssetFile: (file: File, metadata?: { tags?: string; category?: string; description?: string }) => Promise<boolean>
  deleteAsset: (id: string) => Promise<boolean>
}

interface BackendAssetItem {
  id: string
  type?: string
  meta_mime_type?: string
  source_type?: string
  filename?: string
  name?: string
  url?: string
  file_url?: string
  thumbnail_url?: string
  tags?: string[]
  created_at: string
}

function _mapAsset(item: BackendAssetItem): Asset {
  // Backend now returns derived type; fallback to mime_type / filename / source_type
  const type = item.type
    || (item.meta_mime_type || '').split('/')[0]
    || (item.source_type === 'OPERATOR_UPLOAD' && item.filename?.match(/\.(jpg|jpeg|png|webp|gif|bmp|svg)$/i) ? 'image' : '')
    || 'unknown'
  return {
    id: item.id,
    name: item.name || item.filename || '未命名',
    type,
    url: item.url || item.file_url || '',
    thumbnail_url: item.thumbnail_url || item.url || item.file_url || '',
    tags: item.tags || [],
    created_at: item.created_at,
  }
}

export const useAssetPoolStore = create<AssetPoolState>((set, get) => ({
  assets: [],
  isLoading: false,
  error: null,

  fetchAssets: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/assets', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取素材列表失败: ${res.status}`)
      const data = await res.json()
      const items = data.assets || data.items || []
      set({ assets: items.map(_mapAsset), isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createAsset: async (data) => {
    try {
      // 后端 upload 接口字段名不同，需要做映射
      // category 是宠物分类（cat/dog/general），不是素材类型
      const payload = {
        filename: data.name,
        file_url: data.url,
        source_type: data.type === 'image' || data.type === 'video' ? 'OPERATOR_UPLOAD' : (data.type || 'OPERATOR_UPLOAD'),
        license_type: 'OWNED',
        tags: data.tags,
        category: 'GENERAL_PET',
        generate_thumbnail: false,
      }
      const res = await fetch('/api/assets/upload', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchAssets()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  uploadAssetFile: async (file, metadata = {}) => {
    try {
      const form = new FormData()
      form.append('file', file)
      if (metadata.tags) form.append('tags', metadata.tags)
      if (metadata.category) form.append('category', metadata.category)
      if (metadata.description) form.append('description', metadata.description)
      const res = await fetch('/api/assets/upload-file', {
        method: 'POST',
        headers: authHeaders(false), // FormData 不设置 Content-Type
        body: form,
      })
      if (!res.ok) throw new Error('上传失败')
      await get().fetchAssets()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '上传失败' })
      return false
    }
  },

  deleteAsset: async (id) => {
    try {
      const res = await fetch(`/api/assets/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchAssets()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },
}))
