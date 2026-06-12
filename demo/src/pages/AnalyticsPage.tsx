import { useState } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Upload, FileSpreadsheet, CheckCircle2, AlertCircle } from 'lucide-react';
import { mockContents, mockDailyReports } from '../data/mockData';

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'7d' | '30d'>('7d');
  const reports = period === '7d' ? mockDailyReports.slice(0, 7) : mockDailyReports;
  const hasData = mockContents.some((c) => c.actualMetrics);

  const maxPublished = Math.max(...reports.map((r) => r.publishedCount));
  const maxLikes = Math.max(...reports.map((r) => r.avgLikes));

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-foreground">数据分析</h2>
        <div className="flex items-center gap-2">
          <button onClick={() => setPeriod('7d')} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${period === '7d' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}>近7天</button>
          <button onClick={() => setPeriod('30d')} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${period === '30d' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}>近30天</button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: '总发布', value: reports.reduce((s, r) => s + r.publishedCount, 0), icon: BarChart3, color: 'text-blue-600' },
          { label: '平均覆盖率', value: `${(reports.reduce((s, r) => s + r.coverageRate, 0) / reports.length * 100).toFixed(0)}%`, icon: CheckCircle2, color: 'text-emerald-600' },
          { label: '平均 MAPE', value: `${(reports.reduce((s, r) => s + r.mape, 0) / reports.length * 100).toFixed(1)}%`, icon: TrendingDown, color: 'text-amber-600' },
          { label: '平均点赞', value: Math.round(reports.reduce((s, r) => s + r.avgLikes, 0) / reports.length), icon: TrendingUp, color: 'text-violet-600' },
        ].map((s) => (
          <div key={s.label} className="p-4 bg-card rounded-xl border border-border text-center card-hover">
            <s.icon className={`w-5 h-5 mx-auto mb-1 ${s.color}`} />
            <div className="text-xl font-bold text-foreground">{s.value}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Charts area */}
      <div className="grid lg:grid-cols-2 gap-5">
        {/* Published bar chart */}
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="section-title">发布趋势</h3>
          <div className="space-y-3">
            {reports.map((r) => (
              <div key={r.date} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-10 text-right">{r.date}</span>
                <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary/70 rounded-full transition-all" style={{ width: `${(r.publishedCount / maxPublished) * 100}%` }} />
                </div>
                <span className="text-xs font-medium w-5">{r.publishedCount}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Engagement trend */}
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="section-title">平均互动趋势</h3>
          <div className="space-y-3">
            {reports.map((r) => (
              <div key={r.date} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-10 text-right">{r.date}</span>
                <div className="flex-1 flex gap-1 h-6">
                  <div className="h-full bg-rose-300 rounded-l-full" style={{ width: `${(r.avgLikes / maxLikes) * 50}%` }} title={`点赞 ${r.avgLikes}`} />
                  <div className="h-full bg-blue-300" style={{ width: `${(r.avgComments / maxLikes) * 50}%` }} title={`评论 ${r.avgComments}`} />
                  <div className="h-full bg-amber-300 rounded-r-full" style={{ width: `${(r.avgSaves / maxLikes) * 50}%` }} title={`收藏 ${r.avgSaves}`} />
                </div>
                <span className="text-xs font-medium w-8">{r.avgLikes}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground justify-center">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-300" /> 点赞</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-300" /> 评论</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-300" /> 收藏</span>
          </div>
        </div>
      </div>

      {/* Coverage & MAPE */}
      <div className="bg-card rounded-xl border border-border p-5">
        <h3 className="section-title">覆盖率与 MAPE</h3>
        <div className="space-y-3">
          {reports.map((r) => (
            <div key={r.date} className="flex items-center gap-4">
              <span className="text-xs text-muted-foreground w-10">{r.date}</span>
              <div className="flex-1 flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-12">覆盖率</span>
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${r.coverageRate >= 0.7 ? 'bg-emerald-400' : 'bg-amber-400'}`} style={{ width: `${r.coverageRate * 100}%` }} />
                </div>
                <span className="text-xs font-medium w-10">{(r.coverageRate * 100).toFixed(0)}%</span>
              </div>
              <div className="flex items-center gap-2 w-40">
                <span className="text-xs text-muted-foreground">MAPE</span>
                <span className={`text-xs font-medium ${r.mape < 0.2 ? 'text-emerald-600' : 'text-amber-600'}`}>{(r.mape * 100).toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Content attribution with top features */}
      <div className="bg-card rounded-xl border border-border p-5">
        <h3 className="section-title">内容归因与区间命中</h3>
        {hasData ? (
          <div className="divide-y divide-border">
            {mockContents.filter((c) => c.actualMetrics && c.predictions).map((c) => {
              const withinLikes = c.actualMetrics!.likes >= c.predictions!.likes.lower && c.actualMetrics!.likes <= c.predictions!.likes.upper;
              const withinComments = c.actualMetrics!.comments >= c.predictions!.comments.lower && c.actualMetrics!.comments <= c.predictions!.comments.upper;
              const withinSaves = c.actualMetrics!.saves >= c.predictions!.saves.lower && c.actualMetrics!.saves <= c.predictions!.saves.upper;
              return (
                <div key={c.id} className="py-4">
                  <div className="flex items-center gap-4 mb-2">
                    <span className="text-sm text-foreground flex-1 truncate">{c.title}</span>
                    <span className="text-xs text-muted-foreground">点赞 {c.actualMetrics!.likes} / 预演 {c.predictions!.likes.lower}-{c.predictions!.likes.upper}</span>
                    <span className={`text-xs font-medium ${withinLikes ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {withinLikes ? '✓ 命中' : '区间外'}
                    </span>
                  </div>
                  {/* Top feature attribution mock */}
                  <div className="ml-0 sm:ml-4 bg-muted/30 rounded-lg p-3">
                    <p className="text-[10px] text-muted-foreground mb-1.5 font-medium">Top 特征影响（归因分析）</p>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { name: '标题含数字', impact: c.title.match(/\d/) ? '正向' : '中性', weight: c.title.match(/\d/) ? 0.18 : 0 },
                        { name: '配图数量', impact: '正向', weight: 0.12 },
                        { name: 'AIPL阶段', impact: c.stage === 'INTEREST' ? '正向' : '中性', weight: c.stage === 'INTEREST' ? 0.15 : 0.08 },
                        { name: '账号生命周期', impact: c.accountId === 'acc-1' ? '正向' : '弱相关', weight: c.accountId === 'acc-1' ? 0.10 : 0.05 },
                        { name: '发布时段', impact: '正向', weight: 0.09 },
                      ].filter((f) => f.weight > 0).map((f) => (
                        <div key={f.name} className="flex items-center gap-1.5 text-xs">
                          <span className="text-muted-foreground">{f.name}</span>
                          <div className="w-12 h-1 bg-muted rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${f.impact === '正向' ? 'bg-emerald-400' : 'bg-amber-400'}`} style={{ width: `${Math.min(f.weight * 500, 100)}%` }} />
                          </div>
                          <span className={`text-[10px] ${f.impact === '正向' ? 'text-emerald-600' : 'text-amber-600'}`}>{f.impact}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertCircle className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">暂无实际数据，请导入 CSV 回流数据</p>
          </div>
        )}
      </div>

      {/* Import area */}
      <div className="bg-muted/30 rounded-xl border border-dashed border-border p-6 text-center">
        <FileSpreadsheet className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">导入实际互动数据</p>
        <p className="text-xs text-muted-foreground mb-3">支持 CSV 格式：content_id, likes, comments, saves, shares, follows</p>
        <button className="btn-outline text-sm"><Upload className="w-3.5 h-3.5" /> 上传 CSV</button>
      </div>
    </div>
  );
}
