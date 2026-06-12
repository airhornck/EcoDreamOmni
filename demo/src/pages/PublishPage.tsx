import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Send, Clock, Calendar, CheckCircle2, AlertTriangle, Loader2, Heart, MessageCircle, Bookmark } from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ToastProvider';
import { mockContents as initialContents, mockAccounts, platformLabels, statusLabels } from '../data/mockData';
import type { ContentItem } from '../types';

export default function PublishPage() {
  const { showToast } = useToast();
  const [contents, setContents] = useState<ContentItem[]>(() => {
    const stored = JSON.parse(localStorage.getItem('demo_contents') || '[]');
    return [...initialContents, ...stored];
  });
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [confirmContent, setConfirmContent] = useState<ContentItem | null>(null);

  const approvedContents = contents.filter((c) => c.status === 'approved');
  const publishedContents = contents.filter((c) => c.status === 'published');

  const handlePublish = async (contentId: string) => {
    setPublishingId(contentId);
    await new Promise((r) => setTimeout(r, 1500));
    setContents((prev) =>
      prev.map((c) => (c.id === contentId ? { ...c, status: 'published' as const, publishedAt: new Date().toISOString() } : c))
    );
    setPublishingId(null);
    setConfirmContent(null);
    showToast('发布成功！可在「已发布」列表查看', 'success');
  };

  const getAccountName = (id?: string) => {
    if (!id) return '未指定';
    const a = mockAccounts.find((acc) => acc.id === id);
    return a ? a.nickname : id;
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <h2 className="text-2xl font-bold text-foreground tracking-tight">发布管理</h2>

      {/* Strategy hint */}
      <Card className="border-blue-200 bg-blue-50/50">
        <CardContent className="p-4 flex items-start gap-3">
          <Clock className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-blue-800">错峰调度策略</p>
            <p className="text-xs text-blue-600 mt-1">系统根据账号生命周期自动建议发布时段。冷启动期每日限发1篇，成长期3篇，成熟期5篇。</p>
          </div>
        </CardContent>
      </Card>

      {/* Ready to publish */}
      <section>
        <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
          <Send className="w-4 h-4" /> 待发布 ({approvedContents.length})
        </h3>
        {approvedContents.length === 0 ? (
          <EmptyState icon={CheckCircle2} title="暂无待发布内容" description="在任务中心审核通过的内容会出现在这里">
            <Link to="/content"><Button size="sm" variant="outline">去任务中心</Button></Link>
          </EmptyState>
        ) : (
          <Card className="divide-y divide-border">
            {approvedContents.map((c) => (
              <div key={c.id} className="px-4 py-4 flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
                  <Send className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-foreground">{c.title}</h4>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span>{platformLabels[c.platform || 'xhs']}</span>
                    <span>@{getAccountName(c.accountId)}</span>
                    {c.scheduledAt && (
                      <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> 定时: {new Date(c.scheduledAt).toLocaleString('zh-CN')}</span>
                    )}
                  </div>
                  {c.predictions && (
                    <p className="text-xs text-primary mt-1 flex items-center gap-2">
                      预演: <Heart className="w-3 h-3" /> {c.predictions.likes.median} <MessageCircle className="w-3 h-3" /> {c.predictions.comments.median} <Bookmark className="w-3 h-3" /> {c.predictions.saves.median}
                    </p>
                  )}
                </div>
                <Button size="sm" onClick={() => setConfirmContent(c)} disabled={publishingId === c.id}>
                  {publishingId === c.id ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> 发布中...</> : <><Send className="w-3.5 h-3.5" /> 立即发布</>}
                </Button>
              </div>
            ))}
          </Card>
        )}
      </section>

      {/* Published */}
      <section>
        <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> 已发布 ({publishedContents.length})
        </h3>
        <Card className="divide-y divide-border">
          {publishedContents.map((c) => (
            <div key={c.id} className="px-4 py-3 flex items-center gap-3">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusLabels[c.status].bg} ${statusLabels[c.status].color}`}>{statusLabels[c.status].text}</span>
              <span className="text-sm text-foreground flex-1 truncate">{c.title}</span>
              <span className="text-xs text-muted-foreground">{platformLabels[c.platform || 'xhs']}</span>
              <span className="text-xs text-muted-foreground">@{getAccountName(c.accountId)}</span>
              {c.actualMetrics ? (
                <span className="text-xs text-muted-foreground flex items-center gap-1"><Heart className="w-3 h-3" /> {c.actualMetrics.likes}</span>
              ) : (
                <span className="text-xs text-amber-500 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> 待回流</span>
              )}
            </div>
          ))}
        </Card>
      </section>

      {/* Confirm modal */}
      <Modal isOpen={!!confirmContent} onClose={() => setConfirmContent(null)} title="确认发布" maxWidth="sm">
        {confirmContent && (
          <div className="p-6 space-y-4">
            <p className="text-sm text-muted-foreground">确认将以下内容发布到 {platformLabels[confirmContent.platform || 'xhs']}？</p>
            <div className="bg-muted/30 rounded-lg p-3">
              <p className="text-sm font-medium text-foreground">{confirmContent.title}</p>
              <p className="text-xs text-muted-foreground mt-1">@{getAccountName(confirmContent.accountId)}</p>
            </div>
            <div className="flex gap-2">
              <Button className="flex-1" onClick={() => handlePublish(confirmContent.id)} isLoading={publishingId === confirmContent.id}>
                <Send className="w-3.5 h-3.5" /> 确认发布
              </Button>
              <Button variant="outline" className="flex-1" onClick={() => setConfirmContent(null)}>
                取消
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
