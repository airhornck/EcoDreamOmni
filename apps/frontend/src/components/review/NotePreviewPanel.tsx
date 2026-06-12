import { useMemo, useState } from 'react'
import { Badge } from '../ui/Badge'
import { ImageOff, MapPin, Eye, AtSign, Hash } from 'lucide-react'
import type { GeneratedContent } from '../../stores/reviewPublishStore'

const platformLabels: Record<string, string> = {
  xhs: '小红书',
  douyin: '抖音',
  wechat_channels: '视频号',
}

interface NotePreviewPanelProps {
  content: GeneratedContent | null
  location?: string
  mentions?: string[]
  visibility?: 'public' | 'private'
  declaration?: 'none' | 'cooperation' | 'experience'
}

export function NotePreviewPanel({
  content,
  location,
  mentions = [],
  visibility = 'public',
  declaration = 'none',
}: NotePreviewPanelProps) {
  const platform = content?.platform || 'xhs'
  const isXhs = platform === 'xhs'

  const coverUrl = content?.cover_image_url
  const title = content?.title || '暂无标题'
  const body = content?.body || ''
  const tags = content?.tags || []

  const [activeCoverIndex, setActiveCoverIndex] = useState(0)

  // 从 content.images 获取多图（fallback 到单封面）
  const images = content?.images?.length ? content.images : coverUrl ? [coverUrl] : []

  const bodyPreview = useMemo(() => {
    const lines = body.split('\n').filter((l) => l.trim())
    return lines.slice(0, 10).join('\n')
  }, [body])

  if (!isXhs) {
    // 通用预览（抖音/视频号）
    return (
      <div className="bg-white dark:bg-background rounded-xl border border-border overflow-hidden shadow-sm">
        <div className="aspect-[9/16] bg-secondary relative max-h-[400px]">
          {coverUrl ? (
            <img src={coverUrl} alt="cover" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
              <ImageOff className="w-8 h-8" />
            </div>
          )}
          <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/60 to-transparent">
            <h3 className="text-sm font-semibold text-white line-clamp-2">{title}</h3>
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

  // 小红书笔记预览
  return (
    <div className="bg-white dark:bg-background rounded-xl border border-border overflow-hidden shadow-sm">
      {/* Cover / Image Gallery */}
      <div className="relative bg-secondary">
        {images.length > 0 ? (
          <>
            <div className="aspect-[3/4] relative">
              <img
                src={images[activeCoverIndex]}
                alt="cover"
                className="w-full h-full object-cover"
              />
              {images.length > 1 && (
                <>
                  {/* Dots indicator */}
                  <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
                    {images.map((_img: string, i: number) => (
                      <button
                        key={i}
                        onClick={() => setActiveCoverIndex(i)}
                        className={`w-1.5 h-1.5 rounded-full transition-colors ${
                          i === activeCoverIndex ? 'bg-white' : 'bg-white/50'
                        }`}
                      />
                    ))}
                  </div>
                  {/* Page counter */}
                  <div className="absolute top-2 right-2 bg-black/40 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                    {activeCoverIndex + 1}/{images.length}
                  </div>
                </>
              )}
            </div>
          </>
        ) : (
          <div className="aspect-[3/4] flex items-center justify-center text-muted-foreground">
            <ImageOff className="w-8 h-8" />
          </div>
        )}
        <div className="absolute top-2 left-2">
          <Badge variant="default" className="bg-black/50 text-white border-0 text-[10px]">
            {platformLabels[platform] || platform}
          </Badge>
        </div>
      </div>

      {/* Body */}
      <div className="p-3 space-y-2.5">
        <h3 className="text-sm font-semibold leading-snug">{title}</h3>

        <div className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">
          {bodyPreview}
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {tags.map((t) => (
              <span key={t} className="flex items-center gap-0.5 text-xs text-primary">
                <Hash className="w-3 h-3" />
                {t}
              </span>
            ))}
          </div>
        )}

        {/* Mentions */}
        {mentions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {mentions.map((m) => (
              <span key={m} className="flex items-center gap-0.5 text-xs text-primary">
                <AtSign className="w-3 h-3" />
                {m}
              </span>
            ))}
          </div>
        )}

        {/* Location */}
        {location && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="w-3 h-3" />
            {location}
          </div>
        )}

        {/* Meta footer */}
        <div className="flex items-center justify-between pt-2 border-t border-border/50 text-[10px] text-muted-foreground">
          <div className="flex items-center gap-2">
            {visibility === 'private' && (
              <span className="flex items-center gap-0.5">
                <Eye className="w-3 h-3" />
                仅自己可见
              </span>
            )}
            {declaration !== 'none' && (
              <Badge variant="info" className="text-[10px] px-1 py-0">
                {declaration === 'cooperation' ? '合作' : '体验'}
              </Badge>
            )}
          </div>
          <span>{new Date().toLocaleDateString('zh-CN')}</span>
        </div>

        {/* Mock engagement */}
        <div className="flex items-center justify-between pt-1">
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
