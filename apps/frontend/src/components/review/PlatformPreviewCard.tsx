import { useMemo, useState } from 'react'
import { Badge } from '../ui/Badge'
import { ImageOff, Pencil, Camera } from 'lucide-react'
import type { GeneratedContent } from '../../stores/reviewPublishStore'

const platformLabels: Record<string, string> = {
  xhs: '小红书',
  douyin: '抖音',
  wechat_channels: '视频号',
}

const platformTitleRules: Record<string, { maxLength: number; hint: string }> = {
  xhs: { maxLength: 20, hint: '小红书标题限 20 字' },
  douyin: { maxLength: 55, hint: '抖音标题限 55 字' },
  wechat_channels: { maxLength: 30, hint: '视频号标题限 30 字' },
}

interface PlatformPreviewCardProps {
  content: GeneratedContent | null
  editable?: boolean
  onChange?: (patch: Partial<GeneratedContent>) => void
  onCoverChange?: () => void
}

export function PlatformPreviewCard({ content, editable = false, onChange, onCoverChange }: PlatformPreviewCardProps) {
  const platform = content?.platform || 'xhs'
  const isXhs = platform === 'xhs'

  const coverUrl = content?.cover_image_url
  const title = content?.title || '暂无标题'
  const body = content?.body || ''
  const tags = content?.tags || []

  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState(title)

  const bodyPreview = useMemo(() => {
    const lines = body.split('\n').filter((l) => l.trim())
    return lines.slice(0, 6).join('\n')
  }, [body])

  const commitTitle = () => {
    if (titleDraft !== title && onChange) {
      onChange({ title: titleDraft })
    }
    setEditingTitle(false)
  }

  if (isXhs) {
    return (
      <div className="bg-white dark:bg-background rounded-xl border border-border overflow-hidden shadow-sm">
        {/* Cover */}
        <div
          className={`aspect-[4/3] bg-secondary relative group ${editable ? 'cursor-pointer' : ''}`}
          onClick={() => editable && onCoverChange?.()}
        >
          {coverUrl ? (
            <img src={coverUrl} alt="cover" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
              <ImageOff className="w-8 h-8" />
            </div>
          )}
          {editable && (
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
              <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1.5 text-white text-sm font-medium">
                <Camera className="w-4 h-4" />
                更换封面
              </div>
            </div>
          )}
          <div className="absolute top-2 right-2">
            <Badge variant="default" className="bg-black/50 text-white border-0">
              {platformLabels[platform] || platform}
            </Badge>
          </div>
        </div>

        {/* Body */}
        <div className="p-3 space-y-2">
          {editingTitle ? (
            <div className="w-full">
              <input
                autoFocus
                value={titleDraft}
                maxLength={platformTitleRules[platform]?.maxLength}
                onChange={(e) => setTitleDraft(e.target.value)}
                onBlur={commitTitle}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') commitTitle()
                  if (e.key === 'Escape') {
                    setTitleDraft(title)
                    setEditingTitle(false)
                  }
                }}
                className="w-full text-sm font-semibold leading-snug bg-transparent border-b border-primary outline-none px-0"
              />
              <p className="text-[10px] text-muted-foreground mt-0.5">
                {platformTitleRules[platform]?.hint}（{titleDraft.length}/{platformTitleRules[platform]?.maxLength}）
              </p>
            </div>
          ) : (
            <h3
              className={`text-sm font-semibold line-clamp-2 leading-snug ${editable ? 'group/title cursor-pointer hover:text-primary' : ''}`}
              onClick={() => editable && setEditingTitle(true)}
              title={editable ? '点击编辑标题' : undefined}
            >
              <span className="flex items-start gap-1">
                {title}
                {editable && (
                  <Pencil className="w-3 h-3 mt-0.5 text-muted-foreground opacity-60 group-hover/title:opacity-100 transition-opacity" />
                )}
              </span>
            </h3>
          )}
          <p className="text-xs text-muted-foreground line-clamp-4 whitespace-pre-wrap leading-relaxed">
            {bodyPreview}
          </p>

          {/* Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {tags.map((t) => (
                <span key={t} className="text-xs text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                  #{t}
                </span>
              ))}
            </div>
          )}

          {/* Footer mock */}
          <div className="flex items-center justify-between pt-2 border-t border-border/50">
            <div className="flex items-center gap-1.5">
              <div className="w-5 h-5 rounded-full bg-secondary" />
              <span className="text-xs text-muted-foreground">萌宠营养师</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>❤️ 0</span>
              <span>⭐ 0</span>
              <span>💬 0</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Douyin / generic
  return (
    <div className="bg-white dark:bg-background rounded-xl border border-border overflow-hidden shadow-sm">
      <div
        className={`aspect-[9/16] bg-secondary relative max-h-[400px] group ${editable ? 'cursor-pointer' : ''}`}
        onClick={() => editable && onCoverChange?.()}
      >
        {coverUrl ? (
          <img src={coverUrl} alt="cover" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
            <ImageOff className="w-8 h-8" />
          </div>
        )}
        {editable && (
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
            <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1.5 text-white text-sm font-medium">
              <Camera className="w-4 h-4" />
              更换封面
            </div>
          </div>
        )}
        <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/60 to-transparent">
          {editingTitle ? (
            <div className="w-full">
              <input
                autoFocus
                value={titleDraft}
                maxLength={platformTitleRules[platform]?.maxLength}
                onChange={(e) => setTitleDraft(e.target.value)}
                onBlur={commitTitle}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') commitTitle()
                  if (e.key === 'Escape') {
                    setTitleDraft(title)
                    setEditingTitle(false)
                  }
                }}
                className="w-full text-sm font-semibold text-white bg-transparent border-b border-white/70 outline-none px-0"
              />
              <p className="text-[10px] text-white/70 mt-0.5">
                {platformTitleRules[platform]?.hint}（{titleDraft.length}/{platformTitleRules[platform]?.maxLength}）
              </p>
            </div>
          ) : (
            <h3
              className="text-sm font-semibold text-white line-clamp-2"
              onClick={() => editable && setEditingTitle(true)}
            >
              {title}
            </h3>
          )}
        </div>
        <div className="absolute top-2 right-2">
          <Badge variant="default" className="bg-black/50 text-white border-0">
            {platformLabels[platform] || platform}
          </Badge>
        </div>
      </div>
      <div className="p-3 space-y-2">
        <p className="text-xs text-muted-foreground line-clamp-3 whitespace-pre-wrap">{bodyPreview}</p>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tags.map((t) => (
              <span key={t} className="text-xs text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                #{t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
