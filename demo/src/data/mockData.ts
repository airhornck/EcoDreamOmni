import type { Account, ContentItem, TrendItem, PlatformRule, Task, AlertItem, DashboardOverview, DailyReport, User, AgentRegistration, AgentHeartbeat, AgentDailyMetrics, AgentAlert, Persona, WorkflowTemplate } from '../types';

export const mockUser: User = {
  id: 'u1',
  email: 'demo@ecodream.omni',
  name: '张运营',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=demo',
  role: 'admin',
};

export const mockOverview: DashboardOverview = {
  tasksPending: 12,
  briefsPending: 5,
  contentsPendingReview: 8,
  contentsPublished: 156,
  engagementDelta: 23.5,
  avgHealthScore: 87,
};

export const mockPersonas: Persona[] = [
  { id: 'p1', name: '温暖铲屎官', description: '温暖亲切、emoji丰富、专家但不高高在上的猫宠博主', voice: '温暖亲切、emoji丰富、专家但不高高在上', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=p1', accountIds: ['acc-1', 'acc-2'] },
  { id: 'p2', name: '科学养猫派', description: '理性客观、数据支撑、科普向的宠物健康博主', voice: '理性客观、数据支撑、科普向', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=p2', accountIds: ['acc-3'] },
  { id: 'p3', name: '搞笑喵星人', description: '幽默风趣、段子手、轻松日常向的宠物娱乐博主', voice: '幽默风趣、段子手、轻松日常', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=p3', accountIds: ['acc-4'] },
  { id: 'p4', name: '资深兽医助理', description: '专业严谨、医疗背景、注重合规的宠物健康博主', voice: '专业严谨、医疗背景、注重合规', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=p4', accountIds: ['acc-5'] },
];

export const mockWorkflowTemplates: WorkflowTemplate[] = [
  { id: 'wf-standard', name: '标准内容生产', description: '完整工作流：TrendScout选题 → ContentForge生成 → ComplianceGuard审核 → PoolPredictor预演', steps: ['trend_scout', 'content_forge', 'compliance_guard', 'pool_predictor'], isLightweight: false },
  { id: 'wf-light', name: '轻量快速生产', description: '精简工作流：ContentForge生成 → ComplianceGuard审核（跳过趋势侦察）', steps: ['content_forge', 'compliance_guard'], isLightweight: true },
];

export const mockAccounts: Account[] = [
  { id: 'acc-1', platform: 'xhs', nickname: '铲屎官日记', avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=cat1', status: 'active', healthScore: 92, followers: 3420, todayPublished: 1, dailyLimit: 3, lifecycle: 'growth', lastLogin: '2025-04-13', fingerprint: 'fp-xhs-a1b2' },
  { id: 'acc-2', platform: 'xhs', nickname: '萌宠小课堂', avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=cat2', status: 'active', healthScore: 88, followers: 1850, todayPublished: 0, dailyLimit: 3, lifecycle: 'cold_start', lastLogin: '2025-04-14', fingerprint: 'fp-xhs-c3d4' },
  { id: 'acc-3', platform: 'xhs', nickname: '猫咪健康站', avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=cat3', status: 'warming', healthScore: 76, followers: 560, todayPublished: 0, dailyLimit: 1, lifecycle: 'cold_start', lastLogin: '2025-04-12', fingerprint: 'fp-xhs-e5f6' },
  { id: 'acc-4', platform: 'douyin', nickname: '喵星人观察员', avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=cat4', status: 'active', healthScore: 85, followers: 8900, todayPublished: 2, dailyLimit: 5, lifecycle: 'mature', lastLogin: '2025-04-14', fingerprint: 'fp-dy-g7h8' },
  { id: 'acc-5', platform: 'shipinhao', nickname: '养猫知识库', avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=cat5', status: 'restricted', healthScore: 62, followers: 1200, todayPublished: 1, dailyLimit: 1, lifecycle: 'growth', lastLogin: '2025-04-10', fingerprint: 'fp-sp-i9j0' },
];

export const mockContents: ContentItem[] = [
  {
    id: 'c1', title: '换季掉毛别慌！3招让主子毛发亮丽', body: '姐妹们！每到换季，家里是不是猫毛满天飞？今天分享3个亲测有效的方法...', tags: ['#猫咪掉毛', '#养猫知识', '#宠物护理'], images: [], stage: 'AWARENESS', status: 'published', accountId: 'acc-1', accountName: '铲屎官日记', platform: 'xhs', createdAt: '2025-04-14T08:00:00', publishedAt: '2025-04-14T10:30:00',
    predictions: { likes: { lower: 12, median: 35, upper: 89 }, comments: { lower: 1, median: 5, upper: 18 }, saves: { lower: 3, median: 12, upper: 42 }, intervalMode: 'prior', confidence: 0.65 },
    actualMetrics: { likes: 38, comments: 6, saves: 15, shares: 2, follows: 4, exposure: 1200 },
  },
  {
    id: 'c2', title: '猫咪驱虫避坑指南，这3个误区90%的人都不知道', body: '驱虫不是越贵越好！很多铲屎官陷入这3个误区...', tags: ['#猫咪驱虫', '#新手养猫', '#宠物健康'], images: [], stage: 'INTEREST', status: 'reviewing', createdAt: '2025-04-14T09:00:00',
    predictions: { likes: { lower: 20, median: 55, upper: 120 }, comments: { lower: 2, median: 8, upper: 25 }, saves: { lower: 5, median: 18, upper: 50 }, intervalMode: 'prior', confidence: 0.68 },
    complianceResult: { overallPassed: true, layers: [{ layer: 'L1', passed: true }, { layer: 'L2', passed: true, score: 0.42 }, { layer: 'L3', passed: true, reason: 'growth: 1/3' }, { layer: 'L4', passed: true, rules: [] }], action: 'pass' },
  },
  {
    id: 'c3', title: '这款猫粮吃了马上见效，三天治好软便！', body: '紧急推荐！我家主子吃了这款猫粮，软便问题三天就好转了...', tags: ['#猫粮推荐', '#软便', '#急'], images: [], stage: 'PURCHASE', status: 'rejected', accountId: 'acc-2', accountName: '萌宠小课堂', platform: 'xhs', createdAt: '2025-04-13T15:00:00',
    complianceResult: { overallPassed: false, layers: [{ layer: 'L1', passed: false, hits: ['马上见效', '三天治好'] }, { layer: 'L2', passed: true, score: 0.45 }, { layer: 'L3', passed: true, reason: 'cold_start: 1/1' }, { layer: 'L4', passed: true, rules: [] }], action: 'block' },
  },
  {
    id: 'c4', title: '早安～毛孩子今天也是元气满满的一天！', body: '周末愉快呀 下雨天记得给主子备好小毯子哦', tags: ['#早安', '#猫咪', '#日常'], images: [], stage: 'LOYALTY', status: 'draft', createdAt: '2025-04-14T07:00:00',
  },
  {
    id: 'c5', title: '2024年度最受欢迎猫砂盘点', body: '综合铲屎官们的真实反馈，整理出这份年度猫砂榜单...', tags: ['#猫砂', '#盘点', '#年度'], images: [], stage: 'INTEREST', status: 'approved', accountId: 'acc-4', accountName: '喵星人观察员', platform: 'douyin', createdAt: '2025-04-13T10:00:00', scheduledAt: '2025-04-14T20:00:00',
    predictions: { likes: { lower: 45, median: 120, upper: 280 }, comments: { lower: 5, median: 18, upper: 45 }, saves: { lower: 12, median: 40, upper: 95 }, intervalMode: 'fitted', confidence: 0.72 },
  },
  {
    id: 'c6', title: '新手养猫第一周必做清单', body: '接猫回家的第一周，这10件事一定要做好...', tags: ['#新手养猫', '#接猫', '#清单'], images: [], stage: 'AWARENESS', status: 'published', accountId: 'acc-1', accountName: '铲屎官日记', platform: 'xhs', createdAt: '2025-04-12T14:00:00', publishedAt: '2025-04-12T16:00:00',
    predictions: { likes: { lower: 30, median: 80, upper: 200 }, comments: { lower: 3, median: 12, upper: 35 }, saves: { lower: 8, median: 28, upper: 75 }, intervalMode: 'prior', confidence: 0.62 },
    actualMetrics: { likes: 85, comments: 14, saves: 32, shares: 8, follows: 12, exposure: 3500 },
  },
];

export const mockTrends: TrendItem[] = [
  { id: 't1', rank: 1, title: '猫咪换季掉毛怎么办', titleStructure: '数字+痛点+时间跨度', engagementHint: '高', stage: 'AWARENESS', tags: ['#猫咪掉毛', '#换季'], postTime: '2h前', riskLevel: 0.1 },
  { id: 't2', rank: 2, title: '这5款猫粮我家猫都爱吃', titleStructure: '数字+产品+体验', engagementHint: '高', stage: 'INTEREST', tags: ['#猫粮', '#测评'], postTime: '3h前', riskLevel: 0.3 },
  { id: 't3', rank: 3, title: '新手养猫避坑大全', titleStructure: '人群+痛点+大全', engagementHint: '中', stage: 'AWARENESS', tags: ['#新手养猫', '#避坑'], postTime: '5h前', riskLevel: 0.2 },
  { id: 't4', rank: 4, title: '猫咪软便不用慌，一篇讲清楚', titleStructure: '痛点+否定+科普', engagementHint: '高', stage: 'INTEREST', tags: ['#猫咪软便', '#科普'], postTime: '6h前', riskLevel: 0.15 },
  { id: 't5', rank: 5, title: '2024猫砂终极测评', titleStructure: '年份+产品+测评', engagementHint: '中', stage: 'PURCHASE', tags: ['#猫砂', '#测评'], postTime: '8h前', riskLevel: 0.25 },
];

export const mockRules: PlatformRule[] = [
  { id: 'r1', layer: 'l1', name: '处方药关键词拦截', condition: 'content 包含 [处方、诊断、治疗]', action: 'block', priority: 100, enabled: true, version: 3 },
  { id: 'r2', layer: 'l1', name: '疗效承诺拦截', condition: 'content 包含 [马上见效、三天治好、立竿见影]', action: 'block', priority: 90, enabled: true, version: 2 },
  { id: 'r3', layer: 'l2', name: '平台敏感词检测', condition: 'semantic risk score > 0.7', action: 'warn', priority: 70, enabled: true, version: 5 },
  { id: 'r4', layer: 'l3', name: '新号日发频率限制', condition: 'lifecycle=cold_start AND todayPublished >= 1', action: 'block', priority: 60, enabled: true, version: 2 },
  { id: 'r5', layer: 'l3', name: '成长期日发频率限制', condition: 'lifecycle=growth AND todayPublished >= 3', action: 'block', priority: 55, enabled: true, version: 2 },
  { id: 'r6', layer: 'l4', name: '节日临时风控', condition: 'effective_from 在节日区间内', action: 'warn', priority: 40, enabled: false, version: 1 },
];

export const mockTasks: Task[] = [
  { id: 'task-1', title: '生成「猫咪掉毛」图文内容', status: 'completed', type: 'generate', createdAt: '2025-04-14T08:00:00', completedAt: '2025-04-14T08:02:00' },
  { id: 'task-2', title: '合规审核 #c2', status: 'running', type: 'review', createdAt: '2025-04-14T09:00:00' },
  { id: 'task-3', title: '发布「年度猫砂盘点」到抖音', status: 'pending', type: 'publish', createdAt: '2025-04-14T09:30:00' },
  { id: 'task-4', title: '模型校准检查', status: 'pending', type: 'calibrate', createdAt: '2025-04-14T06:00:00' },
  { id: 'task-5', title: '生成「驱虫避坑」图文内容', status: 'completed', type: 'generate', createdAt: '2025-04-14T09:00:00', completedAt: '2025-04-14T09:01:30' },
];

export const mockAlerts: AlertItem[] = [
  { id: 'a1', level: 'warning', title: '账号「喵星人观察员」今日已发2篇', message: '距离日限5篇还有3篇额度，建议错峰发布', timestamp: '2025-04-14T10:00:00' },
  { id: 'a2', level: 'emergency', title: '内容 #c3 被合规拦截', message: 'L1 关键词命中：马上见效、三天治好；已阻止发布', timestamp: '2025-04-13T15:05:00' },
  { id: 'a3', level: 'info', title: '昨日战报已生成', message: '6篇内容发布，区间覆盖率 83%，平均点赞 42', timestamp: '2025-04-14T07:00:00' },
  { id: 'a4', level: 'success', title: '模型校准任务完成', message: 'MAPE 从 18.5% 降至 14.2%，已更新预测模型', timestamp: '2025-04-13T22:00:00' },
];

export const mockDailyReports: DailyReport[] = [
  { date: '04-14', publishedCount: 6, coverageRate: 0.83, mape: 0.142, avgLikes: 42, avgComments: 8, avgSaves: 18 },
  { date: '04-13', publishedCount: 5, coverageRate: 0.76, mape: 0.185, avgLikes: 35, avgComments: 6, avgSaves: 14 },
  { date: '04-12', publishedCount: 4, coverageRate: 0.71, mape: 0.201, avgLikes: 28, avgComments: 5, avgSaves: 10 },
  { date: '04-11', publishedCount: 7, coverageRate: 0.69, mape: 0.220, avgLikes: 31, avgComments: 7, avgSaves: 12 },
  { date: '04-10', publishedCount: 3, coverageRate: 0.65, mape: 0.245, avgLikes: 22, avgComments: 4, avgSaves: 8 },
  { date: '04-09', publishedCount: 5, coverageRate: 0.60, mape: 0.280, avgLikes: 25, avgComments: 5, avgSaves: 9 },
  { date: '04-08', publishedCount: 4, coverageRate: 0.55, mape: 0.310, avgLikes: 20, avgComments: 3, avgSaves: 7 },
];

export const stageLabels: Record<string, string> = {
  AWARENESS: '认知期',
  INTEREST: '兴趣期',
  PURCHASE: '购买期',
  LOYALTY: '忠诚期',
};

export const statusLabels: Record<string, { text: string; color: string; bg: string }> = {
  draft: { text: '草稿', color: 'text-slate-600', bg: 'bg-slate-100' },
  reviewing: { text: '审核中', color: 'text-amber-600', bg: 'bg-amber-50' },
  approved: { text: '已通过', color: 'text-emerald-600', bg: 'bg-emerald-50' },
  published: { text: '已发布', color: 'text-blue-600', bg: 'bg-blue-50' },
  rejected: { text: '已驳回', color: 'text-red-600', bg: 'bg-red-50' },
};

export const platformLabels: Record<string, string> = {
  xhs: '小红书',
  douyin: '抖音',
  shipinhao: '视频号',
};

export const lifecycleLabels: Record<string, string> = {
  cold_start: '冷启动',
  growth: '成长期',
  mature: '成熟期',
};

// Agent mock data (V2.4)
export const mockAgents: AgentRegistration[] = [
  { id: 'agent-content-forge-1', name: 'ContentForge-A1', role: 'CONTENT_FORGE', description: 'AI 内容生成 Agent', owner: '张运营', status: 'ACTIVE', env: 'prod', version: 'v1.3', createdAt: '2025-03-01T00:00:00', updatedAt: '2025-04-14T10:00:00' },
  { id: 'agent-compliance-1', name: 'ComplianceGuard-1', role: 'COMPLIANCE_GUARD', description: '四层合规审核 Agent', owner: '李合规', status: 'ACTIVE', env: 'prod', version: 'v2.1', createdAt: '2025-03-05T00:00:00', updatedAt: '2025-04-13T22:00:00' },
  { id: 'agent-publisher-1', name: 'Publisher-Main', role: 'PUBLISHER', description: '多平台发布调度 Agent', owner: '张运营', status: 'DEGRADED', env: 'prod', version: 'v1.0', createdAt: '2025-03-10T00:00:00', updatedAt: '2025-04-14T09:30:00' },
  { id: 'agent-pool-predictor-1', name: 'PoolPredictor-1', role: 'POOL_PREDICTOR', description: '互动量区间预测 Agent', owner: '王算法', status: 'ACTIVE', env: 'prod', version: 'v1.5', createdAt: '2025-03-15T00:00:00', updatedAt: '2025-04-12T18:00:00' },
  { id: 'agent-trend-scout-1', name: 'TrendScout-1', role: 'TREND_SCOUT', description: '热点趋势侦察 Agent', owner: '张运营', status: 'ACTIVE', env: 'prod', version: 'v0.8', createdAt: '2025-04-01T00:00:00', updatedAt: '2025-04-14T08:00:00' },
  { id: 'agent-data-analyst-1', name: 'DataAnalyst-1', role: 'DATA_ANALYST', description: '数据回流与归因分析 Agent', owner: '王算法', status: 'ACTIVE', env: 'prod', version: 'v1.1', createdAt: '2025-04-05T00:00:00', updatedAt: '2025-04-14T07:00:00' },
  { id: 'agent-marketing-1', name: 'MarketingMethod-1', role: 'MARKETING_METHODOLOGY', description: 'AIPL 方法论中枢 Agent', owner: '张运营', status: 'PAUSED', env: 'staging', version: 'v0.5', createdAt: '2025-04-10T00:00:00', updatedAt: '2025-04-13T15:00:00' },
];

export const mockAgentHeartbeats: AgentHeartbeat[] = [
  { agentId: 'agent-content-forge-1', timestamp: '2025-04-14T10:00:00', status: 'BUSY', currentTaskId: 'cf_20260514_03', queueDepth: 2, version: 'v1.3' },
  { agentId: 'agent-compliance-1', timestamp: '2025-04-14T10:00:00', status: 'IDLE', queueDepth: 0, version: 'v2.1' },
  { agentId: 'agent-publisher-1', timestamp: '2025-04-14T09:58:00', status: 'UNHEALTHY', currentTaskId: '等待平台回调', queueDepth: 5, version: 'v1.0' },
  { agentId: 'agent-pool-predictor-1', timestamp: '2025-04-14T10:00:00', status: 'IDLE', queueDepth: 0, version: 'v1.5' },
  { agentId: 'agent-trend-scout-1', timestamp: '2025-04-14T10:00:00', status: 'IDLE', queueDepth: 1, version: 'v0.8' },
  { agentId: 'agent-data-analyst-1', timestamp: '2025-04-14T10:00:00', status: 'IDLE', queueDepth: 0, version: 'v1.1' },
  { agentId: 'agent-marketing-1', timestamp: '2025-04-13T20:00:00', status: 'IDLE', queueDepth: 0, version: 'v0.5' },
];

export const mockAgentDailyMetrics: AgentDailyMetrics[] = [
  { agentId: 'agent-content-forge-1', date: '04-14', totalInvocations: 24, successCount: 22, failureCount: 1, timeoutCount: 1, humanInterventionCount: 2, taskCompletionRate: 0.917, humanInterventionRate: 0.083, avgLatencyMs: 3200, p95LatencyMs: 5800, p99LatencyMs: 7200, totalInputTokens: 48000, totalOutputTokens: 96000, estimatedCostUsd: 1.92, qualityScoreAvg: 82 },
  { agentId: 'agent-compliance-1', date: '04-14', totalInvocations: 36, successCount: 35, failureCount: 0, timeoutCount: 1, humanInterventionCount: 1, taskCompletionRate: 0.972, humanInterventionRate: 0.028, avgLatencyMs: 1200, p95LatencyMs: 2100, p99LatencyMs: 2800, totalInputTokens: 72000, totalOutputTokens: 18000, estimatedCostUsd: 0.54, qualityScoreAvg: 91 },
  { agentId: 'agent-publisher-1', date: '04-14', totalInvocations: 12, successCount: 9, failureCount: 2, timeoutCount: 1, humanInterventionCount: 3, taskCompletionRate: 0.75, humanInterventionRate: 0.25, avgLatencyMs: 8500, p95LatencyMs: 15000, p99LatencyMs: 22000, totalInputTokens: 12000, totalOutputTokens: 6000, estimatedCostUsd: 0.18, qualityScoreAvg: 78 },
  { agentId: 'agent-pool-predictor-1', date: '04-14', totalInvocations: 18, successCount: 18, failureCount: 0, timeoutCount: 0, humanInterventionCount: 0, taskCompletionRate: 1.0, humanInterventionRate: 0.0, avgLatencyMs: 450, p95LatencyMs: 800, p99LatencyMs: 1200, totalInputTokens: 9000, totalOutputTokens: 3600, estimatedCostUsd: 0.07, qualityScoreAvg: 85 },
];

export const mockAgentAlerts: AgentAlert[] = [
  { id: 'aa-1', severity: 'P1', alertType: 'TOOL_DEGRADED', agentId: 'agent-publisher-1', message: 'Publisher 平台 API 连续失败 3 次，已降级为手动发布', createdAt: '2025-04-14T09:45:00', status: 'OPEN' },
  { id: 'aa-2', severity: 'P0', alertType: 'HEALTH_CHECK_FAIL', agentId: 'agent-publisher-1', message: 'Publisher-Main 心跳缺失超过 3 个周期，状态标记为 UNHEALTHY', createdAt: '2025-04-14T09:50:00', status: 'ACKED', ackedBy: '张运营' },
  { id: 'aa-3', severity: 'P2', alertType: 'COST_ANOMALY', agentId: 'agent-content-forge-1', message: 'ContentForge-A1 单任务 Token 消耗超过同类 p95 的 200%', createdAt: '2025-04-14T08:30:00', status: 'RESOLVED', resolvedAt: '2025-04-14T09:00:00' },
];
