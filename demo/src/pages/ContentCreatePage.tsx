import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlusCircle, Wand2, ShieldCheck, BarChart3, ArrowLeft, Loader2,
  Save, Send, CheckCircle2, XCircle, RotateCcw, Clock, Calendar,
  Sparkles, TrendingUp, FileText, AlertTriangle, Heart, MessageCircle,
  Bookmark, DollarSign, Zap, User, Bot, Settings, ChevronRight,
  Layers, Flag, Eye
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { PredictionResult } from '../components/common/PredictionResult';
import { ComplianceResultView } from '../components/common/ComplianceResult';
import { useToast } from '../components/ToastProvider';
import { mockAccounts, mockPersonas, mockWorkflowTemplates, stageLabels, platformLabels } from '../data/mockData';
import type { ContentItem, PredictionInterval, ComplianceResult, PipelineNode } from '../types';

type Step = 1 | 2 | 3 | 4 | 5;

const pipelineSteps = [
  { key: 'trend_scout', label: 'TrendScout 选题', agent: 'TrendScout', icon: TrendingUp },
  { key: 'content_forge', label: 'ContentForge 生成', agent: 'ContentForge', icon: Wand2 },
  { key: 'compliance_guard', label: 'ComplianceGuard 审核', agent: 'ComplianceGuard', icon: ShieldCheck },
  { key: 'pool_predictor', label: 'PoolPredictor 预演', agent: 'PoolPredictor', icon: BarChart3 },
];

export default function ContentCreatePage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [step, setStep] = useState<Step>(1);

  // Step 1: Task config
  const [taskName, setTaskName] = useState('');
  const [accountId, setAccountId] = useState('');
  const [personaId, setPersonaId] = useState('');
  const [workflowId, setWorkflowId] = useState('wf-standard');
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState('口语化');
  const [stage, setStage] = useState<'AWARENESS' | 'INTEREST' | 'PURCHASE' | 'LOYALTY'>('AWARENESS');
  const [scheduleType, setScheduleType] = useState<'immediate' | 'cron'>('immediate');
  const [cronTime, setCronTime] = useState('20:00');

  // Step 2: Pipeline
  const [pipelineNodes, setPipelineNodes] = useState<PipelineNode[]>([]);
  const [isOrchestrating, setIsOrchestrating] = useState(false);

  // Step 3: Review
  const [generated, setGenerated] = useState<ContentItem | null>(null);
  const [tokenCostUsd, setTokenCostUsd] = useState(0.12);
  const [reviewReason, setReviewReason] = useState('');

  // Step 4: Publish
  const [publishMode, setPublishMode] = useState<'now' | 'schedule'>('now');
  const [publishHour, setPublishHour] = useState(20);

  const selectedAccount = mockAccounts.find((a) => a.id === accountId);
  const selectedPersona = mockPersonas.find((p) => p.id === personaId);
  const selectedWorkflow = mockWorkflowTemplates.find((w) => w.id === workflowId);

  // Initialize pipeline nodes based on workflow
  useEffect(() => {
    if (selectedWorkflow) {
      const nodes: PipelineNode[] = selectedWorkflow.steps.map((s) => {
        const def = pipelineSteps.find((p) => p.key === s);
        return { step: s, label: def?.label || s, status: 'pending' };
      });
      setPipelineNodes(nodes);
    }
  }, [workflowId]);

  const runPipeline = async () => {
    setIsOrchestrating(true);
    const wf = selectedWorkflow!;
    const nodes = wf.steps.map((s) => {
      const def = pipelineSteps.find((p) => p.key === s);
      return { step: s, label: def?.label || s, status: 'pending' as const };
    });
    setPipelineNodes(nodes);

    // Simulate each node
    for (let i = 0; i < nodes.length; i++) {
      await new Promise((r) => setTimeout(r, 1200));
      setPipelineNodes((prev) =>
        prev.map((n, idx) =>
          idx === i ? { ...n, status: 'running', startedAt: new Date().toISOString() } :
          idx < i ? { ...n, status: 'completed' } : n
        )
      );
      await new Promise((r) => setTimeout(r, 1500));
      setPipelineNodes((prev) =>
        prev.map((n, idx) =>
          idx === i ? { ...n, status: 'completed', completedAt: new Date().toISOString() } : n
        )
      );
    }

    // Generate content after pipeline
    const titles: Record<string, string> = {
      AWARENESS: `猫咪${topic}，这3个技巧90%的人都不知道`,
      INTEREST: `${topic}深度解析：内行人才懂的选购指南`,
      PURCHASE: `亲测！${topic}真实体验分享`,
      LOYALTY: `感谢陪伴！${topic}一周年总结`,
    };
    const bodies: Record<string, string> = {
      AWARENESS: `姐妹们！今天来聊聊${topic}。很多新手铲屎官都会遇到这个问题，但其实只需要注意这3点...\n\n1. 选择合适的产品\n2. 掌握正确方法\n3. 坚持就是胜利\n\n觉得有用的话记得点赞收藏哦！`,
      INTEREST: `作为养了5年猫的资深铲屎官，今天想和大家深入聊聊${topic}...\n\n① 先看成分表\n② 再看适口性\n③ 最后比价格\n\n你们家主子最爱哪款？评论区聊聊～`,
      PURCHASE: `终于找到解决${topic}的好办法了！用了一周效果很明显...\n\n真实体验，无广分享。不过效果因猫而异，建议先咨询兽医哦。`,
      LOYALTY: `一年前的今天，我发布了第一篇关于${topic}的笔记...\n\n感谢各位铲屎官这一年的陪伴，我们会继续输出优质内容！`,
    };
    const pred: PredictionInterval = {
      likes: { lower: 15, median: 42, upper: 95 },
      comments: { lower: 2, median: 8, upper: 22 },
      saves: { lower: 5, median: 18, upper: 48 },
      intervalMode: 'prior',
      confidence: 0.65,
    };
    const hasEfficacy = topic.includes('马上') || topic.includes('三天');
    const compliance: ComplianceResult = {
      overallPassed: !hasEfficacy,
      layers: [
        { layer: 'L1', passed: !hasEfficacy, hits: hasEfficacy ? ['疗效承诺词汇'] : [] },
        { layer: 'L2', passed: true, score: 0.35 },
        { layer: 'L3', passed: true, reason: `${selectedAccount?.lifecycle || 'growth'}: ${selectedAccount?.todayPublished ?? 0}/${selectedAccount?.dailyLimit ?? 3}` },
        { layer: 'L4', passed: true, rules: [] },
      ],
      action: hasEfficacy ? 'block' : 'pass',
    };

    const content: ContentItem = {
      id: `c-task-${Date.now()}`,
      title: titles[stage],
      body: bodies[stage],
      tags: ['#' + topic.slice(0, 4), '#养猫知识', '#宠物日常'],
      images: [],
      stage,
      status: hasEfficacy ? 'rejected' : 'reviewing',
      accountId: accountId || undefined,
      accountName: selectedAccount?.nickname,
      platform: selectedAccount?.platform,
      createdAt: new Date().toISOString(),
      predictions: pred,
      complianceResult: compliance,
      taskName: taskName || `任务-${topic}`,
      personaId,
      personaName: selectedPersona?.name,
      workflowTemplateId: workflowId,
      workflowTemplateName: selectedWorkflow?.name,
      tokenCostUsd: 0.12 + Math.random() * 0.08,
      pipelineNodes: nodes.map((n) => ({ ...n, status: 'completed' })),
    };

    setGenerated(content);
    setTokenCostUsd(content.tokenCostUsd || 0.12);
    setIsOrchestrating(false);
    showToast('AI 编排完成，进入人工审核', 'info');
    setStep(3);
  };

  const handlePass = () => {
    if (!generated) return;
    const updated = { ...generated, reviewDecision: 'pass' as const, status: 'approved' as const };
    setGenerated(updated);
    showToast('审核通过，进入发布配置', 'success');
    setStep(4);
  };

  const handleReject = () => {
    if (!generated || !reviewReason.trim()) {
      showToast('请填写驳回理由', 'warning');
      return;
    }
    const updated = { ...generated, reviewDecision: 'reject' as const, reviewReason, status: 'rejected' as const };
    setGenerated(updated);
    saveToStorage(updated);
    showToast('已驳回并保存', 'info');
    setStep(5);
  };

  const handleRework = () => {
    showToast('已打回修改，请调整任务参数后重新编排', 'warning');
    setStep(1);
    setReviewReason('');
  };

  const handlePublish = async () => {
    if (!generated) return;
    const published = {
      ...generated,
      status: 'published' as const,
      publishedAt: new Date().toISOString(),
      scheduledAt: publishMode === 'schedule' ? `2025-04-14T${publishHour.toString().padStart(2, '0')}:00:00` : undefined,
    };
    saveToStorage(published);
    showToast('发布成功！', 'success');
    setStep(5);
  };

  const saveToStorage = (item: ContentItem) => {
    const stored = JSON.parse(localStorage.getItem('demo_contents') || '[]');
    stored.push(item);
    localStorage.setItem('demo_contents', JSON.stringify(stored));
  };

  const stepConfig = [
    { num: 1, label: '创建任务', icon: PlusCircle },
    { num: 2, label: 'AI编排', icon: Bot },
    { num: 3, label: '人工审核', icon: Eye },
    { num: 4, label: '发布调度', icon: Send },
    { num: 5, label: '完成', icon: CheckCircle2 },
  ];

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/content')}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h2 className="text-2xl font-bold text-foreground tracking-tight">新建任务</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            5步完成内容发布：配置 → AI编排 → 审核 → 发布 → 回流
          </p>
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-1">
        {stepConfig.map((s, i) => (
          <div key={s.num} className="flex items-center gap-1 flex-1">
            <div className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
              step >= s.num
                ? step === s.num ? 'bg-primary text-primary-foreground' : 'bg-primary/10 text-primary'
                : 'bg-muted text-muted-foreground'
            }`}>
              <s.icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{s.label}</span>
            </div>
            {i < stepConfig.length - 1 && (
              <ChevronRight className={`w-3 h-3 shrink-0 ${step > s.num ? 'text-primary' : 'text-muted-foreground'}`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Task Config */}
      {step === 1 && (
        <Card>
          <CardContent className="p-6 space-y-5">
            <div className="flex items-center gap-2 mb-2">
              <Settings className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">步骤 1：任务配置</h3>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">任务名称</label>
              <input type="text" value={taskName} onChange={(e) => setTaskName(e.target.value)}
                placeholder="例如：新手养猫误区内容生产"
                className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">选择账号（AccountPool）</label>
                <select value={accountId} onChange={(e) => setAccountId(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                  <option value="">请选择账号</option>
                  {mockAccounts.map((a) => (
                    <option key={a.id} value={a.id}>{a.nickname} ({platformLabels[a.platform]}) · {a.lifecycle === 'cold_start' ? '冷启动' : a.lifecycle === 'growth' ? '成长期' : '成熟期'} · 今日{a.todayPublished}/{a.dailyLimit}篇</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">选择人设（PersonaPool）</label>
                <select value={personaId} onChange={(e) => setPersonaId(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                  <option value="">请选择人设</option>
                  {mockPersonas.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} · {p.description}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">工作流模板</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {mockWorkflowTemplates.map((w) => (
                  <button
                    key={w.id}
                    onClick={() => setWorkflowId(w.id)}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      workflowId === w.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border bg-card hover:border-primary/30'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Layers className={`w-4 h-4 ${workflowId === w.id ? 'text-primary' : 'text-muted-foreground'}`} />
                      <span className="text-sm font-medium text-foreground">{w.name}</span>
                      {w.isLightweight && <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">轻量</span>}
                    </div>
                    <p className="text-xs text-muted-foreground">{w.description}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {w.steps.map((s) => (
                        <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">{pipelineSteps.find((p) => p.key === s)?.label || s}</span>
                      ))}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">选题 / Topic</label>
                <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)}
                  placeholder="例如：新手养猫误区"
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">风格 / Style</label>
                <select value={style} onChange={(e) => setStyle(e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                  <option value="口语化">口语化</option>
                  <option value="专业科普">专业科普</option>
                  <option value="幽默段子">幽默段子</option>
                  <option value="温暖治愈">温暖治愈</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">AIPL 阶段</label>
              <div className="flex flex-wrap gap-2">
                {Object.entries(stageLabels).map(([k, v]) => (
                  <button
                    key={k}
                    onClick={() => setStage(k as typeof stage)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      stage === k ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground hover:bg-muted'
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">
                {stage === 'AWARENESS' && '模板: Hook(痛点吸引) → Body(知识科普) → CTA(关注/收藏) → Disclaimer(合规标注)'}
                {stage === 'INTEREST' && '模板: Hook(好奇心) → Body(深度解析) → CTA(互动提问) → Disclaimer(体验声明)'}
                {stage === 'PURCHASE' && '模板: Hook(真实体验) → Body(产品细节) → CTA(购买引导) → Disclaimer(合作/体验标注)'}
                {stage === 'LOYALTY' && '模板: Hook(情感共鸣) → Body(陪伴故事) → CTA(社群互动) → Disclaimer(无)'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">执行方式</label>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                  <input type="radio" name="schedule" checked={scheduleType === 'immediate'} onChange={() => setScheduleType('immediate')} className="w-4 h-4" />
                  <Zap className="w-3.5 h-3.5 text-primary" /> 立即执行
                </label>
                <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                  <input type="radio" name="schedule" checked={scheduleType === 'cron'} onChange={() => setScheduleType('cron')} className="w-4 h-4" />
                  <Clock className="w-3.5 h-3.5 text-primary" /> 定时执行（CronHub）
                </label>
              </div>
              {scheduleType === 'cron' && (
                <div className="mt-2">
                  <input type="time" value={cronTime} onChange={(e) => setCronTime(e.target.value)}
                    className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
                  <p className="text-[10px] text-muted-foreground mt-1">系统将在指定时间自动触发任务编排</p>
                </div>
              )}
            </div>

            <Button
              onClick={() => setStep(2)}
              disabled={!accountId || !personaId || !topic.trim()}
              className="w-full"
            >
              <Bot className="w-4 h-4" /> 创建任务并启动 AI 编排
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: AI Orchestration */}
      {step === 2 && (
        <Card>
          <CardContent className="p-6 space-y-5">
            <div className="flex items-center gap-2 mb-2">
              <Bot className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">步骤 2：AI 自动编排</h3>
              <span className="text-xs text-muted-foreground ml-auto">trace_id: task-{Date.now().toString(36).slice(-6)}</span>
            </div>

            <div className="bg-muted/30 rounded-xl p-4 space-y-4">
              {pipelineNodes.map((node, idx) => {
                const def = pipelineSteps.find((p) => p.key === node.step);
                const Icon = def?.icon || Zap;
                return (
                  <div key={node.step} className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      node.status === 'completed' ? 'bg-emerald-50' :
                      node.status === 'running' ? 'bg-primary/10' :
                      node.status === 'failed' ? 'bg-red-50' :
                      'bg-muted'
                    }`}>
                      {node.status === 'completed' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> :
                       node.status === 'running' ? <Loader2 className="w-4 h-4 text-primary animate-spin" /> :
                       node.status === 'failed' ? <XCircle className="w-4 h-4 text-red-500" /> :
                       <Icon className="w-4 h-4 text-muted-foreground" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">{node.label}</span>
                        <span className={`text-xs ${
                          node.status === 'completed' ? 'text-emerald-600' :
                          node.status === 'running' ? 'text-primary' :
                          node.status === 'failed' ? 'text-red-500' :
                          'text-muted-foreground'
                        }`}>
                          {node.status === 'completed' ? '已完成' :
                           node.status === 'running' ? '执行中...' :
                           node.status === 'failed' ? '失败' :
                           '等待中'}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden mt-1.5">
                        <div className={`h-full rounded-full transition-all duration-1000 ${
                          node.status === 'completed' ? 'bg-emerald-400 w-full' :
                          node.status === 'running' ? 'bg-primary w-2/3 animate-pulse' :
                          'w-0'
                        }`} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {!isOrchestrating && pipelineNodes.every((n) => n.status === 'pending') && (
              <Button onClick={runPipeline} className="w-full">
                <Zap className="w-4 h-4" /> 开始编排
              </Button>
            )}

            {isOrchestrating && (
              <p className="text-xs text-muted-foreground text-center">
                系统正在串行调用 Agent 流水线，请稍候...
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 3: Human Review */}
      {step === 3 && generated && (
        <div className="space-y-5">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">步骤 3：人工审核台（强制节点）</h3>
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 ml-auto">双人复核</span>
          </div>

          {/* Content preview */}
          <Card>
            <CardContent className="p-5 space-y-4">
              <div className="flex items-center gap-2 mb-1">
                <FileText className="w-4 h-4 text-violet-500" />
                <span className="text-sm font-semibold text-foreground">最终内容预览</span>
              </div>
              <div className="bg-muted/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">{stageLabels[generated.stage]}</span>
                  {generated.accountName && <span className="text-xs text-muted-foreground">@{generated.accountName}</span>}
                  {generated.personaName && <span className="text-xs text-muted-foreground">· {generated.personaName}</span>}
                </div>
                <h4 className="text-base font-bold text-foreground mb-2">{generated.title}</h4>
                <p className="text-sm text-foreground whitespace-pre-line leading-relaxed">{generated.body}</p>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {generated.tags.map((t) => (
                    <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">{t}</span>
                  ))}
                </div>
              </div>

              {/* Pipeline trace */}
              <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/20 rounded-lg p-2">
                <Layers className="w-3.5 h-3.5" />
                工作流: {generated.workflowTemplateName} ·
                {generated.pipelineNodes?.map((n, i) => (
                  <span key={n.step} className="flex items-center gap-1">
                    {n.status === 'completed' ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <XCircle className="w-3 h-3 text-red-500" />}
                    {n.label}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Compliance & Prediction side by side */}
          <div className="grid md:grid-cols-2 gap-4">
            {generated.complianceResult && (
              <Card className={generated.complianceResult.overallPassed ? 'border-emerald-200' : 'border-red-200'}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <ShieldCheck className="w-4 h-4 text-primary" />
                    <span className="text-sm font-semibold text-foreground">合规扫描结果</span>
                  </div>
                  <ComplianceResultView result={generated.complianceResult} />
                </CardContent>
              </Card>
            )}
            {generated.predictions && (
              <Card className="border-amber-200 bg-amber-50/50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart3 className="w-4 h-4 text-primary" />
                    <span className="text-sm font-semibold text-foreground">互动量预演</span>
                  </div>
                  <PredictionResult result={generated.predictions} />
                </CardContent>
              </Card>
            )}
          </div>

          {/* Cost estimate */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">Token 成本预估</span>
                </div>
                <span className="text-sm font-bold text-foreground">${tokenCostUsd.toFixed(3)} USD</span>
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">
                基于 LLM Gateway 返回的 prompt_tokens / completion_tokens 结合模型单价估算，存在 ±5% 误差
              </p>
            </CardContent>
          </Card>

          {/* Review actions */}
          <Card>
            <CardContent className="p-5 space-y-4">
              <p className="text-sm font-medium text-foreground">审核操作</p>
              <div className="flex flex-wrap gap-2">
                <Button onClick={handlePass} variant="secondary" className="flex-1" disabled={!generated.complianceResult?.overallPassed}>
                  <CheckCircle2 className="w-4 h-4" /> 通过 → 发布队列
                </Button>
                <Button onClick={handleRework} variant="outline" className="flex-1">
                  <RotateCcw className="w-4 h-4" /> 打回修改
                </Button>
              </div>
              <div className="pt-2 border-t border-border">
                <label className="block text-xs text-muted-foreground mb-1.5">驳回理由（驳回时必填）</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={reviewReason}
                    onChange={(e) => setReviewReason(e.target.value)}
                    placeholder="例如：L1 风险词汇需修改"
                    className="flex-1 px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <Button variant="outline" onClick={handleReject} disabled={!reviewReason.trim()}>
                    <XCircle className="w-4 h-4" /> 驳回
                  </Button>
                </div>
              </div>
              {!generated.complianceResult?.overallPassed && (
                <p className="text-xs text-red-500 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  合规未通过，建议打回修改或手动修正后重新编排
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 4: Publish */}
      {step === 4 && generated && (
        <div className="space-y-5">
          <div className="flex items-center gap-2">
            <Send className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">步骤 4：发布与调度</h3>
          </div>

          <Card>
            <CardContent className="p-5 space-y-4">
              <div className="bg-muted/30 rounded-lg p-3">
                <p className="text-sm font-medium text-foreground">{generated.title}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                  <span>{platformLabels[generated.platform || 'xhs']}</span>
                  <span>·</span>
                  <span>@{generated.accountName}</span>
                  <span>·</span>
                  <span>{stageLabels[generated.stage]}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">发布方式</label>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                    <input type="radio" name="publish" checked={publishMode === 'now'} onChange={() => setPublishMode('now')} className="w-4 h-4" />
                    <Zap className="w-3.5 h-3.5 text-primary" /> 立即发布
                  </label>
                  <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                    <input type="radio" name="publish" checked={publishMode === 'schedule'} onChange={() => setPublishMode('schedule')} className="w-4 h-4" />
                    <Calendar className="w-3.5 h-3.5 text-primary" /> 定时发布
                  </label>
                </div>
              </div>

              {publishMode === 'schedule' && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1.5">计划发布时段</label>
                  <select value={publishHour} onChange={(e) => setPublishHour(Number(e.target.value))}
                    className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>{i.toString().padStart(2, '0')}:00</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Frequency ladder hint */}
              {selectedAccount && (
                <div className="bg-blue-50 rounded-lg border border-blue-200 p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-medium text-blue-700">频率阶梯提示</span>
                  </div>
                  <p className="text-xs text-blue-600">
                    账号「{selectedAccount.nickname}」为{selectedAccount.lifecycle === 'cold_start' ? '冷启动期' : selectedAccount.lifecycle === 'growth' ? '成长期' : '成熟期'}，
                    今日已发 {selectedAccount.todayPublished}/{selectedAccount.dailyLimit} 篇。
                    {publishMode === 'schedule' && publishHour >= 19 && publishHour <= 22
                      ? ' 选择的时段为黄金时段（19:00-22:00），竞争系数较高。'
                      : ' 建议错峰发布以提升曝光。'}
                  </p>
                </div>
              )}

              <div className="flex gap-2">
                <Button onClick={handlePublish} className="flex-1">
                  <Send className="w-4 h-4" /> {publishMode === 'now' ? '确认发布' : '确认定时'}
                </Button>
                <Button variant="outline" onClick={() => setStep(3)}>
                  返回审核
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 5: Complete */}
      {step === 5 && (
        <div className="space-y-5">
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardContent className="p-8 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="text-lg font-bold text-foreground">
                {generated?.status === 'published' ? '任务完成！内容已发布' : '任务已关闭'}
              </h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                {generated?.status === 'published'
                  ? `「${generated.title}」已成功发布到 ${platformLabels[generated.platform || 'xhs']}。`
                  : `任务「${taskName || topic}」已保存。`}
              </p>

              <div className="bg-card rounded-xl border border-border p-4 max-w-sm mx-auto text-left space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-4 h-4 text-primary" />
                  <span className="text-foreground">发布后 T+24h 数据回流</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  系统将在 24-48h 内通过 CSV 导入或连接器获取实际互动数据，
                  DataAnalyst 将自动生成区间命中率、MAPE 报告与归因分析。
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <BarChart3 className="w-3.5 h-3.5" />
                  昨日战报将展示预测区间覆盖率
                </div>
              </div>

              <div className="flex flex-wrap justify-center gap-2">
                <Button onClick={() => navigate('/content')}>
                  <Flag className="w-4 h-4" /> 去任务中心
                </Button>
                <Button variant="outline" onClick={() => navigate('/analytics')}>
                  <BarChart3 className="w-4 h-4" /> 数据分析
                </Button>
                <Button variant="outline" onClick={() => {
                  setStep(1);
                  setTaskName('');
                  setTopic('');
                  setGenerated(null);
                  setReviewReason('');
                }}>
                  <PlusCircle className="w-4 h-4" /> 再建一个任务
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
