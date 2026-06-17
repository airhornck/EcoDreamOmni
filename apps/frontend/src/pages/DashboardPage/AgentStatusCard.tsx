import { Link } from "react-router-dom";
import { Cpu, Mail, TrendingUp, Activity, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import type { AgentStatus } from "../../stores/dashboardStore";

interface AgentStatusCardProps {
  status: AgentStatus | null;
  isLoading: boolean;
}

export function AgentStatusCard({ status, isLoading }: AgentStatusCardProps) {
  if (isLoading) {
    return <Skeleton className="h-48 bg-card border border-border" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">
              Agent 状态
            </h2>
          </div>
          <Link
            to="/agents"
            className="text-xs text-primary hover:underline flex items-center gap-0.5"
          >
            详情 <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {!status ? (
          <EmptyState
            icon={Cpu}
            title="暂无 Agent 数据"
            description="Agent 驾驶舱上线后即可查看状态"
          />
        ) : (
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <div className="flex items-center gap-2 mb-1">
                <Cpu className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">
                  活跃 Agent
                </span>
              </div>
              <div className="text-xl font-bold text-foreground">
                {status.activeAgents ?? 0}
              </div>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <div className="flex items-center gap-2 mb-1">
                <Mail className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">
                  待处理消息
                </span>
              </div>
              <div className="text-xl font-bold text-foreground">
                {status.pendingMessages ?? 0}
              </div>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">
                  近1h成功率
                </span>
              </div>
              <div
                className={`text-xl font-bold ${status.successRate1h >= 0.9 ? "text-success" : status.successRate1h >= 0.7 ? "text-warning" : "text-red-600"}`}
              >
                {((status.successRate1h ?? 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">最近执行</span>
              </div>
              <div
                className={`text-sm font-semibold ${
                  status.lastExecutionStatus === "success"
                    ? "text-success"
                    : status.lastExecutionStatus === "failure"
                      ? "text-red-600"
                      : "text-muted-foreground"
                }`}
              >
                {status.lastExecutionStatus === "success"
                  ? "成功"
                  : status.lastExecutionStatus === "failure"
                    ? "失败"
                    : "空闲"}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
