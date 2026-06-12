import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus, Eye, Trash2, ShieldCheck, ArrowRight, Heart, MessageCircle, Bookmark,
  Layers, Bot, User, CheckCircle2, XCircle, RotateCcw, Send, Clock, Flag
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { SearchInput } from '../components/ui/SearchInput';
import { EmptyState } from '../components/ui/EmptyState';
import { Modal } from '../components/ui/Modal';
import { StatusBadge } from '../components/common/StatusBadge';
import { useToast } from '../components/ToastProvider';
import { mockContents as initialContents, stageLabels, platformLabels, mockPersonas, mockWorkflowTemplates } from '../data/mockData';
import type { ContentItem, PipelineNode } from '../types';

export default function ContentPage() {
  const { showToast } = useToast();
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterStage, setFilterStage] = useState<string>('all');
  const [contents, setContents] = useState<ContentItem[]>(() => {
    const stored = JSON.parse(localStorage.getItem('demo_contents') || '[]');
    return [...initialContents, ...stored];
  });
  const [viewContent, setViewContent] = useState<ContentItem | null>(null);

  const filtered = useMemo(() => {
    return contents.filter((c) => {
      const matchSearch = !search || c.title.toLowerCase().includes(search.toLowerCase()) || (c.taskName || '').toLowerCase().includes(search.toLowerCase());
      const matchStatus = filterStatus === 'all' || c.status === filterStatus;
      const matchStage = filterStage === 'all' || c.stage === filterStage;
      return matchSearch && matchStatus && matchStage;
    });
  }, [search, filterStatus, filterStage, contents]);

  const updateStatus = (id: string, newStatus: ContentItem['status']) => {
    setContents((prev) => prev.map((c) => (c.id === id ? { ...c, status: newStatus } : c)));
    const label = { draft: '草稿', reviewing: '审核中', approved: '已通过', published: '已发布', rejected: '已驳回' }[newStatus];
    showToast(`状态已更新为「${label}」`, 'success');
  };

  const deleteContent = (id: string) => {
    setContents((prev) => prev.filter((c) => c.id !== id));
    showToast('任务已删除', 'info');
  };

  const getStatusActions = (c: ContentItem) => {
    switch (c.status) {
      case 'draft':
        return (
          <Button size="sm" variant="secondary" onClick={() => updateStatus(c.id, 'reviewing')}>
            <ShieldCheck className="w-3 h-3" /> 提交审核
          </Button>
        );
      case 'reviewing':
        return (
          <>
            <Button size="sm" variant="secondary" onClick={() => updateStatus(c.id, 'approved')}>
              通过
            </Button>
            <Button size="sm" variant="outline" onClick={() => updateStatus(c.id, 'rejected')}>
              驳回
            </Button>
          </>
        );
      case 'approved':
        return (
          <Link to="/publish">
            <Button size="sm" variant="secondary">
              <ArrowRight className="w-3 h-3" /> 去发布
            </Button>
          </Link>
        );
      case 'rejected':
        return (
          <Button size="sm" variant="outline" onClick={() => updateStatus(c.id, 'draft')}>
            <RotateCcw className="w-3 h-3" /> 重新编辑
          </Button>
        );
      default:
        return null;
    }
  };

  const getPipelineStatus = (nodes?: PipelineNode[]) => {
    if (!nodes || nodes.length === 0) return null;
    const completed = nodes.filter((n) => n.status === 'completed').length;
    const failed = nodes.filter((n) => n.status === 'failed').length;
    return { completed, total: nodes.length, failed };
  };

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground tracking-tight">任务中心</h2>
          <p className="text-sm text-muted-foreground mt-0.5">管理内容生产任务，追踪 AI 编排进度与审核状态</p>
        </div>
        <Link to="/content/create">
          <Button><Plus className="w-4 h-4" /> 新建任务</Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={setSearch} placeholder="搜索任务或内容标题..." className="max-w-sm" />
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
          <option value="all">全部状态</option>
          <option value="draft">草稿</option>
          <option value="reviewing">审核中</option>
          <option value="approved">已通过</option>
          <option value="published">已发布</option>
          <option value="rejected">已驳回</option>
        </select>
        <select value={filterStage} onChange={(e) => setFilterStage(e.target.value)}
          className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
          <option value="all">全部阶段</option>
          <option value="AWARENESS">认知期</option>
          <option value="INTEREST">兴趣期</option>
          <option value="PURCHASE">购买期</option>
          <option value="LOYALTY">忠诚期</option>
        </select>
      </div>

      {/* Task list */}
      <Card className="divide-y divide-border">
        {filtered.map((c) => {
          const pipeline = getPipelineStatus(c.pipelineNodes);
          return (
            <div key={c.id} className="px-4 py-4 flex items-start gap-4 hover:bg-muted/40 transition-colors">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <Flag className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <StatusBadge status={c.status} />
                  <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">{stageLabels[c.stage]}</span>
                  {c.platform && <span className="text-xs text-muted-foreground">{platformLabels[c.platform]}</span>}
                  {c.workflowTemplateName && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-100">{c.workflowTemplateName}</span>
                  )}
                </div>
                <h3 className="text-sm font-medium text-foreground truncate">{c.title}</h3>
                {c.taskName && <p className="text-xs text-muted-foreground">任务: {c.taskName}</p>}
                <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{c.body}</p>

                {/* Task metadata row */}
                <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground flex-wrap">
                  <span>{new Date(c.createdAt).toLocaleDateString('zh-CN')}</span>
                  {c.accountName && <span className="flex items-center gap-1"><User className="w-3 h-3" /> {c.accountName}</span>}
                  {c.personaName && <span className="flex items-center gap-1"><Bot className="w-3 h-3" /> {c.personaName}</span>}
                  {c.predictions && (
                    <span className="text-primary flex items-center gap-1">
                      <Heart className="w-3 h-3" /> {c.predictions.likes.median}
                      <MessageCircle className="w-3 h-3" /> {c.predictions.comments.median}
                    </span>
                  )}
                  {pipeline && (
                    <span className="flex items-center gap-1">
                      <Layers className="w-3 h-3" />
                      编排 {pipeline.completed}/{pipeline.total}
                    </span>
                  )}
                  {c.tokenCostUsd && (
                    <span className="flex items-center gap-1">
                      成本 ${c.tokenCostUsd.toFixed(2)}
                    </span>
                  )}
                </div>

                {/* Review decision badge */}
                {c.reviewDecision && (
                  <div className="mt-1.5">
                    {c.reviewDecision === 'pass' ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center gap-1 inline-flex">
                        <CheckCircle2 className="w-3 h-3" /> 人工审核通过
                      </span>
                    ) : c.reviewDecision === 'reject' ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-50 text-red-600 border border-red-100 flex items-center gap-1 inline-flex">
                        <XCircle className="w-3 h-3" /> 已驳回: {c.reviewReason}
                      </span>
                    ) : (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-100 flex items-center gap-1 inline-flex">
                        <RotateCcw className="w-3 h-3" /> 打回修改
                      </span>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2 mt-2">
                  {getStatusActions(c)}
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button onClick={() => setViewContent(c)} className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-all" title="查看">
                  <Eye className="w-4 h-4" />
                </button>
                <button onClick={() => deleteContent(c.id)} className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all" title="删除">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <EmptyState icon={Flag} title="暂无任务" description="点击右上角「新建任务」开始内容生产工作流">
            <Link to="/content/create"><Button size="sm" variant="outline">去创建</Button></Link>
          </EmptyState>
        )}
      </Card>

      {/* View modal */}
      <Modal isOpen={!!viewContent} onClose={() => setViewContent(null)} title="任务详情" maxWidth="xl">
        {viewContent && (
          <div className="p-6 space-y-4">
            <div className="flex items-center gap-2">
              <StatusBadge status={viewContent.status} />
              <span className="text-xs text-muted-foreground">{stageLabels[viewContent.stage]}</span>
              {viewContent.workflowTemplateName && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">{viewContent.workflowTemplateName}</span>}
            </div>

            {/* Task context */}
            {(viewContent.taskName || viewContent.personaName || viewContent.accountName) && (
              <div className="bg-muted/30 rounded-lg p-3 space-y-1">
                {viewContent.taskName && <p className="text-xs text-muted-foreground">任务名称: <span className="text-foreground font-medium">{viewContent.taskName}</span></p>}
                {viewContent.accountName && <p className="text-xs text-muted-foreground">发布账号: <span className="text-foreground font-medium">{viewContent.accountName}</span></p>}
                {viewContent.personaName && <p className="text-xs text-muted-foreground">使用人设: <span className="text-foreground font-medium">{viewContent.personaName}</span></p>}
                {viewContent.tokenCostUsd && <p className="text-xs text-muted-foreground">Token 成本: <span className="text-foreground font-medium">${viewContent.tokenCostUsd.toFixed(3)} USD</span></p>}
              </div>
            )}

            <h3 className="text-lg font-bold text-foreground">{viewContent.title}</h3>
            <p className="text-sm text-foreground leading-relaxed">{viewContent.body}</p>
            <div className="flex flex-wrap gap-1.5">
              {viewContent.tags.map((t) => <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">{t}</span>)}
            </div>

            {/* Pipeline trace */}
            {viewContent.pipelineNodes && viewContent.pipelineNodes.length > 0 && (
              <div className="bg-muted/30 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1"><Layers className="w-3.5 h-3.5" /> AI 编排链路</h4>
                <div className="space-y-1.5">
                  {viewContent.pipelineNodes.map((n) => (
                    <div key={n.step} className="flex items-center gap-2 text-sm">
                      {n.status === 'completed' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <XCircle className="w-3.5 h-3.5 text-red-500" />}
                      <span className="text-foreground">{n.label}</span>
                      <span className="text-xs text-muted-foreground ml-auto">{n.status === 'completed' ? '已完成' : '失败'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {viewContent.predictions && (
              <div className="bg-muted/30 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">互动量预演</h4>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div><span className="text-muted-foreground">点赞</span> <span className="font-medium">{viewContent.predictions.likes.lower}-{viewContent.predictions.likes.upper}</span> <span className="text-xs text-muted-foreground">(中位数 {viewContent.predictions.likes.median})</span></div>
                  <div><span className="text-muted-foreground">评论</span> <span className="font-medium">{viewContent.predictions.comments.lower}-{viewContent.predictions.comments.upper}</span></div>
                  <div><span className="text-muted-foreground">收藏</span> <span className="font-medium">{viewContent.predictions.saves.lower}-{viewContent.predictions.saves.upper}</span></div>
                </div>
              </div>
            )}
            {viewContent.complianceResult && (
              <div className="bg-muted/30 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5" /> 合规扫描结果</h4>
                <div className="space-y-1.5">
                  {viewContent.complianceResult.layers.map((l) => (
                    <div key={l.layer} className="flex items-center gap-2 text-sm">
                      {l.passed ? <span className="text-emerald-500">✓</span> : <span className="text-red-500">✗</span>}
                      <span className="text-foreground">{l.layer}</span>
                      {l.hits && <span className="text-xs text-red-500">命中: {l.hits.join(', ')}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {viewContent.actualMetrics && (
              <div className="bg-muted/30 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">实际数据 (24h)</h4>
                <div className="flex flex-wrap gap-4 text-sm">
                  <span className="flex items-center gap-1"><Heart className="w-3.5 h-3.5 text-rose-400" /> {viewContent.actualMetrics.likes}</span>
                  <span className="flex items-center gap-1"><MessageCircle className="w-3.5 h-3.5 text-blue-400" /> {viewContent.actualMetrics.comments}</span>
                  <span className="flex items-center gap-1"><Bookmark className="w-3.5 h-3.5 text-amber-400" /> {viewContent.actualMetrics.saves}</span>
                  <span className="flex items-center gap-1">分享 {viewContent.actualMetrics.shares}</span>
                  <span className="flex items-center gap-1">曝光 {viewContent.actualMetrics.exposure}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
