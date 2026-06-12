import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Send, Users, BarChart3, ShieldCheck,
  TrendingUp, Settings, Sparkles, LogOut, HelpCircle, Cpu,
  ChevronDown, Activity
} from 'lucide-react';
import { useState } from 'react';
import type { User } from '../types';

interface NavGroup {
  label: string;
  items: { path: string; label: string; icon: typeof LayoutDashboard }[];
}

const navGroups: NavGroup[] = [
  {
    label: '运营中心',
    items: [
      { path: '/dashboard', label: '驾驶舱', icon: LayoutDashboard },
      { path: '/content', label: '任务中心', icon: FileText },
      { path: '/publish', label: '发布管理', icon: Send },
      { path: '/accounts', label: '账号池', icon: Users },
    ],
  },
  {
    label: '智能辅助',
    items: [
      { path: '/predict', label: '互动预演', icon: Sparkles },
      { path: '/trends', label: '趋势侦察', icon: TrendingUp },
      { path: '/compliance', label: '合规中心', icon: ShieldCheck },
    ],
  },
  {
    label: '数据与配置',
    items: [
      { path: '/analytics', label: '数据分析', icon: BarChart3 },
      { path: '/rules', label: '规则中心', icon: Settings },
      { path: '/skillhub', label: '技能中枢', icon: Cpu },
    ],
  },
  {
    label: 'Agent 治理',
    items: [
      { path: '/agents', label: 'Agent 驾驶舱', icon: Activity },
    ],
  },
];

export default function Sidebar({ user, onLogout, onRestartTour }: { user: User; onLogout: () => void; onRestartTour: () => void }) {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  const [collapsedGroups, setCollapsedGroups] = useState<string[]>([]);

  if (isLoginPage) return null;

  const toggleGroup = (label: string) => {
    setCollapsedGroups((prev) =>
      prev.includes(label) ? prev.filter((g) => g !== label) : [...prev, label]
    );
  };

  return (
    <aside className="w-56 bg-card border-r border-border flex flex-col h-screen sticky top-0 shrink-0">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <Cpu className="w-4 h-4 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-foreground leading-tight">EcoDreamOmni</h1>
            <p className="text-[10px] text-muted-foreground">素人号矩阵AI平台</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {navGroups.map((group) => {
          const isCollapsed = collapsedGroups.includes(group.label);
          const hasActive = group.items.some((item) => location.pathname === item.path);

          return (
            <div key={group.label} className="mb-2">
              <button
                onClick={() => toggleGroup(group.label)}
                className="w-full flex items-center justify-between px-2 py-1.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider hover:text-foreground transition-colors"
              >
                {group.label}
                <ChevronDown className={`w-3 h-3 transition-transform ${isCollapsed ? '-rotate-90' : ''}`} />
              </button>
              {!isCollapsed && (
                <div className="space-y-0.5 mt-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          isActive
                            ? 'bg-primary/10 text-primary'
                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {item.label}
                      </NavLink>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border space-y-1">
        <button
          onClick={onRestartTour}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
        >
          <HelpCircle className="w-4 h-4" />
          重新引导
        </button>
        <div className="flex items-center gap-2 px-3 py-2">
          <img src={user.avatar} alt="" className="w-7 h-7 rounded-full bg-muted" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-foreground truncate">{user.name}</p>
            <p className="text-[10px] text-muted-foreground truncate">{user.email}</p>
          </div>
          <button onClick={onLogout} className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all">
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
