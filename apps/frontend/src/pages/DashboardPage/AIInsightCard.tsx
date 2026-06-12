import { Sparkles } from "lucide-react";
import { Card, CardContent } from "../../components/ui/Card";
import { Skeleton } from "../../components/ui/Skeleton";

interface AIInsightCardProps {
  insight?: string;
  detail?: string;
  isLoading: boolean;
}

export function AIInsightCard({
  insight,
  detail,
  isLoading,
}: AIInsightCardProps) {
  if (isLoading) {
    return <Skeleton className="h-40 bg-card border border-border" />;
  }

  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardContent className="pt-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-xs font-medium text-primary">AI 智能建议</span>
        </div>
        <p className="text-sm font-semibold text-foreground leading-snug">
          {insight ?? "今日最佳发布时间是 18:00"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {detail ?? "预估可提升 15% 互动量"}
        </p>
        {/* Mode C: 「查看详情」按钮已移除，详情在 Copilot Panel 中展示 */}
      </CardContent>
    </Card>
  );
}
