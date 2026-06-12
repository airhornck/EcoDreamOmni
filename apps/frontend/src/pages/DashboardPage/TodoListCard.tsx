import { Link } from "react-router-dom";
import { Lightbulb, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import type { SmartTopic } from "../../stores/dashboardStore";

interface TodoListCardProps {
  topics: SmartTopic[];
  isLoading: boolean;
  selectedTopicId?: string | null;
  onSelectTopic?: (topicId: string | null) => void;
}

export function TodoListCard({ topics, isLoading, selectedTopicId, onSelectTopic }: TodoListCardProps) {
  if (isLoading) {
    return <Skeleton className="h-64 bg-card border border-border" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">
              智能选题推荐
            </h2>
          </div>
          <Link
            to="/analytics"
            className="text-xs text-primary hover:underline flex items-center gap-0.5"
          >
            更多选题 <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {!topics || topics.length === 0 ? (
          <EmptyState
            icon={Lightbulb}
            title="暂无推荐选题"
            description="系统正在分析趋势数据，请稍后再试"
            aiSuggestion="根据最近热度话题「猫咪驱虫」生成内容"
          />
        ) : (
          <div className="space-y-3">
            {topics.map((topic) => (
              <div
                key={topic.id}
                className={`flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer ${
                  selectedTopicId === topic.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/30 hover:bg-muted/30"
                }`}
                onClick={() => onSelectTopic?.(selectedTopicId === topic.id ? null : topic.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-foreground truncate">
                    {topic.title}
                  </div>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    {topic.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="default"
                        className="text-[10px]"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-xs text-muted-foreground">预估互动</div>
                  <div className="text-sm font-semibold text-primary">
                    {(topic.estimatedEngagement ?? 0).toLocaleString()}
                  </div>
                </div>
                {/* Mode C: 「采用」按钮已移除，选题操作走 Copilot Action Card */}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
