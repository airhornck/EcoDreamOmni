import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAICopilotStore } from '../../stores/aiCopilotStore'
import { IconNav } from './IconNav'
import { Header } from './Header'
import { AICopilotPanel } from '../ai-copilot/AICopilotPanel'
import { CommandPalette } from '../ui/CommandPalette'
import { useCommandPalette } from '../ui/useCommandPalette'
import {
  Home, Sparkles, ClipboardList, BarChart3, Users, FolderOpen,
  Cpu, Settings, Play, BookOpen, Search, Zap,
} from 'lucide-react'

interface WorkspaceLayoutProps {
  children: ReactNode
}

function GlobalCommandPalette() {
  const navigate = useNavigate()
  const { open, setOpen } = useCommandPalette()

  const commands = [
    {
      id: 'nav-home', label: '工作台', group: '页面跳转',
      icon: <Home className="w-4 h-4" />,
      shortcut: 'G 1',
      onSelect: () => navigate('/'),
    },
    {
      id: 'nav-generate', label: '内容生产', group: '页面跳转',
      icon: <Sparkles className="w-4 h-4" />,
      shortcut: 'G 2',
      onSelect: () => navigate('/generate'),
    },
    {
      id: 'nav-review', label: '审核发布', group: '页面跳转',
      icon: <ClipboardList className="w-4 h-4" />,
      shortcut: 'G 3',
      onSelect: () => navigate('/review'),
    },
    {
      id: 'nav-analytics', label: '数据报表', group: '页面跳转',
      icon: <BarChart3 className="w-4 h-4" />,
      shortcut: 'G 4',
      onSelect: () => navigate('/analytics'),
    },
    {
      id: 'nav-accounts', label: '账号矩阵', group: '页面跳转',
      icon: <Users className="w-4 h-4" />,
      shortcut: 'G 5',
      onSelect: () => navigate('/accounts'),
    },
    {
      id: 'nav-assets', label: '素材库', group: '页面跳转',
      icon: <FolderOpen className="w-4 h-4" />,
      shortcut: 'G 6',
      onSelect: () => navigate('/assets'),
    },
    {
      id: 'nav-agents', label: 'Agent 舰队', group: '页面跳转',
      icon: <Cpu className="w-4 h-4" />,
      shortcut: 'G 7',
      onSelect: () => navigate('/agents'),
    },
    {
      id: 'nav-settings', label: '设置', group: '页面跳转',
      icon: <Settings className="w-4 h-4" />,
      shortcut: 'G 0',
      onSelect: () => navigate('/settings'),
    },
    {
      id: 'nav-lab', label: '实验室', group: '页面跳转',
      icon: <Play className="w-4 h-4" />,
      onSelect: () => navigate('/lab'),
    },
    {
      id: 'nav-rules', label: '平台规则', group: '页面跳转',
      icon: <BookOpen className="w-4 h-4" />,
      onSelect: () => navigate('/rules'),
    },
    {
      id: 'nav-keywords', label: '关键词库', group: '页面跳转',
      icon: <BookOpen className="w-4 h-4" />,
      shortcut: 'G K',
      onSelect: () => navigate('/keywords'),
    },
    {
      id: 'nav-templates', label: '模板库', group: '页面跳转',
      icon: <BookOpen className="w-4 h-4" />,
      shortcut: 'G T',
      onSelect: () => navigate('/templates'),
    },
    {
      id: 'ai-create', label: '创建内容', group: 'AI 快捷操作',
      icon: <Sparkles className="w-4 h-4" />,
      shortcut: 'Ctrl+N',
      onSelect: () => navigate('/generate/create'),
    },
    {
      id: 'ai-search', label: '全局搜索', group: 'AI 快捷操作',
      icon: <Search className="w-4 h-4" />,
      onSelect: () => { /* TODO: open global search */ },
    },
    {
      id: 'ai-quick', label: 'AI 快速操作', group: 'AI 快捷操作',
      icon: <Zap className="w-4 h-4" />,
      onSelect: () => { /* TODO: trigger quick action */ },
    },
  ]

  return (
    <CommandPalette
      commands={commands}
      open={open}
      onOpenChange={setOpen}
      placeholder="搜索命令、页面、快捷操作..."
    />
  )
}

export function WorkspaceLayout({ children }: WorkspaceLayoutProps) {
  const { isOpen } = useAICopilotStore()

  return (
    <div
      className="h-screen w-screen bg-background text-foreground overflow-hidden font-sans grid"
      style={{
        gridTemplateColumns: isOpen ? '48px 1fr 320px' : '48px 1fr 0fr',
        gridTemplateRows: '56px 1fr',
        transition: 'grid-template-columns 0.3s ease',
      }}
    >
      {/* Left: IconNav — rows 1-2, col 1 */}
      <div className="row-span-2 col-start-1">
        <IconNav />
      </div>

      {/* Top: Header — row 1, cols 2-3 (spans across top) */}
      <div className="col-start-2 col-span-2">
        <Header />
      </div>

      {/* Center: Main Canvas — row 2, col 2 */}
      <main className="col-start-2 row-start-2 flex flex-col min-w-0 overflow-hidden">
        <div className="flex-1 p-6 overflow-y-auto">{children}</div>
      </main>

      {/* Right: AI Copilot Panel — row 2, col 3 (below Header) */}
      <div className="col-start-3 row-start-2 min-w-0 overflow-hidden">
        <AICopilotPanel />
      </div>

      {/* Global Command Palette */}
      <GlobalCommandPalette />
    </div>
  )
}
