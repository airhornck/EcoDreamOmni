import { Link } from "react-router-dom";
import { BookOpen, ChevronRight, Clock } from "lucide-react";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import type { StoryProgress } from "../../stores/dashboardStore";

interface StoryProgressCardProps {
  stories: StoryProgress[];
  isLoading: boolean;
}

export function StoryProgressCard({
  stories,
  isLoading,
}: StoryProgressCardProps) {
  if (isLoading) {
    return <Skeleton className="h-48 bg-card border border-border" />;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">
              故事线进度
            </h2>
          </div>
          <Link
            to="/accounts"
            className="text-xs text-primary hover:underline flex items-center gap-0.5"
          >
            全部剧本 <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {stories.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="暂无活跃剧本"
            description="创建 persona 故事线后即可在此追踪进度"
            aiSuggestion="创建「新手养猫」系列故事线"
          />
        ) : (
          <div className="space-y-4">
            {stories.map((story) => {
              const pct =
                story.totalNodes > 0
                  ? Math.round(
                      (story.currentNodeIndex / story.totalNodes) * 100,
                    )
                  : 0;
              return (
                <div key={story.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">
                      {story.name}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {story.currentNodeIndex} / {story.totalNodes}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>当前：{story.currentNode}</span>
                    <span>下一节点：{story.nextNodeTopic}</span>
                  </div>
                  {story.estimatedCompletionAt && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      预计完成：
                      {new Date(story.estimatedCompletionAt).toLocaleString(
                        "zh-CN",
                        {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        },
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
