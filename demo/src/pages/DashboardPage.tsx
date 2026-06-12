import { Link } from 'react-router-dom';
import {
  FileText, Send, ShieldCheck, BarChart3, Sparkles,
  CheckCircle2, AlertTriangle, AlertCircle, Heart, MessageCircle, Bookmark,
  Activity, Cpu
} from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { TaskItem } from '../components/common/TaskItem';
import { Card, CardContent } from '../components/ui/Card';
import { AlertBanner } from '../components/ui/AlertBanner';
import { mockOverview, mockContents, mockTasks, mockAlerts, mockTrends, mockDailyReports, stageLabels, mockAgents, mockAgentHeartbeats } from '../data/mockData';

export default function DashboardPage() {
  const publishedContents = mockContents.filter((c) => c.status === 'published').slice(0, 3);
  const report = mockDailyReports[0];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground tracking-tight">驾驶舱</h2>
          <p className="text-sm text-muted-foreground mt-1">
            欢迎回来，张运营。今日有 {mockOverview.tasksPending} 项待处理任务。
          </p>
        </div>
        <Link to="/content/create" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
          <Sparkles className="w-4 h-4" />
          新建任务
        </Link>
      </div>

      {/* Overview stats */}
      <div data-tour="dashboard-stats" className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="待生成任务" value={mockOverview.tasksPending} icon={FileText} variant="primary" />
        <StatCard label="已发布内容" value={mockOverview.contentsPublished} icon={Send} variant="success" />
        <StatCard label="互动增长" value={`+${mockOverview.engagementDelta}%`} icon={BarChart3} variant="primary" />
        <StatCard label="平均健康分" value={mockOverview.avgHealthScore} icon={CheckCircle2} variant="default" />
      </div>

      {/* Agent fleet status (V2.4) */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            Agent 舰队概览
          </h3>
          <Link to="/agents" className="text-xs text-primary hover:underline">进入驾驶舱</Link>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {mockAgents.slice(0, 4).map((agent) => {
            const hb = mockAgentHeartbeats.find((h) => h.agentId === agent.id);
            const isHealthy = agent.status === 'ACTIVE';
            const isDegraded = agent.status === 'DEGRADED';
            return (
              <Link key={agent.id} to="/agents" className="p-3 bg-card rounded-xl border border-border hover:border-primary/30 hover:shadow-sm transition-all">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs font-medium text-foreground truncate">{agent.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : isDegraded ? 'bg-amber-500' : 'bg-red-500'}`} />
                  <span className="text-xs text-muted-foreground">
                    {hb?.status === 'BUSY' ? '运行中' : hb?.status === 'IDLE' ? '空闲' : hb?.status === 'UNHEALTHY' ? '故障' : '健康'}
                  </span>
                  {hb && hb.queueDepth > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-600">队列 {hb.queueDepth}</span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Quick actions */}
      <section data-tour="dashboard-actions">
        <h3 className="text-base font-semibold text-foreground mb-4">快捷操作</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { to: '/content/create', label: '创建任务', icon: Sparkles },
            { to: '/publish', label: '发布排期', icon: Send },
            { to: '/compliance', label: '合规审核', icon: ShieldCheck },
            { to: '/predict', label: '互动预演', icon: BarChart3 },
          ].map((a) => (
            <Link key={a.label} to={a.to}
              className="p-4 bg-card rounded-xl border border-border hover:border-primary/30 hover:shadow-sm transition-all flex flex-col items-center text-center gap-2.5">
              <div className="p-2 rounded-lg bg-secondary">
                <a.icon className="w-5 h-5 text-primary" />
              </div>
              <span className="text-sm font-medium text-foreground">{a.label}</span>
            </Link>
          ))}
        </div>
      </section>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: Task board + Recent content */}
        <div className="lg:col-span-2 space-y-6">
          <section data-tour="dashboard-tasks">
            <h3 className="text-base font-semibold text-foreground mb-4">任务看板</h3>
            <Card>
              {mockTasks.map((task, i) => (
                <TaskItem key={task.id} task={task} className={i < mockTasks.length - 1 ? 'border-b border-border' : ''} />
              ))}
            </Card>
          </section>

          <section>
            <h3 className="text-base font-semibold text-foreground mb-4">最近内容</h3>
            <Card className="divide-y divide-border">
              {publishedContents.map((c) => (
                <Link key={c.id} to="/content" className="flex items-center gap-3 px-4 py-3 hover:bg-muted/40 transition-colors">
                  <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-50 text-blue-600 border border-blue-100">
                    已发布
                  </span>
                  <span className="text-sm text-foreground flex-1 truncate">{c.title}</span>
                  <span className="text-xs text-muted-foreground">{c.platform}</span>
                  {c.actualMetrics && (
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Heart className="w-3 h-3" /> {c.actualMetrics.likes}
                    </span>
                  )}
                </Link>
              ))}
            </Card>
          </section>
        </div>

        {/* Right: Report + Alerts + Topics */}
        <div className="space-y-6">
          {/* Yesterday report */}
          <section data-tour="dashboard-report">
            <h3 className="text-base font-semibold text-foreground mb-4">昨日战报</h3>
            <Card>
              <CardContent className="p-4 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">发布篇数</span>
                  <span className="font-medium">{report.publishedCount} 篇</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">区间覆盖率</span>
                  <span className="font-medium text-emerald-600">{(report.coverageRate * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">MAPE</span>
                  <span className="font-medium">{(report.mape * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">平均互动</span>
                  <span className="font-medium flex items-center gap-2">
                    <Heart className="w-3 h-3 text-rose-400" /> {report.avgLikes}
                    <MessageCircle className="w-3 h-3 text-blue-400" /> {report.avgComments}
                    <Bookmark className="w-3 h-3 text-amber-400" /> {report.avgSaves}
                  </span>
                </div>
              </CardContent>
            </Card>
            <Link to="/analytics" className="block mt-2 text-center text-xs text-primary hover:underline">
              查看详细报告
            </Link>
          </section>

          {/* Trending topics */}
          <section>
            <h3 className="text-base font-semibold text-foreground mb-4">智能选题</h3>
            <Card className="divide-y divide-border">
              {mockTrends.slice(0, 3).map((t) => (
                <div key={t.id} className="px-4 py-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-primary">#{t.rank}</span>
                    <span className="text-sm text-foreground font-medium">{t.title}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{stageLabels[t.stage]}</span>
                    <span>·</span>
                    <span>互动: {t.engagementHint}</span>
                    <span>·</span>
                    <span className={`${t.riskLevel > 0.25 ? 'text-amber-600' : 'text-emerald-600'}`}>
                      审核: {t.riskLevel > 0.25 ? '较严' : '正常'}
                    </span>
                  </div>
                </div>
              ))}
            </Card>
            <Link to="/trends" className="block mt-2 text-center text-xs text-primary hover:underline">
              查看更多选题
            </Link>
          </section>

          {/* Alerts */}
          <section>
            <h3 className="text-base font-semibold text-foreground mb-4">实时告警</h3>
            <div className="space-y-2">
              {mockAlerts.slice(0, 2).map((alert) => (
                <AlertBanner
                  key={alert.id}
                  icon={alert.level === 'emergency' ? AlertTriangle : alert.level === 'warning' ? AlertCircle : CheckCircle2}
                  title={alert.title}
                  description={alert.message}
                  variant={alert.level === 'emergency' ? 'danger' : alert.level === 'warning' ? 'warning' : alert.level === 'success' ? 'success' : 'info'}
                />
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
