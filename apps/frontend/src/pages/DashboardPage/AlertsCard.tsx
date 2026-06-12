import { useState } from "react";
import { AlertTriangle, AlertCircle, Info, CheckCircle2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import type { Alert } from "../../stores/dashboardStore";

const alertIconMap: Record<string, LucideIcon> = {
  emergency: AlertCircle,
  warning: AlertTriangle,
  info: Info,
  success: CheckCircle2,
};

const alertColorMap: Record<string, string> = {
  emergency: "text-red-600 bg-destructive/15 border-destructive/30",
  warning: "text-orange-600 bg-warning/15 border-warning/30",
  info: "text-blue-600 bg-info/15 border-info/30",
  success: "text-green-600 bg-success/15 border-success/30",
};

const alertBadgeVariantMap: Record<
  string,
  "danger" | "warning" | "info" | "success"
> = {
  emergency: "danger",
  warning: "warning",
  info: "info",
  success: "success",
};

interface AlertsCardProps {
  alerts: Alert[];
  isLoading: boolean;
}

export function AlertsCard({ alerts, isLoading }: AlertsCardProps) {
  const [showAll, setShowAll] = useState(false);
  const displayed = showAll ? alerts : alerts.slice(0, 5);

  if (isLoading) {
    return <Skeleton className="h-48 bg-card border border-border" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">
              异常与告警
            </h2>
          </div>
          {alerts.length > 5 && (
            <button
              onClick={() => setShowAll((v) => !v)}
              className="text-xs text-primary hover:underline"
            >
              {showAll ? "收起" : "查看全部"}
            </button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <EmptyState
            icon={CheckCircle2}
            title="暂无告警"
            description="系统运行正常，未发现异常"
          />
        ) : (
          <div className="space-y-2">
            {displayed.map((alert) => {
              const Icon = alertIconMap[alert.level] || Info;
              const colorClass =
                alertColorMap[alert.level] || alertColorMap.info;
              return (
                <div
                  key={alert.id}
                  className={`flex items-start gap-2 p-3 rounded-lg border ${colorClass}`}
                >
                  <Icon className="w-4 h-4 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{alert.title}</span>
                      <Badge
                        variant={alertBadgeVariantMap[alert.level] || "info"}
                        className="text-[10px]"
                      >
                        {alert.level === "emergency"
                          ? "紧急"
                          : alert.level === "warning"
                            ? "警告"
                            : "提示"}
                      </Badge>
                    </div>
                    <p className="text-xs mt-0.5 opacity-90">{alert.message}</p>
                    <span className="text-[10px] opacity-70 mt-1 block">
                      {new Date(alert.timestamp).toLocaleString("zh-CN")}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
