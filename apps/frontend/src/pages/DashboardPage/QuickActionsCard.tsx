import { Link } from "react-router-dom";
import {
  FileText,
  Send,
  ShieldCheck,
  BarChart3,
  Settings,
  Sparkles,
  ClipboardCheck,
  Users,
  Bot,
  Image,
  BookOpen,
  Brain,
  Layers,
  ClipboardList,
  LayoutDashboard,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "../../components/ui/Badge";
import { Skeleton } from "../../components/ui/Skeleton";
import type { QuickAction } from "../../stores/dashboardStore";

const ICON_MAP: Record<string, LucideIcon> = {
  LayoutDashboard,
  FileText,
  Send,
  ShieldCheck,
  BarChart3,
  Settings,
  Sparkles,
  ClipboardCheck,
  Users,
  Bot,
  Image,
  BookOpen,
  Brain,
  Layers,
  ClipboardList,
};

interface QuickActionsCardProps {
  actions: QuickAction[];
  isLoading: boolean;
}

export function QuickActionsCard({ actions, isLoading }: QuickActionsCardProps) {
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
      {actions.map((action) => {
        const Icon = ICON_MAP[action.icon] || LayoutDashboard;
        return (
          <Link
            key={action.id}
            to={action.href}
            className="group relative flex flex-col items-center justify-center gap-2 p-4 rounded-xl border border-border bg-card text-center transition-colors hover:border-primary/50 hover:bg-muted/30"
          >
            <Icon className="w-6 h-6 text-primary transition-transform group-hover:scale-110" />
            <span className="text-sm font-medium text-foreground">
              {action.label}
            </span>
            {typeof action.badge === "number" && action.badge > 0 && (
              <Badge
                variant="danger"
                className="absolute top-2 right-2 text-[10px] px-1.5 py-0"
              >
                {action.badge}
              </Badge>
            )}
          </Link>
        );
      })}
    </div>
  );
}
