import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAssetPoolStore } from '../stores/assetPoolStore'
import { usePageCopilot } from '../hooks/usePageCopilot'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { FolderOpen, Plus, Trash2, Image, FileText, Video } from 'lucide-react'

const typeIcons: Record<string, React.ElementType> = {
  image: Image,
  video: Video,
  document: FileText,
}

export function AssetPoolPage() {
  const navigate = useNavigate()
  const { assets, isLoading, error, fetchAssets, createAsset, deleteAsset } = useAssetPoolStore()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [type, setType] = useState('image')
  const [tags, setTags] = useState('')

  useEffect(() => {
    fetchAssets()
  }, [fetchAssets])

  usePageCopilot(
    [
      {
        id: 'asset-upload',
        type: 'decision',
        title: '📤 上传素材',
        description: '添加新的图片、视频或文档素材',
        priority: 1,
        actions: [{ id: 'upload_asset', label: '上传', variant: 'primary' }],
      },
      {
        id: 'asset-auto-tag',
        type: 'decision',
        title: '🏷️ AI 批量打标签',
        description: '为未打标签的素材自动生成标签',
        priority: 2,
        actions: [{ id: 'auto_tag_assets', label: '开始打标签', variant: 'primary' }],
      },
      {
        id: 'asset-apply-task',
        type: 'suggestion',
        title: '🚀 应用到任务',
        description: '前往内容生产创建新任务',
        priority: 3,
        actions: [{ id: 'apply_to_task', label: '去创建任务', variant: 'secondary' }],
      },
    ],
    (_cardId, actionId) => {
      if (actionId === 'upload_asset') {
        setShowCreate(true)
      } else if (actionId === 'auto_tag_assets') {
        // TODO: 接入 AI 批量打标签能力
        alert('AI 批量打标签能力即将上线')
      } else if (actionId === 'apply_to_task') {
        navigate('/generate/create')
      }
    }
  )

  const handleCreate = async () => {
    if (!name.trim() || !url.trim()) return
    const success = await createAsset({
      name,
      url,
      type,
      tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
    })
    if (success) {
      setShowCreate(false)
      setName('')
      setUrl('')
      setTags('')
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="素材库"
        subtitle="品牌素材、知识库与内容资产统一管理"
        action={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4" />
            添加素材
          </Button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {showCreate && (
        <Card>
          <CardHeader><h3 className="text-base font-semibold">添加素材</h3></CardHeader>
          <CardContent className="space-y-3">
            <input
              type="text" placeholder="素材名称" value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            />
            <input
              type="text" placeholder="URL 链接" value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            />
            <div className="flex gap-3">
              <select
                value={type} onChange={(e) => setType(e.target.value)}
                className="h-10 px-3 rounded-lg border border-border bg-background text-sm"
              >
                <option value="image">图片</option>
                <option value="video">视频</option>
                <option value="document">文档</option>
              </select>
              <input
                type="text" placeholder="标签（逗号分隔）" value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="flex-1 h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
              <Button onClick={handleCreate}>添加</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="min-w-0 overflow-hidden">
        <CardHeader className="flex items-center gap-2">
          <FolderOpen className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">素材列表</h2>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && assets.length === 0 && (
            <EmptyState icon={FolderOpen} title="暂无素材" description="添加你的第一个素材资源" />
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {assets.map((asset) => {
              const Icon = typeIcons[asset.type] || FileText
              return (
                <div key={asset.id} className="p-4 rounded-lg border border-border hover:border-primary/30 transition-all">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Icon className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">{asset.name}</p>
                        <p className="text-xs text-muted-foreground truncate max-w-[200px]">{asset.url}</p>
                      </div>
                    </div>
                    <button onClick={() => deleteAsset(asset.id)} className="p-1.5 hover:bg-destructive/10 rounded">
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </button>
                  </div>
                  <div className="flex gap-1 mt-2">
                    <Badge variant="default">{asset.type}</Badge>
                    {asset.tags?.map((tag) => (
                      <Badge key={tag} variant="default">{tag}</Badge>
                    ))}
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
