import type { AnalysisReport } from './types'

interface ReportDetailZoneProps {
  report: AnalysisReport | null
}

export function ReportDetailZone({ report }: ReportDetailZoneProps) {
  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground">
        <p className="text-sm">暂无报告数据</p>
        <p className="text-xs mt-1">请先完成分析</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      {/* JSON Preview */}
      <div className="bg-card rounded-xl border border-border p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">结构化分析报告（JSON）</h3>
        </div>
        <pre className="bg-secondary/30 rounded-lg p-3 font-mono text-[11px] leading-relaxed overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(report, null, 2)}
        </pre>
      </div>

      {/* Section Analysis Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <AnalysisCard icon="T" iconColor="bg-blue-100 text-blue-600" title="标题分析">
          <p className="text-[11px] text-muted-foreground">模式：{report.title_analysis.pattern}</p>
          <p className="text-[11px] text-muted-foreground">含数字：{report.title_analysis.contains_number ? '✅' : '❌'} 长度：{report.title_analysis.length}字</p>
        </AnalysisCard>
        <AnalysisCard icon="H" iconColor="bg-emerald-100 text-emerald-600" title="开头钩子">
          <p className="text-[11px] text-muted-foreground">类型：{report.hook_analysis.hook_type}</p>
          <p className="text-[11px] text-muted-foreground">效果分：{report.hook_analysis.effectiveness}</p>
        </AnalysisCard>
        <AnalysisCard icon="B" iconColor="bg-amber-100 text-amber-600" title="正文结构">
          <p className="text-[11px] text-muted-foreground">段落数：{report.body_analysis.sections} 平均长度：{report.body_analysis.avg_section_length}字</p>
          <p className="text-[11px] text-muted-foreground">含故事：{report.body_analysis.has_story ? '✅' : '❌'} 含数据：{report.body_analysis.has_data ? '✅' : '❌'}</p>
        </AnalysisCard>
        <AnalysisCard icon="C" iconColor="bg-rose-100 text-rose-600" title="结尾 CTA">
          <p className="text-[11px] text-muted-foreground">类型：{report.cta_analysis.cta_type}</p>
          <p className="text-[11px] text-muted-foreground">效果分：{report.cta_analysis.effectiveness}</p>
        </AnalysisCard>
      </div>
    </div>
  )
}

function AnalysisCard({ icon, iconColor, title, children }: {
  icon: string
  iconColor: string
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-card rounded-xl border border-border p-3 card-hover">
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold ${iconColor}`}>{icon}</span>
        <span className="text-xs font-medium">{title}</span>
      </div>
      {children}
    </div>
  )
}
