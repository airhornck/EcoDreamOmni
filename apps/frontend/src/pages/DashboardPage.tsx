import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import { PageHeader } from "../components/common/PageHeader";
import { useDashboardContext } from "./DashboardPage/hooks/useDashboardContext";

import {
  useDashboardOverview,
  useDashboardCoreMetrics,
  useDashboardAlerts,
  useDashboardSmartTopics,
  useDashboardAgentStatus,
  useDashboardEngagementTrend,
  useDashboardQuickActions,
  useDashboardActivityLog,
} from "../hooks/useDashboardQueries";

import { MetricCards } from "./DashboardPage/MetricCards";
import { TodoListCard } from "./DashboardPage/TodoListCard";
import { AIInsightCard } from "./DashboardPage/AIInsightCard";
import { TrendChartCard } from "./DashboardPage/TrendChartCard";
import { AgentStatusCard } from "./DashboardPage/AgentStatusCard";
import { AlertsCard } from "./DashboardPage/AlertsCard";
import { QuickActionsCard } from "./DashboardPage/QuickActionsCard";
import { ActivityLogCard } from "./DashboardPage/ActivityLogCard";

export function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);

  useDashboardContext({ navigate });

  const overviewQuery = useDashboardOverview();
  const metricsQuery = useDashboardCoreMetrics();
  const alertsQuery = useDashboardAlerts();
  const topicsQuery = useDashboardSmartTopics();
  const agentQuery = useDashboardAgentStatus();
  const trendQuery = useDashboardEngagementTrend();
  const quickActionsQuery = useDashboardQuickActions();
  const activityLogQuery = useDashboardActivityLog();

  const isLoading =
    overviewQuery.isLoading ||
    metricsQuery.isLoading ||
    alertsQuery.isLoading ||
    topicsQuery.isLoading ||
    agentQuery.isLoading ||
    trendQuery.isLoading ||
    quickActionsQuery.isLoading ||
    activityLogQuery.isLoading;

  const pendingTasks = overviewQuery.data?.tasksPending ?? 0;

  return (
    <div className="space-y-8 animate-fade-in">
      <PageHeader
        title="工作台"
        subtitle={`欢迎回来，${user?.username ?? "运营"}。今日有 ${pendingTasks} 项待处理任务。`}
      />

      {/* 顶部指标卡 */}
      <section>
        <MetricCards
          overview={overviewQuery.data ?? null}
          coreMetrics={metricsQuery.data ?? null}
          isLoading={isLoading}
        />
      </section>

      {/* 快捷入口 */}
      <section>
        <QuickActionsCard
          actions={quickActionsQuery.data ?? []}
          isLoading={quickActionsQuery.isLoading}
        />
      </section>

      {/* Bento Grid 主体 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 左栏 */}
        <div className="space-y-8">
          <TodoListCard
            topics={topicsQuery.data ?? []}
            isLoading={topicsQuery.isLoading}
            selectedTopicId={selectedTopicId}
            onSelectTopic={setSelectedTopicId}
          />
          <ActivityLogCard
            entries={activityLogQuery.data?.entries ?? []}
            total={activityLogQuery.data?.total ?? 0}
            isLoading={activityLogQuery.isLoading}
          />
          <TrendChartCard
            data={trendQuery.data ?? []}
            isLoading={trendQuery.isLoading}
          />
        </div>

        {/* 右栏 */}
        <div className="space-y-8">
          <AIInsightCard
            insight="今日最佳发布时间是 18:00"
            detail="预估可提升 15% 互动量"
            isLoading={isLoading}
          />
          <AlertsCard
            alerts={alertsQuery.data ?? []}
            isLoading={alertsQuery.isLoading}
          />
          <AgentStatusCard
            status={agentQuery.data ?? null}
            isLoading={agentQuery.isLoading}
          />
        </div>
      </div>
    </div>
  );
}
