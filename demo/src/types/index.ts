export interface User {
  id: string;
  email: string;
  name: string;
  avatar: string;
  role: 'admin' | 'operator';
}

export interface Account {
  id: string;
  platform: 'xhs' | 'douyin' | 'shipinhao';
  nickname: string;
  avatar: string;
  status: 'active' | 'warming' | 'restricted' | 'banned';
  healthScore: number;
  followers: number;
  todayPublished: number;
  dailyLimit: number;
  lifecycle: 'cold_start' | 'growth' | 'mature';
  lastLogin: string;
  fingerprint: string;
}

export interface Persona {
  id: string;
  name: string;
  description: string;
  voice: string;
  avatar: string;
  accountIds: string[];
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  steps: string[];
  isLightweight: boolean;
}

export interface PipelineNode {
  step: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startedAt?: string;
  completedAt?: string;
  output?: string;
}

export interface ContentItem {
  id: string;
  title: string;
  body: string;
  tags: string[];
  images: string[];
  stage: 'AWARENESS' | 'INTEREST' | 'PURCHASE' | 'LOYALTY';
  status: 'draft' | 'reviewing' | 'approved' | 'published' | 'rejected';
  accountId?: string;
  accountName?: string;
  platform?: string;
  createdAt: string;
  publishedAt?: string;
  scheduledAt?: string;
  predictions?: PredictionInterval;
  actualMetrics?: ActualMetrics;
  complianceResult?: ComplianceResult;
  // Task context (V2.3 workflow)
  taskId?: string;
  taskName?: string;
  personaId?: string;
  personaName?: string;
  workflowTemplateId?: string;
  workflowTemplateName?: string;
  tokenCostUsd?: number;
  pipelineNodes?: PipelineNode[];
  reviewDecision?: 'pass' | 'reject' | 'rework';
  reviewReason?: string;
}

export interface PredictionInterval {
  likes: { lower: number; median: number; upper: number };
  comments: { lower: number; median: number; upper: number };
  saves: { lower: number; median: number; upper: number };
  intervalMode: 'prior' | 'fitted';
  confidence: number;
}

export interface ActualMetrics {
  likes: number;
  comments: number;
  saves: number;
  shares: number;
  follows: number;
  exposure: number;
}

export interface ComplianceResult {
  overallPassed: boolean;
  layers: { layer: string; passed: boolean; hits?: string[]; score?: number; reason?: string; rules?: string[] }[];
  action: 'pass' | 'warn' | 'block';
}

export interface TrendItem {
  id: string;
  rank: number;
  title: string;
  titleStructure: string;
  engagementHint: string;
  stage: string;
  tags: string[];
  postTime: string;
  riskLevel: number;
}

export interface PlatformRule {
  id: string;
  layer: 'l1' | 'l2' | 'l3' | 'l4';
  name: string;
  condition: string;
  action: 'block' | 'warn' | 'suggest';
  priority: number;
  enabled: boolean;
  version: number;
}

export interface Task {
  id: string;
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  type: 'generate' | 'review' | 'publish' | 'calibrate';
  createdAt: string;
  completedAt?: string;
}

export interface AlertItem {
  id: string;
  level: 'emergency' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
}

export interface DashboardOverview {
  tasksPending: number;
  briefsPending: number;
  contentsPendingReview: number;
  contentsPublished: number;
  engagementDelta: number;
  avgHealthScore: number;
}

export interface DailyReport {
  date: string;
  publishedCount: number;
  coverageRate: number;
  mape: number;
  avgLikes: number;
  avgComments: number;
  avgSaves: number;
}

// AgentHub / AgentWatch / AgentMetrics (V2.4)
export interface AgentRegistration {
  id: string;
  name: string;
  role: 'TREND_SCOUT' | 'CONTENT_FORGE' | 'COMPLIANCE_GUARD' | 'PUBLISHER' | 'DATA_ANALYST' | 'POOL_PREDICTOR' | 'MARKETING_METHODOLOGY' | 'PLATFORM_RULE' | 'ORCHESTRATOR';
  description: string;
  owner: string;
  status: 'REGISTERED' | 'ACTIVE' | 'DEGRADED' | 'PAUSED' | 'OFFLINE';
  env: 'dev' | 'staging' | 'prod';
  version: string;
  createdAt: string;
  updatedAt: string;
}

export interface AgentHeartbeat {
  agentId: string;
  timestamp: string;
  status: 'HEALTHY' | 'BUSY' | 'IDLE' | 'UNHEALTHY';
  currentTaskId?: string;
  queueDepth: number;
  memoryMb?: number;
  cpuPercent?: number;
  version: string;
}

export interface AgentDailyMetrics {
  agentId: string;
  date: string;
  totalInvocations: number;
  successCount: number;
  failureCount: number;
  timeoutCount: number;
  humanInterventionCount: number;
  taskCompletionRate: number;
  humanInterventionRate: number;
  avgLatencyMs: number;
  p95LatencyMs: number;
  p99LatencyMs: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  estimatedCostUsd: number;
  qualityScoreAvg?: number;
}

export interface AgentAlert {
  id: string;
  severity: 'P0' | 'P1' | 'P2';
  alertType: 'LOOP' | 'TIMEOUT' | 'TOOL_DEGRADED' | 'COST_ANOMALY' | 'HEALTH_CHECK_FAIL';
  agentId: string;
  traceId?: string;
  contentId?: string;
  message: string;
  createdAt: string;
  status: 'OPEN' | 'ACKED' | 'RESOLVED' | 'IGNORED';
  ackedBy?: string;
  resolvedAt?: string;
  rootCause?: string;
}
