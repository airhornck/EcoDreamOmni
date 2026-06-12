import { useState } from 'react'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { ChevronDown, ChevronRight, FileText } from 'lucide-react'
import type { TopicReport } from '../../stores/reviewPublishStore'

export function TopicReportPanel({ report }: { report: TopicReport | null }) {
  const [open, setOpen] = useState(false)

  if (!report) {
    return (
      <Card className="bg-muted/30">
        <CardHeader className="text-sm font-medium flex items-center gap-2 py-3">
          <FileText className="w-4 h-4 text-muted-foreground" />
          <span className="text-muted-foreground">选题报告（无数据）</span>
        </CardHeader>
      </Card>
    )
  }

  const selected = (report.topics || []).find((t) => t.status === 'adopted') || (report.topics || [])[0]

  return (
    <Card className="bg-muted/30">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">选题报告</span>
          <Badge variant="info" className="text-xs">{report['5a_stage']}</Badge>
          {selected && (
            <span className="text-xs text-muted-foreground">
              选中: {selected.title}
            </span>
          )}
        </div>
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>

      {open && (
        <CardContent className="pt-0 pb-4 space-y-3">
          <div className="text-xs text-muted-foreground">
            人群契合度: <strong className="text-foreground">{report.audience_fit_score}/100</strong>
          </div>

          <div className="space-y-2">
            {report.topics.map((topic) => (
              <div
                key={topic.id}
                className={`flex items-center justify-between p-2.5 rounded-lg text-sm ${
                  topic.status === 'adopted'
                    ? 'bg-primary/10 border border-primary/20'
                    : 'bg-secondary/50'
                }`}
              >
                <div className="flex items-center gap-2">
                  {topic.status === 'adopted' && (
                    <Badge variant="success" className="text-[10px]">已采用</Badge>
                  )}
                  <span className="font-medium">{topic.title}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>预估互动: {topic.estimated_engagement}</span>
                  <span className="flex gap-1">
                    {(topic.tags || []).slice(0, 2).map((t) => (
                      <span key={t} className="bg-secondary px-1 rounded">{t}</span>
                    ))}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
