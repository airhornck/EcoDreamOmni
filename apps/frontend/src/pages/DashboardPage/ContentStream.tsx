import { ContentCard } from "../../components/ui/ContentCard";
import { EmptyState } from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";

interface ContentStreamProps {
  isLoading: boolean;
}

const mockContents = [
  {
    id: "cnt_001",
    accountName: "小艾养猫记",
    platform: "小红书",
    title: "猫咪驱虫避坑指南，这3个误区90%的人都不知道",
    tags: ["驱虫", "新手养猫"],
    engagement: "25-60",
    complianceScore: 96,
    agentTrace: [
      { name: "TrendScout", status: "success" as const, duration: "0.8s" },
      { name: "ContentForge", status: "success" as const, duration: "8.5s" },
      { name: "Compliance", status: "running" as const },
    ],
  },
  {
    id: "cnt_002",
    accountName: "省钱狗爸",
    platform: "小红书",
    title: "平价狗粮测评，这5款值得买",
    tags: ["狗粮", "测评"],
    engagement: "120-280",
    complianceScore: 88,
    agentTrace: [
      { name: "TrendScout", status: "success" as const, duration: "0.6s" },
      { name: "ContentForge", status: "success" as const, duration: "6.2s" },
      { name: "Compliance", status: "success" as const, duration: "2.1s" },
    ],
  },
  {
    id: "cnt_003",
    accountName: "阿明救助站",
    platform: "小红书",
    title: "流浪猫绝育指南：术前术后注意事项",
    tags: ["救助", "TNR"],
    engagement: "80-150",
    complianceScore: 72,
    agentTrace: [
      { name: "TrendScout", status: "success" as const, duration: "0.9s" },
      { name: "ContentForge", status: "success" as const, duration: "9.1s" },
      { name: "Compliance", status: "error" as const },
    ],
    aiSuggestion: "医疗声明待补充",
  },
  {
    id: "cnt_004",
    accountName: "宠物医院日记",
    platform: "小红书",
    title: "新手养猫体检清单，这6项必查",
    tags: ["养猫", "健康"],
    engagement: "180-320",
    complianceScore: 94,
    agentTrace: [
      { name: "TrendScout", status: "success" as const, duration: "0.7s" },
      { name: "ContentForge", status: "success" as const, duration: "7.4s" },
      { name: "Compliance", status: "success" as const, duration: "1.8s" },
    ],
  },
];

export function ContentStream({ isLoading }: ContentStreamProps) {
  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-shrink-0 w-72 h-80 bg-card border border-border"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-foreground">
          最近内容卡片流
        </span>
        <span className="text-xs text-muted-foreground">
          选中卡片后，Copilot 会主动建议
        </span>
      </div>
      {mockContents.length === 0 ? (
        <EmptyState
          emoji="📭"
          title="暂无近期内容"
          description="点击「+ 新建任务」让我帮你生成第一篇小红书笔记"
          aiSuggestion="生成新手养猫系列内容"
        />
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {mockContents.map((item) => (
            <ContentCard
              key={item.id}
              accountName={item.accountName}
              platform={item.platform}
              title={item.title}
              tags={item.tags}
              engagement={item.engagement}
              complianceScore={item.complianceScore}
              agentTrace={item.agentTrace}
              aiSuggestion={item.aiSuggestion}
              className="flex-shrink-0 w-72"
            />
          ))}
        </div>
      )}
    </div>
  );
}
