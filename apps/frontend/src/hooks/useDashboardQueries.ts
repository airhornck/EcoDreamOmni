import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import type {
  TodayOverview,
  CoreMetrics,
  Alert,
  ActivityEntry,
  AgentStatus,
  EngagementTrend,
  QuickAction,
} from "../stores/dashboardStore";
interface AgentListItem {
  id: string;
  status: string;
  success_rate?: number;
  recent_tasks_1h?: number;
}

const dashboardKeys = {
  all: ["dashboard"] as const,
  overview: () => [...dashboardKeys.all, "overview"] as const,
  coreMetrics: () => [...dashboardKeys.all, "core-metrics"] as const,
  alerts: () => [...dashboardKeys.all, "alerts"] as const,
  activityLog: () => [...dashboardKeys.all, "activity-log"] as const,
  smartTopics: () => [...dashboardKeys.all, "smart-topics"] as const,
  agentStatus: () => [...dashboardKeys.all, "agent-status"] as const,
  engagementTrend: (days: number) =>
    [...dashboardKeys.all, "engagement-trend", days] as const,
};

export function useDashboardOverview() {
  return useQuery({
    queryKey: dashboardKeys.overview(),
    queryFn: async () => {
      const res = await apiClient<{ today: TodayOverview }>(
        "/dashboard/overview",
      );
      return res.today;
    },
  });
}

export function useDashboardCoreMetrics() {
  return useQuery({
    queryKey: dashboardKeys.coreMetrics(),
    queryFn: async () => {
      const res = await apiClient<{ metrics: CoreMetrics }>(
        "/dashboard/core-metrics",
      );
      return res.metrics;
    },
  });
}

export function useDashboardAlerts() {
  return useQuery({
    queryKey: dashboardKeys.alerts(),
    queryFn: async () => {
      const res = await apiClient<{ alerts: Alert[] }>("/dashboard/alerts");
      return res.alerts;
    },
  });
}

export function useDashboardActivityLog() {
  return useQuery({
    queryKey: dashboardKeys.activityLog(),
    queryFn: async () => {
      const res = await apiClient<{ entries: ActivityEntry[]; total: number }>(
        "/dashboard/activity-log",
      );
      return res;
    },
  });
}

export function useDashboardQuickActions() {
  return useQuery({
    queryKey: dashboardKeys.all,
    queryFn: async () => {
      const res = await apiClient<{ actions: QuickAction[] }>(
        "/dashboard/quick-actions",
      );
      return res.actions ?? [];
    },
  });
}

export function useDashboardSmartTopics() {
  return useQuery({
    queryKey: dashboardKeys.smartTopics(),
    queryFn: async () => {
      const res = await apiClient<{
        topics: Array<{
          id: string;
          title: string;
          estimated_engagement?: number;
          estimatedEngagement?: number;
          tags?: string[];
        }>;
      }>("/trend-scout/topics?limit=5");
      return (res.topics ?? []).map((t) => ({
        id: t.id,
        title: t.title,
        estimatedEngagement: t.estimated_engagement ?? t.estimatedEngagement ?? 0,
        tags: t.tags ?? [],
      }));
    },
  });
}

export function useDashboardAgentStatus() {
  return useQuery({
    queryKey: dashboardKeys.agentStatus(),
    queryFn: async () => {
      const res = await apiClient<AgentStatus | AgentListItem[]>("/agents");

      // 兼容旧版 { status } 格式（测试与过渡期）
      if (res && typeof res === "object" && "status" in res) {
        return (res as { status: AgentStatus }).status ?? null;
      }

      // 新版 /agents 返回 Agent 列表，派生出状态概览
      const agents = Array.isArray(res) ? res : [];
      const activeAgents = agents.length;
      const pendingMessages = agents.reduce(
        (sum, a) => sum + (a.recent_tasks_1h ?? 0),
        0,
      );
      const avgSuccessRate =
        activeAgents === 0
          ? 0
          : agents.reduce((sum, a) => sum + (a.success_rate ?? 0), 0) /
            activeAgents;
      const allHealthy = agents.every((a) => a.status === "ACTIVE");

      const status: AgentStatus = {
        activeAgents,
        pendingMessages,
        successRate1h: avgSuccessRate,
        lastExecutionStatus:
          activeAgents === 0
            ? "idle"
            : allHealthy
              ? "success"
              : "failure",
      };
      return status;
    },
  });
}

export function useDashboardEngagementTrend(days = 7) {
  return useQuery({
    queryKey: dashboardKeys.engagementTrend(days),
    queryFn: async () => {
      const res = await apiClient<{ trend: EngagementTrend[] }>(
        `/data-analyst/engagement-trend?days=${days}`,
      );
      return res.trend ?? [];
    },
  });
}

