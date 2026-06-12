import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { WorkspaceLayout } from './components/layout/WorkspaceLayout'
import { useAuthStore } from './stores/authStore'
import { useCopilotPageSync } from './hooks/useCopilotPageSync'
import { useAuthCopilotSync } from './hooks/useAuthCopilotSync'


// ── Lazy-loaded page chunks ──
// 内容生产
const TaskHubPage = lazy(() => import('./pages/TaskHubPage').then(m => ({ default: m.TaskHubPage })))
const TaskHubCreatePage = lazy(() => import('./pages/TaskHubCreatePage').then(m => ({ default: m.TaskHubCreatePage })))
const ContentForgePage = lazy(() => import('./pages/ContentForgePage').then(m => ({ default: m.ContentForgePage })))
const PredictionsPage = lazy(() => import('./pages/PredictionsPage').then(m => ({ default: m.PredictionsPage })))
const LabPage = lazy(() => import('./pages/PlaygroundPage').then(m => ({ default: m.LabPage })))

// 风控与发布
const CompliancePage = lazy(() => import('./pages/CompliancePage').then(m => ({ default: m.CompliancePage })))
const ReviewPublishCenterPage = lazy(() => import('./pages/ReviewPublishCenterPage').then(m => ({ default: m.ReviewPublishCenterPage })))
const ReviewPublishDetailPage = lazy(() => import('./pages/ReviewPublishDetailPage').then(m => ({ default: m.ReviewPublishDetailPage })))
const PublisherPage = lazy(() => import('./pages/PublisherPage').then(m => ({ default: m.PublisherPage })))

// 数据智能
const DataAnalystPage = lazy(() => import('./pages/DataAnalystPage').then(m => ({ default: m.DataAnalystPage })))
const EngagementTrackingPage = lazy(() => import('./pages/EngagementTrackingPage').then(m => ({ default: m.EngagementTrackingPage })))
const AccountPoolPage = lazy(() => import('./pages/AccountPoolPage').then(m => ({ default: m.AccountPoolPage })))

// Agent 治理
const SkillHubPage = lazy(() => import('./pages/SkillHubPage').then(m => ({ default: m.SkillHubPage })))
const AgentOrchestraPage = lazy(() => import('./pages/AgentOrchestraPage').then(m => ({ default: m.AgentOrchestraPage })))
const LlmCockpitPage = lazy(() => import('./pages/LlmCockpitPage').then(m => ({ default: m.LlmCockpitPage })))

// 编排与调度
const WorkflowCockpitPage = lazy(() => import('./pages/WorkflowCockpitPage').then(m => ({ default: m.WorkflowCockpitPage })))
const CronCockpitPage = lazy(() => import('./pages/CronCockpitPage').then(m => ({ default: m.CronCockpitPage })))

// 系统配置
const PlatformRulesPage = lazy(() => import('./pages/PlatformRulesPage').then(m => ({ default: m.PlatformRulesPage })))
const PlatformSchemaPage = lazy(() => import('./pages/PlatformSchemaPage').then(m => ({ default: m.PlatformSchemaPage })))
const ProxyConfigPage = lazy(() => import('./pages/ProxyConfigPage').then(m => ({ default: m.ProxyConfigPage })))
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const AssetPoolPage = lazy(() => import('./pages/AssetPoolPage').then(m => ({ default: m.AssetPoolPage })))
const TimelinePage = lazy(() => import('./pages/TimelinePage').then(m => ({ default: m.TimelinePage })))
const VetDrugPage = lazy(() => import('./pages/VetDrugPage').then(m => ({ default: m.VetDrugPage })))
const KeywordLibraryPage = lazy(() => import('./pages/KeywordLibraryPage').then(m => ({ default: m.KeywordLibraryPage })))
const TemplateLibraryPage = lazy(() => import('./pages/TemplateLibraryPage').then(m => ({ default: m.TemplateLibraryPage })))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="space-y-3 text-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm text-muted-foreground">页面加载中...</p>
      </div>
    </div>
  )
}

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function LayoutWrapper() {
  useCopilotPageSync()
  useAuthCopilotSync()
  return (
    <WorkspaceLayout>
      <Outlet />
    </WorkspaceLayout>
  )
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<LayoutWrapper />}>
        {/* ── 规范路由（主入口）── */}
        <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />

        {/* 内容生产 */}
        <Route path="/generate" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><TaskHubPage /></Suspense></ProtectedRoute>} />
        <Route path="/generate/create" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><TaskHubCreatePage /></Suspense></ProtectedRoute>} />
        <Route path="/generate/editor/:taskId" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><ContentForgePage /></Suspense></ProtectedRoute>} />

        {/* 审核发布 */}
        <Route path="/review" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><ReviewPublishCenterPage /></Suspense></ProtectedRoute>} />
        <Route path="/review/:taskId" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><ReviewPublishDetailPage /></Suspense></ProtectedRoute>} />

        {/* 数据报表 */}
        <Route path="/analytics" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><DataAnalystPage /></Suspense></ProtectedRoute>} />

        {/* 账号管理 */}
        <Route path="/accounts" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><AccountPoolPage /></Suspense></ProtectedRoute>} />

        {/* 素材库 */}
        <Route path="/assets" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><AssetPoolPage /></Suspense></ProtectedRoute>} />

        {/* Agent 驾驶舱 */}
        <Route path="/agents" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><AgentOrchestraPage /></Suspense></ProtectedRoute>} />

        {/* 模型管理 */}
        <Route path="/models" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><LlmCockpitPage /></Suspense></ProtectedRoute>} />

        {/* 实验室 */}
        <Route path="/lab" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><LabPage /></Suspense></ProtectedRoute>} />

        {/* 关键词库 */}
        <Route path="/keywords" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><KeywordLibraryPage /></Suspense></ProtectedRoute>} />

        {/* 模板库 */}
        <Route path="/templates" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><TemplateLibraryPage /></Suspense></ProtectedRoute>} />

        {/* 设置 */}
        <Route path="/settings" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><SettingsPage /></Suspense></ProtectedRoute>} />

        {/* ── 子功能路由（保留独立入口）── */}
        <Route path="/compliance" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><CompliancePage /></Suspense></ProtectedRoute>} />
        <Route path="/publisher" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><PublisherPage /></Suspense></ProtectedRoute>} />
        <Route path="/engagement-tracking" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><EngagementTrackingPage /></Suspense></ProtectedRoute>} />
        <Route path="/skillhub" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><SkillHubPage /></Suspense></ProtectedRoute>} />
        <Route path="/workflow-cockpit" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><WorkflowCockpitPage /></Suspense></ProtectedRoute>} />
        <Route path="/cron-cockpit" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><CronCockpitPage /></Suspense></ProtectedRoute>} />
        <Route path="/workflows" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><WorkflowCockpitPage /></Suspense></ProtectedRoute>} />
        <Route path="/rules" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><PlatformRulesPage /></Suspense></ProtectedRoute>} />
        <Route path="/platform-rules" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><PlatformRulesPage /></Suspense></ProtectedRoute>} />
        <Route path="/platform-rules/schema" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><PlatformSchemaPage /></Suspense></ProtectedRoute>} />
        <Route path="/proxy-config" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><ProxyConfigPage /></Suspense></ProtectedRoute>} />

        <Route path="/timeline" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><TimelinePage /></Suspense></ProtectedRoute>} />
        <Route path="/vetdrug" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><VetDrugPage /></Suspense></ProtectedRoute>} />
        <Route path="/predictions" element={<ProtectedRoute><Suspense fallback={<PageLoader />}><PredictionsPage /></Suspense></ProtectedRoute>} />


        {/* ── 旧路由重定向（向后兼容）── */}
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        <Route path="/task-hub" element={<Navigate to="/generate" replace />} />
        <Route path="/task-hub/create" element={<Navigate to="/generate/create" replace />} />
        <Route path="/content-forge/:taskId" element={<Navigate to="/generate/editor/:taskId" replace />} />
        <Route path="/personas" element={<Navigate to="/accounts" replace />} />
        <Route path="/brand-knowledge" element={<Navigate to="/rules" replace />} />
        <Route path="/trend-scout" element={<Navigate to="/analytics" replace />} />
        <Route path="/review-publish-center" element={<Navigate to="/review" replace />} />
        <Route path="/review-publish-center/:taskId" element={<Navigate to="/review/:taskId" replace />} />
        <Route path="/data-analyst" element={<Navigate to="/analytics" replace />} />
        <Route path="/account-pool" element={<Navigate to="/accounts" replace />} />
        <Route path="/agent-orchestra" element={<Navigate to="/agents" replace />} />
        <Route path="/llm-cockpit" element={<Navigate to="/models" replace />} />
        <Route path="/playground" element={<Navigate to="/lab" replace />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
export default App
