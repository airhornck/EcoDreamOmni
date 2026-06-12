import { useState } from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, FileText, Search } from 'lucide-react';
import { mockContents } from '../data/mockData';

export default function CompliancePage() {
  const [search, setSearch] = useState('');
  const contentsWithCompliance = mockContents.filter((c) => c.complianceResult);
  const filtered = contentsWithCompliance.filter((c) => !search || c.title.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6 animate-fade-in">
      <h2 className="text-xl font-bold text-foreground">合规中心</h2>

      {/* Compliance summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: '已审核', value: contentsWithCompliance.length, icon: ShieldCheck, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: '通过', value: contentsWithCompliance.filter((c) => c.complianceResult?.overallPassed).length, icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { label: '拦截', value: contentsWithCompliance.filter((c) => !c.complianceResult?.overallPassed).length, icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
          { label: '今日扫描', value: 12, icon: FileText, color: 'text-violet-600', bg: 'bg-violet-50' },
        ].map((s) => (
          <div key={s.label} className={`p-4 rounded-xl border text-center ${s.bg} border-${s.color.split('-')[1]}-200`}>
            <s.icon className={`w-5 h-5 mx-auto mb-1 ${s.color}`} />
            <div className="text-xl font-bold text-foreground">{s.value}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Layer explanation */}
      <div className="bg-card rounded-xl border border-border p-5">
        <h3 className="section-title">四层合规扫描</h3>
        <div className="grid md:grid-cols-4 gap-3">
          {[
            { layer: 'L1', name: '法律红线', desc: '处方药、诊断、治疗承诺关键词拦截', color: 'bg-red-50 border-red-200 text-red-700' },
            { layer: 'L2', name: '平台规则', desc: '敏感词语义模型评分，>0.7 触发警告', color: 'bg-amber-50 border-amber-200 text-amber-700' },
            { layer: 'L3', name: '账号策略', desc: '频率阶梯校验：冷启动1篇/日，成长3篇/日', color: 'bg-blue-50 border-blue-200 text-blue-700' },
            { layer: 'L4', name: '动态风控', desc: '节日临时策略、时段竞争系数、自定义规则', color: 'bg-violet-50 border-violet-200 text-violet-700' },
          ].map((l) => (
            <div key={l.layer} className={`p-3 rounded-xl border ${l.color}`}>
              <span className="text-xs font-bold">{l.layer}</span>
              <p className="text-sm font-medium mt-1">{l.name}</p>
              <p className="text-xs opacity-80 mt-0.5">{l.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Audit records */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="section-title">审核记录</h3>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索内容..."
              className="pl-9 pr-4 py-1.5 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
          </div>
        </div>
        <div className="bg-card rounded-xl border border-border divide-y divide-border">
          {filtered.map((c) => (
            <div key={c.id} className="px-4 py-4">
              <div className="flex items-center gap-2 mb-2">
                {c.complianceResult!.overallPassed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-xs font-medium ${c.complianceResult!.overallPassed ? 'text-emerald-600' : 'text-red-600'}`}>
                  {c.complianceResult!.overallPassed ? '通过' : '拦截'}
                </span>
                <span className="text-sm text-foreground flex-1 truncate">{c.title}</span>
              </div>
              <div className="ml-6 space-y-1.5">
                {c.complianceResult!.layers.map((l) => (
                  <div key={l.layer} className="flex items-center gap-2 text-xs">
                    {l.passed ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <AlertTriangle className="w-3 h-3 text-red-400" />}
                    <span className="text-muted-foreground">{l.layer}</span>
                    {l.hits && l.hits.length > 0 && <span className="text-red-500">命中: {l.hits.join(', ')}</span>}
                    {l.score !== undefined && <span className="text-muted-foreground">评分: {l.score}</span>}
                    {l.reason && <span className="text-muted-foreground">{l.reason}</span>}
                  </div>
                ))}
              </div>
              <p className="ml-6 text-xs text-muted-foreground mt-1.5">动作: {c.complianceResult!.action} · 不可变记录</p>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="p-8 text-center text-sm text-muted-foreground">暂无审核记录</div>
          )}
        </div>
      </div>
    </div>
  );
}
