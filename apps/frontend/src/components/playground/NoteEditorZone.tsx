import { useState, useCallback } from 'react'
import { usePlaygroundStore } from '../../stores/playgroundStore'
import type { NoteInput } from './types'

const CATEGORIES = ['宠物健康', '新手养猫', '省钱攻略', '宠物食品', '宠物用品', '养宠日常']

export function NoteEditorZone() {
  const setNoteInput = usePlaygroundStore((s) => s.setNoteInput)

  const [title, setTitle] = useState('猫咪驱虫避坑指南，这3个误区90%的人都不知道')
  const [content, setContent] = useState(
    '作为一个养了3年猫的铲屎官，今天必须跟大家聊聊驱虫这件事！\n\n😱 误区一：以为家养猫不用驱虫\n很多人觉得猫咪不出门就不用驱虫，其实这是大错特错！寄生虫卵可能通过鞋底、快递箱、甚至是窗户飘进来...\n\n✅ 正确做法：即使家养，也要每3个月做一次体内外驱虫。\n\n💡 误区二：驱虫药越贵越好\n市面上驱虫药从几十到几百都有，但真的不是越贵越好！关键要看成分和驱虫谱...\n\n✅ 正确做法：选择广谱驱虫药，覆盖跳蚤、蜱虫、蛔虫、绦虫即可。\n\n🎯 误区三：驱虫后不用观察\n很多铲屎官给猫吃了驱虫药就完事了，其实驱虫后的48小时非常关键！\n\n✅ 正确做法：驱虫后观察2天，有异常及时就医。\n\n好了，今天就分享到这里！你们家毛孩子驱虫遇到过什么问题？欢迎在评论区交流～ 👇',
  )
  const [category, setCategory] = useState('宠物健康')
  const [tags, setTags] = useState<string[]>(['猫咪驱虫', '新手养猫', '省钱攻略', '宠物健康'])
  const [tagInput, setTagInput] = useState('')
  const [likes, setLikes] = useState('12500')
  const [collects, setCollects] = useState('3400')
  const [comments, setComments] = useState('890')

  const updateStore = useCallback(() => {
    const input: NoteInput = {
      title,
      content,
      category,
      tags,
      metrics: {
        likes: Number(likes) || 0,
        collects: Number(collects) || 0,
        comments: Number(comments) || 0,
      },
    }
    setNoteInput(input)
  }, [title, content, category, tags, likes, collects, comments, setNoteInput])

  const handleAddTag = () => {
    const t = tagInput.trim()
    if (t && !tags.includes(t)) {
      setTags((prev) => [...prev, t])
      setTagInput('')
    }
  }

  const handleRemoveTag = (t: string) => {
    setTags((prev) => prev.filter((x) => x !== t))
  }

  // Debounced store update
  const handleChange = (updater: () => void) => {
    updater()
    // Small delay to batch updates
    window.setTimeout(updateStore, 300)
  }

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      {/* Title */}
      <div>
        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">标题</label>
        <input
          type="text"
          value={title}
          onChange={(e) => handleChange(() => setTitle(e.target.value))}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          placeholder="输入笔记标题..."
        />
      </div>

      {/* Content */}
      <div>
        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">正文</label>
        <textarea
          value={content}
          onChange={(e) => handleChange(() => setContent(e.target.value))}
          rows={12}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all leading-relaxed"
          placeholder="粘贴笔记正文..."
        />
      </div>

      {/* Cover Image Drop Zone */}
      <div>
        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">封面图</label>
        <div className="w-full h-40 rounded-lg border-2 border-dashed border-border bg-secondary/30 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-primary/40 hover:bg-primary/5 transition-all group">
          <svg className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span className="text-xs text-muted-foreground">拖拽图片到此处，或点击粘贴链接</span>
          <span className="text-[10px] text-muted-foreground/60">支持 JPG, PNG, WebP（最大 5MB）</span>
        </div>
      </div>

      {/* Category & Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">赛道标签</label>
          <select
            value={category}
            onChange={(e) => handleChange(() => setCategory(e.target.value))}
            className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1.5 block">互动数据（可选）</label>
          <div className="flex gap-2">
            <input type="number" placeholder="点赞" value={likes} onChange={(e) => handleChange(() => setLikes(e.target.value))} className="flex-1 h-9 px-2 rounded-lg border border-border bg-background text-sm text-center" />
            <input type="number" placeholder="收藏" value={collects} onChange={(e) => handleChange(() => setCollects(e.target.value))} className="flex-1 h-9 px-2 rounded-lg border border-border bg-background text-sm text-center" />
            <input type="number" placeholder="评论" value={comments} onChange={(e) => handleChange(() => setComments(e.target.value))} className="flex-1 h-9 px-2 rounded-lg border border-border bg-background text-sm text-center" />
          </div>
        </div>
      </div>

      {/* Tags */}
      <div>
        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">话题标签</label>
        <div className="flex flex-wrap gap-2">
          {tags.map((t) => (
            <span key={t} className="px-2 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium flex items-center gap-1">
              #{t}
              <button onClick={() => handleChange(() => handleRemoveTag(t))} className="hover:text-primary/70">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </span>
          ))}
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddTag(); } }}
            placeholder="+ 添加标签"
            className="h-7 px-2 rounded-full border border-border bg-background text-xs w-24 focus:outline-none focus:border-primary"
          />
        </div>
      </div>
    </div>
  )
}
