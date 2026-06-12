import {
  FileText,
  Send,
  Activity,
  AlertTriangle,
  BarChart3,
} from "lucide-react";
import { Skeleton } from "../../components/ui/Skeleton";
import { StatCard } from "../../components/common/StatCard";
import type { TodayOverview, CoreMetrics } from "../../stores/dashboardStore";

interface MetricCardsProps {
  overview: TodayOverview | null;
  coreMetrics: CoreMetrics | null;
  isLoading: boolean;
}

export function MetricCards({
  overview,
  coreMetrics,
  isLoading,
}: MetricCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-24 bg-card border border-border" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <StatCard
        label="待审核任务数"
        value={
          coreMetrics?.pendingReview ?? overview?.contentsPendingReview ?? 0
        }
        icon={FileText}
        variant="warning"
      />
      <StatCard
        label="今日已发布数"
        value={coreMetrics?.publishedToday ?? overview?.contentsPublished ?? 0}
        icon={Send}
        variant="success"
      />
      <StatCard
        label="队列中任务数"
        value={coreMetrics?.queuedTasks ?? 0}
        icon={Activity}
        variant="primary"
      />
      <StatCard
        label="失败 / DLQ 数"
        value={coreMetrics?.failedDlq ?? 0}
        icon={AlertTriangle}
        variant="danger"
      />
      <StatCard
        label="今日 Token 成本"
        value={`¥${(coreMetrics?.tokenCostToday ?? 0).toFixed(2)}`}
        icon={BarChart3}
        variant="default"
      />
    </div>
  );
}
