import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import type {
  TodayOverview,
  CoreMetrics,
  Alert,
  ActivityEntry,
  AgentStatus,
  StoryProgress,
  EngagementTrend,
  HitRate,
} from "../stores/dashboardStore";

const dashboardKeys = {
  all: ["dashboard"] as const,
  overview: () => [...dashboardKeys.all, "overview"] as const,
  coreMetrics: () => [...dashboardKeys.all, "core-metrics"] as const,
  alerts: () => [...dashboardKeys.all, "alerts"] as const,
  activityLog: () => [...dashboardKeys.all, "activity-log"] as const,
  smartTopics: () => [...dashboardKeys.all, "smart-topics"] as const,
  agentStatus: () => [...dashboardKeys.all, "agent-status"] as const,
  storyProgress: () => [...dashboardKeys.all, "story-progress"] as const,
  engagementTrend: (days: number) =>
    [...dashboardKeys.all, "engagement-trend", days] as const,
  hitRate: () => [...dashboardKeys.all, "hit-rate"] as const,
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
      const res = await apiClient<{ status: AgentStatus }>("/agents");
      return res.status ?? null;
    },
  });
}

export function useDashboardStoryProgress() {
  return useQuery({
    queryKey: dashboardKeys.storyProgress(),
    queryFn: async () => {
      const res = await apiClient<{
        items?: StoryProgress[];
        stories?: StoryProgress[];
      }>("/persona-stories?status=active");
      const items = res.items ?? res.stories ?? [];
      return items.filter(
        (item) =>
          item.currentNodeIndex !== undefined || item.totalNodes !== undefined,
      );
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

export function useDashboardHitRate() {
  return useQuery({
    queryKey: dashboardKeys.hitRate(),
    queryFn: async () => {
      const res = await apiClient<{ rates: HitRate[] }>(
        "/predictions/hit-rate",
      );
      return res.rates ?? [];
    },
  });
}
