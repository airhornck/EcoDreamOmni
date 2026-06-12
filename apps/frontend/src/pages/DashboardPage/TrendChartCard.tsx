import { Suspense, lazy } from "react";
import { Link } from "react-router-dom";
import { TrendingUp } from "lucide-react";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import type { EngagementTrend } from "../../stores/dashboardStore";

const EngagementTrendChart = lazy(
  () => import("../../components/charts/EngagementTrendChart"),
);

interface TrendChartCardProps {
  data: EngagementTrend[];
  isLoading: boolean;
}

export function TrendChartCard({ data, isLoading }: TrendChartCardProps) {
  if (isLoading) {
    return <Skeleton className="h-64 bg-card border border-border" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">
              互动量趋势
            </h2>
          </div>
          <Link
            to="/analytics"
            className="text-xs text-primary hover:underline"
          >
            详细分析 →
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <EmptyState
            icon={TrendingUp}
            title="暂无趋势数据"
            description="数据导入后将展示近7日互动量趋势"
            aiSuggestion="今日数据预计 12:00 更新完成"
          />
        ) : (
          <Suspense
            fallback={
              <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">
                加载图表...
              </div>
            }
          >
            <EngagementTrendChart data={data} />
          </Suspense>
        )}
      </CardContent>
    </Card>
  );
}
