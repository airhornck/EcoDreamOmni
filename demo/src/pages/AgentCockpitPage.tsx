import { useState } from 'react';
import {
  Activity, Heart, AlertTriangle, CheckCircle2, XCircle,
  Clock, Cpu, Database, Globe, Layers, PauseCircle, PlayCircle,
  ChevronDown, ChevronUp, TrendingUp, TrendingDown, Zap, BarChart3
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { mockAgents, mockAgentHeartbeats, mockAgentDailyMetrics, mockAgentAlerts } from '../data/mockData';

const statusConfig: Record<string, { icon: typeof Activity; color: string; bg: string; label: string }> = {
  ACTIVE: { icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50', label: '健康' },
  DEGRADED: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50', label: '降级' },
  PAUSED: { icon: PauseCircle, color: 'text-slate-500', bg: 'bg-slate-100', label: '暂停' },
  OFFLINE: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', label: '离线' },
  REGISTERED: { icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50', label: '已注册' },
};

const heartbeatConfig: Record<string, { color: string; label: string }> = {
  HEALTHY: { color: 'text-emerald-600', label: '健康' },
  IDLE: { color: 'text-blue-600', label: '空闲' },
  BUSY: { color: 'text-violet-600', label: '运行' },
  UNHEALTHY: { color: 'text-red-600', label: '故障' },
};

const roleLabels: Record<string, string> = {
  TREND_SCOUT: '趋势侦察',
  CONTENT_FORGE: '内容生成',
  COMPLIANCE_GUARD: '合规审核',
  PUBLISHER: '发布调度',
  DATA_ANALYST: '数据分析',
  POOL_PREDICTOR: '互动预测',
  MARKETING_METHODOLOGY: '方法论中枢',
  PLATFORM_RULE: '规则引擎',
  ORCHESTRATOR: '编排器',
};

const severityConfig: Record<string, { color: string; bg: string; label: string }> = {
  P0: { color: 'text-red-700', bg: 'bg-red-50 border-red-200', label: 'P0 紧急' },
  P1: { color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200', label: 'P1 重要' },
  P2: { color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200', label: 'P2 提示' },
};

export default function AgentCockpitPage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'status' | 'metrics' | 'alerts'>('status');

  const statusCounts = {
    healthy: mockAgents.filter((a) => a.status === 'ACTIVE').length,
    degraded: mockAgents.filter((a) => a.status === 'DEGRADED').length,
    offline: mockAgents.filter((a) => a.status === 'OFFLINE').length,
    paused: mockAgents.filter((a) => a.status === 'PAUSED').length,
  };

  const selectedMetrics = selectedAgent
    ? mockAgentDailyMetrics.filter((m) => m.agentId === selectedAgent)
    : [];

  const selectedAlerts = selectedAgent
    ? mockAgentAlerts.filter((a) => a.agentId === selectedAgent)
    : mockAgentAlerts;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            Agent 驾驶舱
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Agent 舰队状态监控、统计报表与配置管理
          </p>
        </div>
      </div>

      {/* Status summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: '健康', count: statusCounts.healthy, icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200' },
          { label: '降级', count: statusCounts.degraded, icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200' },
          { label: '故障', count: statusCounts.offline, icon: XCircle, color: 'text-red-600', bg: 'bg-red-50 border-red-200' },
          { label: '暂停', count: statusCounts.paused, icon: PauseCircle, color: 'text-slate-500', bg: 'bg-slate-100 border-slate-200' },
        ].map((s) => (
          <div key={s.label} className={`p-4 rounded-xl border text-center ${s.bg}`}>
            <s.icon className={`w-5 h-5 mx-auto mb-1 ${s.color}`} />
            <div className={`text-2xl font-bold ${s.color}`}>{s.count}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-1">
        {[
          { key: 'status' as const, label: '状态看板', icon: Activity },
          { key: 'metrics' as const, label: '统计报表', icon: BarChart3 },
          { key: 'alerts' as const, label: '告警历史', icon: AlertTriangle },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium transition-all border-b-2 -mb-1 ${
              activeTab === tab.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Status Tab */}
      {activeTab === 'status' && (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Agent 名称</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">角色</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">状态</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">心跳</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">当前任务</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">队列</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">版本</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">环境</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {mockAgents.map((agent) => {
                  const hb = mockAgentHeartbeats.find((h) => h.agentId === agent.id);
                  const st = statusConfig[agent.status];
                  const hbSt = hb ? heartbeatConfig[hb.status] : null;
                  return (
                    <tr
                      key={agent.id}
                      className={`hover:bg-muted/30 transition-colors cursor-pointer ${selectedAgent === agent.id ? 'bg-primary/5' : ''}`}
                      onClick={() => setSelectedAgent(agent.id === selectedAgent ? null : agent.id)}
                    >
                      <td className="px-4 py-3 font-medium text-foreground">{agent.name}</td>
                      <td className="px-4 py-3 text-muted-foreground">{roleLabels[agent.role]}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${st.bg} ${st.color}`}>
                          <st.icon className="w-3 h-3" />
                          {st.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {hbSt ? (
                          <span className={`text-xs font-medium ${hbSt.color}`}>{hbSt.label}</span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground truncate max-w-[120px]">
                        {hb?.currentTaskId || '—'}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">{hb?.queueDepth ?? 0}</td>
                      <td className="px-4 py-3 text-xs font-mono text-muted-foreground">{agent.version}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-1.5 py-0.5 rounded ${agent.env === 'prod' ? 'bg-emerald-50 text-emerald-600' : agent.env === 'staging' ? 'bg-amber-50 text-amber-600' : 'bg-blue-50 text-blue-600'}`}>
                          {agent.env}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Metrics Tab */}
      {activeTab === 'metrics' && (
        <div className="space-y-5">
          {/* Agent selector for metrics */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-muted-foreground">选择 Agent:</span>
            {mockAgents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id === selectedAgent ? null : agent.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedAgent === agent.id
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground hover:bg-muted'
                }`}
              >
                {agent.name}
              </button>
            ))}
          </div>

          {selectedMetrics.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {selectedMetrics.map((m) => (
                <Card key={m.agentId + m.date}>
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{m.date}</span>
                      <span className={`text-xs font-medium ${m.taskCompletionRate >= 0.9 ? 'text-emerald-600' : 'text-amber-600'}`}>
                        完成率 {(m.taskCompletionRate * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="text-center p-2 bg-muted/30 rounded-lg">
                        <div className="text-lg font-bold text-foreground">{m.totalInvocations}</div>
                        <div className="text-[10px] text-muted-foreground">总调用</div>
                      </div>
                      <div className="text-center p-2 bg-muted/30 rounded-lg">
                        <div className="text-lg font-bold text-foreground">{m.humanInterventionCount}</div>
                        <div className="text-[10px] text-muted-foreground">人工干预</div>
                      </div>
                      <div className="text-center p-2 bg-muted/30 rounded-lg">
                        <div className="text-lg font-bold text-foreground">{(m.avgLatencyMs / 1000).toFixed(1)}s</div>
                        <div className="text-[10px] text-muted-foreground">平均延迟</div>
                      </div>
                      <div className="text-center p-2 bg-muted/30 rounded-lg">
                        <div className="text-lg font-bold text-foreground">${m.estimatedCostUsd.toFixed(2)}</div>
                        <div className="text-[10px] text-muted-foreground">预估成本</div>
                      </div>
                    </div>
                    {m.qualityScoreAvg && (
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-muted-foreground">质量评分</span>
                        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-primary rounded-full" style={{ width: `${m.qualityScoreAvg}%` }} />
                        </div>
                        <span className="font-medium">{m.qualityScoreAvg}</span>
                      </div>
                    )}
                    <div className="text-[10px] text-muted-foreground">
                      Token: {m.totalInputTokens.toLocaleString()} in / {m.totalOutputTokens.toLocaleString()} out
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-card rounded-xl border border-border">
              <BarChart3 className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">请选择上方 Agent 查看统计详情</p>
            </div>
          )}

          {/* Human intervention leaderboard */}
          <Card>
            <CardContent className="p-5">
              <h3 className="text-sm font-semibold text-foreground mb-4">人机干预排行榜 TOP5</h3>
              <div className="space-y-2">
                {mockAgentDailyMetrics
                  .sort((a, b) => b.humanInterventionRate - a.humanInterventionRate)
                  .slice(0, 5)
                  .map((m, i) => {
                    const agent = mockAgents.find((a) => a.id === m.agentId);
                    return (
                      <div key={m.agentId} className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                        <span className="text-sm text-foreground flex-1">{agent?.name || m.agentId}</span>
                        <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-amber-400 rounded-full" style={{ width: `${Math.min(m.humanInterventionRate * 100 * 5, 100)}%` }} />
                        </div>
                        <span className="text-xs font-medium text-muted-foreground w-10 text-right">
                          {(m.humanInterventionRate * 100).toFixed(0)}%
                        </span>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-3">
          {selectedAlerts.length > 0 ? (
            selectedAlerts.map((alert) => (
              <Card key={alert.id} className={`border ${severityConfig[alert.severity].bg}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className={`w-5 h-5 mt-0.5 ${severityConfig[alert.severity].color}`} />
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${severityConfig[alert.severity].bg} ${severityConfig[alert.severity].color}`}>
                            {severityConfig[alert.severity].label}
                          </span>
                          <span className="text-xs text-muted-foreground">{alert.alertType}</span>
                          <span className="text-xs text-muted-foreground">·</span>
                          <span className="text-xs text-muted-foreground">
                            {mockAgents.find((a) => a.id === alert.agentId)?.name || alert.agentId}
                          </span>
                        </div>
                        <p className="text-sm text-foreground">{alert.message}</p>
                        {alert.rootCause && (
                          <p className="text-xs text-muted-foreground mt-1">根因: {alert.rootCause}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`text-xs font-medium ${
                        alert.status === 'OPEN' ? 'text-red-600' :
                        alert.status === 'ACKED' ? 'text-amber-600' :
                        alert.status === 'RESOLVED' ? 'text-emerald-600' :
                        'text-slate-500'
                      }`}>
                        {alert.status === 'OPEN' ? '未处理' : alert.status === 'ACKED' ? '已确认' : alert.status === 'RESOLVED' ? '已解决' : '已忽略'}
                      </span>
                      <p className="text-[10px] text-muted-foreground mt-1">{alert.createdAt}</p>
                      {alert.ackedBy && <p className="text-[10px] text-muted-foreground">确认人: {alert.ackedBy}</p>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <div className="text-center py-12 bg-card rounded-xl border border-border">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">暂无告警</p>
            </div>
          )}
        </div>
      )}

      {/* Agent config hint */}
      <div className="bg-blue-50 rounded-xl border border-blue-200 p-4 flex items-start gap-3">
        <Zap className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-blue-800">Agent 治理说明</p>
          <p className="text-xs text-blue-600 mt-1">
            AgentHub 提供注册发现、配置版本化、环境隔离与权限管理；AgentWatch 负责心跳监控与异常告警；AgentMetrics 统计任务完成率、Token 成本与质量评分。Phase 1 聚焦基础治理，Phase 2 扩展链路追踪与自动熔断。
          </p>
        </div>
      </div>
    </div>
  );
}
