import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { useOnboarding } from './hooks/useOnboarding';
import { ToastProvider } from './components/ToastProvider';
import Sidebar from './components/Sidebar';
import OnboardingTour from './components/OnboardingTour';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ContentPage from './pages/ContentPage';
import ContentCreatePage from './pages/ContentCreatePage';
import PublishPage from './pages/PublishPage';
import AccountsPage from './pages/AccountsPage';
import PredictPage from './pages/PredictPage';
import AnalyticsPage from './pages/AnalyticsPage';
import CompliancePage from './pages/CompliancePage';
import TrendsPage from './pages/TrendsPage';
import RulesPage from './pages/RulesPage';
import SkillHubPage from './pages/SkillHubPage';
import AgentCockpitPage from './pages/AgentCockpitPage';

const onboardingSteps = [
  { id: 'welcome', title: '欢迎来到 EcoDreamOmni', description: '这是宠物健康素人号矩阵 AI 内容管理与分发平台的交互演示。你可以体验从任务创建、AI 编排、人工审核到发布与数据回流的完整闭环。', placement: 'center' as const },
  { id: 'nav', title: '左侧导航栏', description: '所有核心功能模块都在此。运营高频功能（驾驶舱/任务中心/发布/账号）与智能辅助（预演/趋势/合规）已分组展示，新增 Agent 治理模块。', targetSelector: 'aside nav', placement: 'right' as const },
  { id: 'dashboard', title: '驾驶舱概览', description: '今日概览、快捷操作、任务看板一站式呈现运营全景。点击模块可下钻到对应功能页。', targetSelector: '[data-tour="dashboard-stats"]', placement: 'bottom' as const },
  { id: 'content', title: '创建任务', description: '选择账号池+人设池+工作流模板，AI 自动编排（TrendScout→ContentForge→ComplianceGuard→PoolPredictor），经人工审核后发布。', targetSelector: '[data-tour="dashboard-actions"]', placement: 'bottom' as const },
  { id: 'publish', title: '发布管理', description: '审核通过内容进入 Publisher 队列，支持立即发布和定时排期，对接 PlatformRule L4 时段限制。', targetSelector: '[data-tour="dashboard-tasks"]', placement: 'bottom' as const },
  { id: 'analytics', title: '数据回流', description: '导入实际互动数据后，DataAnalyst 计算区间覆盖率、MAPE，提供归因分析，支持 Celery 异步模型校准。', targetSelector: '[data-tour="dashboard-report"]', placement: 'left' as const },
  { id: 'finish', title: '开始体验', description: '点击左侧导航栏，自由探索所有功能模块。所有数据均为演示数据，你可以随意操作。', placement: 'center' as const },
];

function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const onboarding = useOnboarding(onboardingSteps);

  if (!user) return <>{children}</>;

  return (
    <ToastProvider>
      <div className="flex min-h-screen">
        <Sidebar user={user} onLogout={logout} onRestartTour={onboarding.restart} />
        <div className="flex-1 flex flex-col min-w-0">
          <main className="flex-1 p-6 lg:p-8 overflow-y-auto">
            <div className="max-w-6xl mx-auto">
              {children}
            </div>
          </main>
        </div>
        <OnboardingTour
          steps={onboardingSteps}
          currentStep={onboarding.currentStep}
          isActive={onboarding.isActive}
          progress={onboarding.progress}
          onNext={onboarding.next}
          onPrev={onboarding.prev}
          onSkip={onboarding.skip}
        />
      </div>
    </ToastProvider>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function AppRoutes() {
  const { isAuthenticated, login, isLoading } = useAuth();

  return (
    <AppLayout>
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage onLogin={login} isLoading={isLoading} />} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/content" element={<ProtectedRoute><ContentPage /></ProtectedRoute>} />
        <Route path="/content/create" element={<ProtectedRoute><ContentCreatePage /></ProtectedRoute>} />
        <Route path="/publish" element={<ProtectedRoute><PublishPage /></ProtectedRoute>} />
        <Route path="/accounts" element={<ProtectedRoute><AccountsPage /></ProtectedRoute>} />
        <Route path="/predict" element={<ProtectedRoute><PredictPage /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><AnalyticsPage /></ProtectedRoute>} />
        <Route path="/compliance" element={<ProtectedRoute><CompliancePage /></ProtectedRoute>} />
        <Route path="/trends" element={<ProtectedRoute><TrendsPage /></ProtectedRoute>} />
        <Route path="/rules" element={<ProtectedRoute><RulesPage /></ProtectedRoute>} />
        <Route path="/skillhub" element={<ProtectedRoute><SkillHubPage /></ProtectedRoute>} />
        <Route path="/agents" element={<ProtectedRoute><AgentCockpitPage /></ProtectedRoute>} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppLayout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
