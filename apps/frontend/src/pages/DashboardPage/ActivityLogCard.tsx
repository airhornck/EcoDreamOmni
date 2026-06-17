import { Link } from "react-router-dom";
import { Clock, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import type { ActivityEntry } from "../../stores/dashboardStore";

interface ActivityLogCardProps {
  entries: ActivityEntry[];
  total: number;
  isLoading: boolean;
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function ActivityLogCard({
  entries,
  total,
  isLoading,
}: ActivityLogCardProps) {
  if (isLoading) {
    return <Skeleton className="h-64 bg-card border border-border" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">
              最近动态
            </h2>
          </div>
          <Link
            to="/timeline"
            className="text-xs text-primary hover:underline flex items-center gap-0.5"
          >
            全部 {total} 条 <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="暂无动态"
            description="系统运行记录将在这里展示"
          />
        ) : (
          <div className="space-y-3">
            {entries.slice(0, 6).map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 text-sm p-3 rounded-lg border border-border bg-muted/20"
              >
                <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-medium shrink-0">
                  {entry.actor?.[0] ?? "系"}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-foreground">
                    <span className="font-medium">{entry.actor}</span>{" "}
                    {entry.action}{" "}
                    <span className="text-primary">{entry.target}</span>
                  </p>
                  <span className="text-[10px] text-muted-foreground mt-0.5 block">
                    {formatTime(entry.timestamp)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
