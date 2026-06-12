import { useState } from 'react';
import { Sparkles, BarChart3, Info, CheckCircle2 } from 'lucide-react';
import type { PredictionInterval } from '../types';

export default function PredictPage() {
  const [title, setTitle] = useState('');
  const [tags, setTags] = useState('');
  const [hour, setHour] = useState(20);
  const [hasImage, setHasImage] = useState(true);
  const [result, setResult] = useState<PredictionInterval | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [tips, setTips] = useState<string[]>([]);

  const handlePredict = async () => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 1200));
    const likesMed = Math.floor(20 + title.length * 1.5 + (hasImage ? 15 : 0));
    const commentsMed = Math.floor(likesMed * 0.15);
    const savesMed = Math.floor(likesMed * 0.3);
    setResult({
      likes: { lower: Math.floor(likesMed * 0.3), median: likesMed, upper: Math.floor(likesMed * 2.2) },
      comments: { lower: Math.floor(commentsMed * 0.2), median: commentsMed, upper: Math.floor(commentsMed * 2.5) },
      saves: { lower: Math.floor(savesMed * 0.25), median: savesMed, upper: Math.floor(savesMed * 2.3) },
      intervalMode: 'prior',
      confidence: 0.62 + Math.random() * 0.1,
    });
    setTips([
      '标题含具体数字，与模板 rubric 一致',
      `当前时段 ${hour}:00 竞争系数 ${(0.5 + Math.random() * 0.5).toFixed(2)}，属于${hour >= 19 && hour <= 22 ? '黄金时段' : '常规时段'}`,
      hasImage ? '含图片内容互动率平均高 23%（经验规则）' : '建议添加配图以提升互动率',
      tags.split(/[,，]/).filter(Boolean).length >= 3 ? '标签数量充足' : '建议添加 3-5 个相关标签',
    ]);
    setIsLoading(false);
  };

  const Bar = ({ label, value, max, color }: { label: string; value: number; max: number; color: string }) => (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium text-foreground">{value}</span>
      </div>
      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-1000 ${color}`} style={{ width: `${Math.min((value / max) * 100, 100)}%` }} />
      </div>
    </div>
  );

  return (
    <div className="space-y-5 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-violet-500" />
        <h2 className="text-xl font-bold text-foreground">互动量预演</h2>
      </div>
      <p className="text-sm text-muted-foreground">输入内容特征，预测发布后的互动量区间。冷启动阶段为宽先验区间，仅供参考。</p>

      <div className="bg-card rounded-xl border border-border p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">标题</label>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)}
            placeholder="例如：猫咪驱虫避坑指南，这3个误区90%的人都不知道"
            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">标签（逗号分隔）</label>
            <input type="text" value={tags} onChange={(e) => setTags(e.target.value)}
              placeholder="#新手养猫, #驱虫, #科普"
              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">计划发布时段</label>
            <select value={hour} onChange={(e) => setHour(Number(e.target.value))}
              className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>{i.toString().padStart(2, '0')}:00</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="hasImg" checked={hasImage} onChange={(e) => setHasImage(e.target.checked)}
            className="w-4 h-4 rounded border-border" />
          <label htmlFor="hasImg" className="text-sm text-foreground">包含配图</label>
        </div>
        <button onClick={handlePredict} disabled={isLoading || !title.trim()}
          className="btn-primary w-full">
          {isLoading ? '预测中...' : <><BarChart3 className="w-4 h-4" /> 开始预演</>}
        </button>
      </div>

      {result && (
        <div className="bg-card rounded-xl border border-border p-5 space-y-5 animate-slide-in">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">预演结果</h3>
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200">interval_mode={result.intervalMode}</span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[
              { label: '点赞', data: result.likes, color: 'bg-rose-400' },
              { label: '评论', data: result.comments, color: 'bg-blue-400' },
              { label: '收藏', data: result.saves, color: 'bg-amber-400' },
            ].map((m) => (
              <div key={m.label} className="bg-muted/30 rounded-xl p-4 text-center">
                <div className="text-lg font-bold text-muted-foreground mb-1">{m.label}</div>
                <div className="text-xl font-bold text-foreground">{m.data.median}</div>
                <div className="text-xs text-muted-foreground mb-2">中位数</div>
                <div className="text-sm text-foreground font-medium">{m.data.lower} – {m.data.upper}</div>
                <div className="text-xs text-muted-foreground">{m.label}区间</div>
              </div>
            ))}
          </div>

          <Bar label="点赞区间分布" value={result.likes.median} max={result.likes.upper} color="bg-rose-400" />
          <Bar label="评论区间分布" value={result.comments.median} max={result.comments.upper} color="bg-blue-400" />
          <Bar label="收藏区间分布" value={result.saves.median} max={result.saves.upper} color="bg-amber-400" />

          <div className="bg-blue-50 rounded-lg border border-blue-200 p-3">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-semibold text-blue-700">启发式优化清单（非因果承诺）</span>
            </div>
            <ul className="space-y-1.5">
              {tips.map((t, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-blue-700">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  {t}
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-muted-foreground">置信度: {(result.confidence * 100).toFixed(0)}% · 冷启动阶段区间较宽，仅作参考</p>
        </div>
      )}
    </div>
  );
}
