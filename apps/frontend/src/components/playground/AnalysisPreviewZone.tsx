import { ViralScoreRing } from './ViralScoreRing'
import { EmotionCurveChart } from './EmotionCurveChart'
import type { AnalysisReport } from './types'

const DIMENSION_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  structure: { bg: 'bg-blue-100', text: 'text-blue-700', label: '结构' },
  function: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: '功能' },
  emotion: { bg: 'bg-rose-100', text: 'text-rose-700', label: '情感' },
  industry: { bg: 'bg-amber-100', text: 'text-amber-700', label: '行业' },
  effect: { bg: 'bg-violet-100', text: 'text-violet-700', label: '效果' },
}

interface AnalysisPreviewZoneProps {
  report: AnalysisReport | null
  isLoading?: boolean
}

function KeywordHighlighter({ text, matches }: { text: string; matches: AnalysisReport['keyword_matches'] }) {
  if (!matches) return <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">{text}</p>

  // Build a list of all matches with positions
  const allMatches: Array<{ start: number; end: number; keyword: string; dimension: string }> = []

  Object.entries(matches).forEach(([dimension, list]) => {
    list.forEach((m) => {
      const idx = text.indexOf(m.keyword)
      if (idx >= 0) {
        allMatches.push({ start: idx, end: idx + m.keyword.length, keyword: m.keyword, dimension })
      }
    })
  })

  // Sort by position and remove overlaps (keep longer matches)
  allMatches.sort((a, b) => a.start - b.start || b.end - a.end)
  const filtered: typeof allMatches = []
  for (const m of allMatches) {
    const last = filtered[filtered.length - 1]
    if (!last || m.start >= last.end) {
      filtered.push(m)
    }
  }

  // Render with highlights
  const segments: Array<{ text: string; dimension?: string }> = []
  let lastEnd = 0
  for (const m of filtered) {
    if (m.start > lastEnd) {
      segments.push({ text: text.slice(lastEnd, m.start) })
    }
    segments.push({ text: m.keyword, dimension: m.dimension })
    lastEnd = m.end
  }
  if (lastEnd < text.length) {
    segments.push({ text: text.slice(lastEnd) })
  }

  return (
    <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
      {segments.map((seg, i) => {
        if (seg.dimension && DIMENSION_COLORS[seg.dimension]) {
          const style = DIMENSION_COLORS[seg.dimension]
          return (
            <span key={i} className={`${style.bg} ${style.text} rounded px-0.5`}>
              {seg.text}
            </span>
          )
        }
        return <span key={i}>{seg.text}</span>
      })}
    </p>
  )
}

export function AnalysisPreviewZone({ report, isLoading }: AnalysisPreviewZoneProps) {
  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-64 bg-card border border-border rounded-xl" />
        <div className="h-48 bg-card border border-border rounded-xl" />
      </div>
    )
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <svg className="w-12 h-12 text-muted-foreground/30 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
        <p className="text-sm text-muted-foreground">暂无分析数据</p>
        <p className="text-xs text-muted-foreground/60 mt-1">在 Copilot 面板中点击「开始分析」</p>
      </div>
    )
  }

  const { keyword_matches, viral_score, scoring_breakdown, emotion_curve, success_factors, structure_type, structure_confidence } = report

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Original text with highlights */}
        <div className="bg-card rounded-xl border border-border p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">原文 · 关键词高亮</h3>
            <div className="flex gap-1.5 text-[10px]">
              {Object.entries(DIMENSION_COLORS).map(([dim, style]) => (
                <span key={dim} className={`px-1.5 py-0.5 rounded ${style.bg} ${style.text}`}>{style.label}</span>
              ))}
            </div>
          </div>
          <div className="max-h-[420px] overflow-y-auto pr-2 space-y-2">
            <KeywordHighlighter text={report.title_analysis ? `标题: ${report.title_analysis.pattern}` : ''} matches={keyword_matches} />
            <div className="border-t border-border my-2" />
            <KeywordHighlighter text={`正文:\n${report.title_analysis ? '' : ''}`} matches={keyword_matches} />
          </div>
        </div>

        {/* Right: Analysis Summary */}
        <div className="space-y-4">
          {/* Structure Type Badge */}
          <div className="bg-card rounded-xl border border-border p-4 card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">识别结构类型</p>
                <p className="text-lg font-bold text-primary">{structure_type}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground mb-1">置信度</p>
                <p className="text-sm font-semibold">{Math.round(structure_confidence * 100)}%</p>
              </div>
            </div>
          </div>

          {/* Viral Score Ring */}
          <div className="bg-card rounded-xl border border-border p-4 card-hover">
            <div className="flex items-center gap-4">
              <ViralScoreRing value={viral_score} size={72} stroke={6} />
              <div className="flex-1">
                <p className="text-sm font-semibold mb-2">爆款评分</p>
                <div className="space-y-1.5">
                  <ScoreBar label="结构完整性" value={scoring_breakdown.completeness} max={40} />
                  <ScoreBar label="关键词丰富" value={scoring_breakdown.keyword_richness} max={35} />
                  <ScoreBar label="情绪曲线" value={scoring_breakdown.emotion_curve} max={25} />
                </div>
              </div>
            </div>
          </div>

          {/* Emotion Curve */}
          <div className="bg-card rounded-xl border border-border p-4 card-hover">
            <p className="text-xs font-medium text-muted-foreground mb-2">情绪曲线</p>
            <EmotionCurveChart data={emotion_curve} />
          </div>

          {/* Success Factors */}
          <div className="bg-card rounded-xl border border-border p-4 card-hover">
            <p className="text-xs font-medium text-muted-foreground mb-2">Top 3 成功因子</p>
            <div className="space-y-2">
              {success_factors.slice(0, 3).map((factor, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <p className="text-xs text-foreground">{factor}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ScoreBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.round((value / max) * 100)
  const color = pct >= 80 ? 'bg-success' : pct >= 50 ? 'bg-warning' : 'bg-destructive'
  return (
    <div className="flex items-center gap-2 text-[10px]">
      <span className="w-16 text-muted-foreground truncate">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%`, transition: 'width 0.6s ease-out' }} />
      </div>
      <span className="w-6 text-right">{value}</span>
    </div>
  )
}
