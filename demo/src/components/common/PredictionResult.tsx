import { Card, CardContent } from '../ui/Card';
import { Info, Heart, MessageCircle, Bookmark, CheckCircle2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { PredictionInterval } from '../../types';

interface PredictionResultProps {
  result: PredictionInterval;
  tips?: string[];
}

export function PredictionResult({ result, tips }: PredictionResultProps) {
  const metrics = [
    { label: '点赞', icon: Heart, data: result.likes, color: 'text-rose-500' },
    { label: '评论', icon: MessageCircle, data: result.comments, color: 'text-blue-500' },
    { label: '收藏', icon: Bookmark, data: result.saves, color: 'text-amber-500' },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {metrics.map((m) => (
          <Card key={m.label} className="p-4 text-center">
            <m.icon className={cn('w-5 h-5 mx-auto mb-2', m.color)} />
            <div className="text-2xl font-bold text-foreground">{m.data.median}</div>
            <div className="text-xs text-muted-foreground mb-1">中位数</div>
            <div className="text-sm font-medium text-foreground">
              {m.data.lower} – {m.data.upper}
            </div>
            <div className="text-xs text-muted-foreground">{m.label}区间</div>
          </Card>
        ))}
      </div>

      {tips && tips.length > 0 && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Info className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-semibold text-blue-700">启发式优化清单</span>
            </div>
            <ul className="space-y-2">
              {tips.map((t, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-blue-700">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  {t}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <p className="text-xs text-muted-foreground">
        interval_mode={result.intervalMode} · 置信度 {(result.confidence * 100).toFixed(0)}%
      </p>
    </div>
  );
}
