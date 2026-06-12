import { Card, CardContent } from '../ui/Card';
import { ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';
import type { ComplianceResult as ComplianceResultType } from '../../types';

interface ComplianceResultProps {
  result: ComplianceResultType;
}

export function ComplianceResultView({ result }: ComplianceResultProps) {
  return (
    <Card className={result.overallPassed ? 'border-emerald-200' : 'border-red-200'}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          {result.overallPassed ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          ) : (
            <XCircle className="w-5 h-5 text-red-500" />
          )}
          <span className={`text-sm font-semibold ${result.overallPassed ? 'text-emerald-700' : 'text-red-700'}`}>
            {result.overallPassed ? '合规检测通过' : '合规检测未通过'}
          </span>
        </div>
        <div className="space-y-1.5">
          {result.layers.map((l) => (
            <div key={l.layer} className="flex items-center gap-2 text-sm">
              {l.passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-red-400 shrink-0" />
              )}
              <span className="text-foreground font-medium w-8">{l.layer}</span>
              {l.hits && l.hits.length > 0 && (
                <span className="text-xs text-red-500">命中: {l.hits.join(', ')}</span>
              )}
              {l.score !== undefined && (
                <span className="text-xs text-muted-foreground">评分: {l.score}</span>
              )}
              {l.reason && (
                <span className="text-xs text-muted-foreground">{l.reason}</span>
              )}
            </div>
          ))}
        </div>
        <p className="text-xs font-medium mt-3 text-muted-foreground">
          动作: <span className="text-foreground">{result.action}</span>
        </p>
      </CardContent>
    </Card>
  );
}
