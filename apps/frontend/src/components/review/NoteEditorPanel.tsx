import { useState, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { MarkdownBody } from './MarkdownBody'
import { CoverPickerModal } from './CoverPickerModal'
import {
  ImagePlus,
  X,
  MapPin,
  AtSign,
  Hash,
  Eye,
  EyeOff,
  FileText,
  AlertCircle,
} from 'lucide-react'
import type { GeneratedContent } from '../../stores/reviewPublishStore'

/* ── types ── */

export interface NoteMeta {
  location?: string
  mentions?: string[]
  visibility?: 'public' | 'private'
  declaration?: 'none' | 'cooperation' | 'experience'
}

interface FieldConstraint {
  name: string
  label: string
  type: string
  required?: boolean
  min?: unknown
  max?: unknown
  min_chars?: number
  max_chars?: number
  max_count?: number
  default?: unknown
  supported?: string[]
  description?: string
}

interface ContentFormat {
  format_name: string
  fields: FieldConstraint[]
}

interface PlatformSchema {
  platform_id: string
  display_name: string
  content_formats: ContentFormat[]
}

interface NoteEditorPanelProps {
  content: GeneratedContent | null
  meta?: NoteMeta
  editable?: boolean
  onChange: (patch: Partial<GeneratedContent>) => void
  onMetaChange?: (meta: Partial<NoteMeta>) => void
  onCoverChange?: () => void
  maxImages?: number
  platformSchema?: PlatformSchema | null
  contentFormat?: string
}

/* ── helpers ── */

function parseTags(tagStr: string): string[] {
  return tagStr
    .split(/[,，#\s]+/)
    .map((t) => t.trim())
    .filter(Boolean)
}

/* ── component ── */

export function NoteEditorPanel({
  content,
  meta = {},
  editable = true,
  onChange,
  onMetaChange,
  maxImages: propMaxImages,
  platformSchema,
  contentFormat,
}: NoteEditorPanelProps) {
  const platform = content?.platform || 'xhs'

  // 根据 contentFormat 匹配 PlatformSchema 中的字段约束
  const formatFields = useMemo(() => {
    if (!platformSchema || !contentFormat) return null
    const fmt = platformSchema.content_formats.find((cf) => cf.format_name === contentFormat)
    if (!fmt) return null
    const map: Record<string, FieldConstraint> = {}
    fmt.fields.forEach((f) => { map[f.name] = f })
    return map
  }, [platformSchema, contentFormat])

  // 动态计算约束值（优先 PlatformSchema，次 props，最后兜底）
  const maxImages = propMaxImages ?? (formatFields?.pic_num?.max as number) ?? 18
  const titleMaxChars = (formatFields?.title?.max_chars as number) ?? (platform === 'xhs' ? 20 : platform === 'douyin' ? 55 : 30)
  const titleMinChars = (formatFields?.title?.min_chars as number) ?? 1
  const bodyMaxChars = (formatFields?.content?.max_chars as number) ?? undefined
  const tagMaxCount = (formatFields?.topic?.max_count as number) ?? 10
  const tagMaxChars = (formatFields?.topic?.max_chars as number) ?? undefined

  // 格式提示信息
  const formatHint = useMemo(() => {
    if (!contentFormat) return null
    const hints: string[] = []
    const picNum = formatFields?.pic_num
    if (picNum) hints.push(`图片 ${picNum.min ?? 1}-${picNum.max ?? 18} 张`)
    const title = formatFields?.title
    if (title?.max_chars) hints.push(`标题 ≤${title.max_chars} 字`)
    const content = formatFields?.content
    if (content?.max_chars) hints.push(`正文 ≤${content.max_chars} 字`)
    const duration = formatFields?.duration
    if (duration) hints.push(`时长 ${duration.min ?? ''}-${duration.max ?? ''}`)
    return hints.length > 0 ? hints.join(' · ') : null
  }, [formatFields, contentFormat])

  // 封面图片数组（复用 cover_image_url + 未来扩展 images）
  const images = useMemo(() => {
    const list: string[] = []
    if (content?.cover_image_url) list.push(content.cover_image_url)
    if (content?.images?.length) {
      content.images.forEach((img) => {
        if (!list.includes(img)) list.push(img)
      })
    }
    return list
  }, [content])

  // 封面选择弹窗
  const [coverPickerOpen, setCoverPickerOpen] = useState(false)
  const [pickerMode, setPickerMode] = useState<'add' | 'replace'>('add')
  const [replaceIndex, setReplaceIndex] = useState(0)

  // 话题编辑状态
  const [tagDraft, setTagDraft] = useState('')
  const [tagInputFocus, setTagInputFocus] = useState(false)

  const tags = content?.tags || []

  const openAddCover = () => {
    setPickerMode('add')
    setCoverPickerOpen(true)
  }

  const openReplaceCover = (index: number) => {
    setPickerMode('replace')
    setReplaceIndex(index)
    setCoverPickerOpen(true)
  }

  const handleCoverSelect = useCallback(
    (url: string) => {
      if (pickerMode === 'replace') {
        const nextImages = [...images]
        nextImages[replaceIndex] = url
        onChange({ cover_image_url: nextImages[0], images: nextImages })
      } else {
        const nextImages = [...images, url]
        onChange({ cover_image_url: nextImages[0], images: nextImages })
      }
      setCoverPickerOpen(false)
    },
    [images, pickerMode, replaceIndex, onChange]
  )

  const handleRemoveImage = (index: number) => {
    const nextImages = images.filter((_, i) => i !== index)
    onChange({ cover_image_url: nextImages[0] || '', images: nextImages })
  }

  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      const newTags = parseTags(tagDraft)
      if (newTags.length > 0) {
        const merged = Array.from(new Set([...tags, ...newTags]))
        onChange({ tags: merged })
        setTagDraft('')
      }
    }
  }

  const handleTagBlur = () => {
    setTagInputFocus(false)
    const newTags = parseTags(tagDraft)
    if (newTags.length > 0) {
      const merged = Array.from(new Set([...tags, ...newTags]))
      onChange({ tags: merged })
      setTagDraft('')
    }
  }

  const removeTag = (tag: string) => {
    onChange({ tags: tags.filter((t) => t !== tag) })
  }

  const title = content?.title || ''
  const titleChars = title.length
  const titleWarning = titleChars > titleMaxChars

  return (
    <div className="space-y-4">
      {/* ── Cover Gallery ── */}
      <Card>
        <CardHeader className="flex items-center justify-between py-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <ImagePlus className="w-4 h-4 text-primary" />
            封面
            <Badge variant="default" className="text-[10px]">
              {images.length}/{maxImages}
            </Badge>
            {formatHint && (
              <span className="text-[10px] text-muted-foreground ml-1">({formatHint})</span>
            )}
          </div>
          {images.length >= maxImages && (
            <span className="text-[10px] text-destructive flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              已达上限
            </span>
          )}
        </CardHeader>
        <CardContent className="pt-0 space-y-3">
          {/* Image grid */}
          {images.length > 0 && (
            <div className="grid grid-cols-4 gap-2">
              {images.map((img, i) => (
                <div key={`${img}-${i}`} className="relative group aspect-square rounded-lg overflow-hidden border border-border">
                  <img src={img} alt={`cover-${i}`} className="w-full h-full object-cover" />
                  {editable && (
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center gap-1">
                      <button
                        onClick={() => openReplaceCover(i)}
                        className="opacity-0 group-hover:opacity-100 p-1 bg-white/90 rounded text-xs text-foreground hover:bg-white transition-opacity"
                      >
                        更换
                      </button>
                      <button
                        onClick={() => handleRemoveImage(i)}
                        className="opacity-0 group-hover:opacity-100 p-1 bg-white/90 rounded text-xs text-destructive hover:bg-white transition-opacity"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                  {i === 0 && (
                    <div className="absolute top-1 left-1 bg-primary text-primary-foreground text-[10px] px-1 py-0.5 rounded">
                      首图
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Add button */}
          {editable && images.length < maxImages && (
            <button
              onClick={openAddCover}
              className="w-full h-20 border-2 border-dashed border-border rounded-lg flex flex-col items-center justify-center text-muted-foreground hover:border-primary hover:text-primary transition-colors"
            >
              <ImagePlus className="w-5 h-5 mb-1" />
              <span className="text-xs">添加封面</span>
            </button>
          )}

          {/* Ratio hint — 视频格式不显示图片比例提示 */}
          {(!contentFormat || !contentFormat.includes('视频')) && (
            <div className="text-[10px] text-muted-foreground">
              推荐比例：
              <span className="text-foreground">3:4</span>（竖图）/
              <span className="text-foreground">1:1</span>（方图）/
              <span className="text-foreground">4:3</span>（横图）
            </div>
          )}

          <CoverPickerModal
            open={coverPickerOpen}
            onClose={() => setCoverPickerOpen(false)}
            onSelect={handleCoverSelect}
          />
        </CardContent>
      </Card>

      {/* ── Title ── */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FileText className="w-4 h-4 text-primary" />
            标题
          </div>
        </CardHeader>
        <CardContent className="pt-0 space-y-2">
          <input
            type="text"
            value={title}
            readOnly={!editable}
            placeholder="输入标题..."
            onChange={(e) => {
              if (!editable) return
              onChange({ title: e.target.value })
            }}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <div className="flex items-center justify-between">
            <span className={`text-[10px] ${titleWarning ? 'text-destructive' : 'text-muted-foreground'}`}>
              {titleChars}/{titleMaxChars} 字
              {titleWarning && '（超出限制）'}
              {titleChars < titleMinChars && titleChars > 0 && '（字数不足）'}
            </span>
            {platformSchema && contentFormat ? (
              <span className="text-[10px] text-muted-foreground">{contentFormat} 标题限 {titleMaxChars} 字</span>
            ) : platform === 'xhs' ? (
              <span className="text-[10px] text-muted-foreground">小红书标题限 {titleMaxChars} 字</span>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {/* ── Body (Rich Text) ── */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FileText className="w-4 h-4 text-primary" />
            正文
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <MarkdownBody
            body={content?.body || ''}
            editable={editable}
            onChange={(body) => onChange({ body })}
          />
          {bodyMaxChars !== undefined && (
            <div className="mt-1.5 text-[10px] text-muted-foreground text-right">
              {(content?.body || '').length}/{bodyMaxChars} 字
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Meta Fields ── */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Hash className="w-4 h-4 text-primary" />
            其他信息
          </div>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          {/* Tags */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground flex items-center gap-1">
              <Hash className="w-3 h-3" />
              话题标签
            </label>
            <div className="flex flex-wrap gap-1.5 min-h-[2rem] p-1.5 rounded-lg border border-border bg-background">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-0.5 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded"
                >
                  #{tag}
                  {editable && (
                    <button onClick={() => removeTag(tag)} className="hover:text-destructive">
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </span>
              ))}
              {editable && (
                <input
                  type="text"
                  value={tagDraft}
                  onChange={(e) => setTagDraft(e.target.value)}
                  onKeyDown={handleTagKeyDown}
                  onFocus={() => setTagInputFocus(true)}
                  onBlur={handleTagBlur}
                  placeholder={tagInputFocus ? '输入后按回车' : tags.length === 0 ? '添加话题...' : ''}
                  className="flex-1 min-w-[4rem] text-sm bg-transparent outline-none placeholder:text-muted-foreground/50"
                />
              )}
            </div>
            <p className="text-[10px] text-muted-foreground">最多 {tagMaxCount} 个话题{tagMaxChars ? `，每话题 ≤${tagMaxChars} 字` : ''}</p>
          </div>

          {/* Mentions */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground flex items-center gap-1">
              <AtSign className="w-3 h-3" />
              @用户
            </label>
            <input
              type="text"
              value={(meta.mentions || []).join(' ')}
              readOnly={!editable}
              placeholder="输入用户名，空格分隔"
              onChange={(e) => {
                if (!editable || !onMetaChange) return
                const mentions = e.target.value.split(/\s+/).filter(Boolean)
                onMetaChange({ mentions })
              }}
              className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Location */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              标记地点
            </label>
            <input
              type="text"
              value={meta.location || ''}
              readOnly={!editable}
              placeholder="输入地点..."
              onChange={(e) => {
                if (!editable || !onMetaChange) return
                onMetaChange({ location: e.target.value })
              }}
              className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Visibility */}
          <div className="flex items-center justify-between">
            <label className="text-xs text-muted-foreground flex items-center gap-1">
              {meta.visibility === 'private' ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              公开可见
            </label>
            {editable ? (
              <button
                onClick={() => onMetaChange?.({ visibility: meta.visibility === 'private' ? 'public' : 'private' })}
                className={`relative w-9 h-5 rounded-full transition-colors ${
                  meta.visibility === 'private' ? 'bg-muted' : 'bg-primary'
                }`}
              >
                <span
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${
                    meta.visibility === 'private' ? 'left-0.5' : 'left-[1.125rem]'
                  }`}
                />
              </button>
            ) : (
              <span className="text-xs text-muted-foreground">
                {meta.visibility === 'private' ? '仅自己可见' : '公开'}
              </span>
            )}
          </div>

          {/* Declaration */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">声明</label>
            <div className="flex gap-2">
              {([
                { value: 'none', label: '无需声明' },
                { value: 'cooperation', label: '合作' },
                { value: 'experience', label: '体验' },
              ] as const).map((opt) => (
                <button
                  key={opt.value}
                  disabled={!editable}
                  onClick={() => onMetaChange?.({ declaration: opt.value })}
                  className={`flex-1 h-8 rounded-lg text-xs font-medium transition-colors ${
                    meta.declaration === opt.value
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  } ${!editable ? 'opacity-60 cursor-default' : ''}`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
