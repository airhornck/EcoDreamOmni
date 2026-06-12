import { useEffect, useRef, useState } from 'react'
import { useAssetPoolStore } from '../../stores/assetPoolStore'
import { Button } from '../ui/Button'
import { ImageOff, Upload, X, ImageIcon } from 'lucide-react'

interface CoverPickerModalProps {
  open: boolean
  onClose: () => void
  onSelect: (url: string, ratio?: string) => void
}

export function CoverPickerModal({ open, onClose, onSelect }: CoverPickerModalProps) {
  const { assets, isLoading, error, fetchAssets, uploadAssetFile } = useAssetPoolStore()
  const [activeTab, setActiveTab] = useState<'library' | 'upload'>('library')
  const [selectedRatio, setSelectedRatio] = useState('3:4')
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const ratios = [
    { label: '1:1', value: '1:1', className: 'aspect-square' },
    { label: '3:4', value: '3:4', className: 'aspect-[3/4]' },
    { label: '4:3', value: '4:3', className: 'aspect-[4/3]' },
    { label: '9:16', value: '9:16', className: 'aspect-[9/16]' },
    { label: '16:9', value: '16:9', className: 'aspect-[16/9]' },
    { label: '3:1', value: '3:1', className: 'aspect-[3/1]' },
  ]

  useEffect(() => {
    if (open && activeTab === 'library') {
      fetchAssets()
    }
  }, [open, activeTab, fetchAssets])

  const imageAssets = assets.filter((a) => (a.type || '').startsWith('image'))

  const ALLOWED_EXTS = ['.jpg', '.jpeg', '.png']

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 格式校验：仅允许 jpg / png
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    if (!ALLOWED_EXTS.includes(ext)) {
      alert(`仅支持 JPG、PNG 格式，当前文件：${file.name}`)
      // 重置 input 以便可再次选择同一文件
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }

    setUploading(true)
    try {
      const success = await uploadAssetFile(file, { tags: 'cover' })
      if (success) {
        await fetchAssets()
        setActiveTab('library')
      }
    } catch {
      // error handled by store
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-background rounded-xl border border-border shadow-lg w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="text-base font-semibold">选择封面</h2>
          <button onClick={onClose} className="p-1 hover:bg-secondary rounded">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-secondary rounded-lg p-0.5 m-4 mb-0 w-fit">
          <button
            onClick={() => setActiveTab('library')}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'library' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5 inline mr-1" />
            素材库
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'upload' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground'
            }`}
          >
            <Upload className="w-3.5 h-3.5 inline mr-1" />
            本地上传
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'library' && (
            <>
              {isLoading && (
                <div className="grid grid-cols-4 gap-3">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="aspect-square animate-pulse bg-secondary rounded-lg" />
                  ))}
                </div>
              )}
              {!isLoading && error && (
                <div className="text-sm text-destructive">{error}</div>
              )}
              {!isLoading && !error && imageAssets.length === 0 && (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <ImageOff className="w-8 h-8 mb-2" />
                  <p className="text-sm">暂无图片素材</p>
                  <Button size="sm" variant="outline" className="mt-3" onClick={() => setActiveTab('upload')}>
                    <Upload className="w-3.5 h-3.5 mr-1" />
                    上传图片
                  </Button>
                </div>
              )}
              {!isLoading && imageAssets.length > 0 && (
                <>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs text-muted-foreground">裁剪比例：</span>
                    <div className="flex gap-1">
                      {ratios.map((r) => (
                        <button
                          key={r.value}
                          onClick={() => setSelectedRatio(r.value)}
                          className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                            selectedRatio === r.value
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                          }`}
                        >
                          {r.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-3">
                    {imageAssets.map((asset) => (
                      <button
                        key={asset.id}
                        onClick={() => onSelect(asset.url, selectedRatio)}
                        className="group relative rounded-lg border border-border overflow-hidden hover:border-primary transition-colors"
                      >
                        <div className={ratios.find((r) => r.value === selectedRatio)?.className || 'aspect-square'}>
                          <img
                            src={asset.thumbnail_url || asset.url}
                            alt={asset.name}
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                        </div>
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
                      </button>
                    ))}
                  </div>
                </>
              )}
            </>
          )}

          {activeTab === 'upload' && (
            <div className="flex flex-col items-center justify-center py-8">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="w-full max-w-sm h-48 border-2 border-dashed border-border rounded-xl flex flex-col items-center justify-center cursor-pointer hover:border-primary hover:bg-secondary/30 transition-colors"
              >
                <Upload className="w-8 h-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">点击或拖拽上传图片</p>
                <p className="text-xs text-muted-foreground mt-1">支持 JPG、PNG、WebP</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".jpg,.jpeg,.png"
                className="hidden"
                onChange={handleFileChange}
              />
              {uploading && (
                <p className="text-sm text-muted-foreground mt-3">上传中...</p>
              )}
              <p className="text-xs text-muted-foreground mt-3">
                上传后将自动保存到素材库
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-5 py-4 border-t border-border">
          <Button variant="ghost" size="sm" onClick={onClose}>
            取消
          </Button>
        </div>
      </div>
    </div>
  )
}
