import { useState } from 'react';
import { Settings, Plus, ToggleRight, ToggleLeft, Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { mockRules } from '../data/mockData';
import type { PlatformRule } from '../types';

export default function RulesPage() {
  const [rules, setRules] = useState<PlatformRule[]>(mockRules);
  const [filterLayer, setFilterLayer] = useState<string>('all');
  const [showAdd, setShowAdd] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', condition: '', action: 'warn' as const, layer: 'l4' as const, priority: 10 });

  const filtered = rules.filter((r) => filterLayer === 'all' || r.layer === filterLayer);

  const toggleRule = (id: string) => {
    setRules((prev) => prev.map((r) => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  const addRule = () => {
    if (!newRule.name.trim()) return;
    const rule: PlatformRule = {
      id: `r-${Date.now()}`,
      name: newRule.name,
      condition: newRule.condition,
      action: newRule.action,
      layer: newRule.layer,
      priority: newRule.priority,
      enabled: true,
      version: 1,
    };
    setRules((prev) => [...prev, rule]);
    setShowAdd(false);
    setNewRule({ name: '', condition: '', action: 'warn', layer: 'l4', priority: 10 });
  };

  const layerBadge: Record<string, string> = {
    l1: 'bg-red-50 text-red-700 border-red-200',
    l2: 'bg-amber-50 text-amber-700 border-amber-200',
    l3: 'bg-blue-50 text-blue-700 border-blue-200',
    l4: 'bg-violet-50 text-violet-700 border-violet-200',
  };

  const layerNames: Record<string, string> = { l1: 'L1 法律红线', l2: 'L2 平台规则', l3: 'L3 账号策略', l4: 'L4 动态风控' };

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-foreground">规则中心</h2>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary text-sm">
          <Plus className="w-4 h-4" /> 新建规则
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Settings className="w-4 h-4 text-muted-foreground" />
        {['all', 'l1', 'l2', 'l3', 'l4'].map((l) => (
          <button key={l} onClick={() => setFilterLayer(l)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filterLayer === l ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground hover:bg-muted'
            }`}>
            {l === 'all' ? '全部' : layerNames[l]}
          </button>
        ))}
      </div>

      {/* Add rule form */}
      {showAdd && (
        <div className="bg-card rounded-xl border border-border p-5 space-y-3 animate-slide-in">
          <h3 className="text-sm font-semibold text-foreground">新建规则</h3>
          <div className="grid md:grid-cols-2 gap-3">
            <input type="text" value={newRule.name} onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
              placeholder="规则名称"
              className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
            <select value={newRule.layer} onChange={(e) => setNewRule({ ...newRule, layer: e.target.value as any })}
              className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
              {Object.entries(layerNames).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <input type="text" value={newRule.condition} onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
            placeholder="触发条件"
            className="w-full px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
          <div className="flex items-center gap-3">
            <select value={newRule.action} onChange={(e) => setNewRule({ ...newRule, action: e.target.value as any })}
              className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
              <option value="block">拦截</option>
              <option value="warn">警告</option>
              <option value="suggest">建议</option>
            </select>
            <input type="number" value={newRule.priority} onChange={(e) => setNewRule({ ...newRule, priority: Number(e.target.value) })}
              placeholder="优先级"
              className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring w-24" />
          </div>
          <div className="flex gap-2">
            <button onClick={addRule} className="btn-primary text-sm">创建</button>
            <button onClick={() => setShowAdd(false)} className="btn-outline text-sm">取消</button>
          </div>
        </div>
      )}

      {/* Rules list */}
      <div className="bg-card rounded-xl border border-border divide-y divide-border">
        {filtered.map((rule) => (
          <div key={rule.id} className="px-4 py-4 flex items-start gap-3">
            <button onClick={() => toggleRule(rule.id)} className="mt-0.5">
              {rule.enabled ? <ToggleRight className="w-5 h-5 text-emerald-500" /> : <ToggleLeft className="w-5 h-5 text-slate-300" />}
            </button>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${layerBadge[rule.layer]}`}>{layerNames[rule.layer]}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${rule.enabled ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>{rule.enabled ? '启用' : '禁用'}</span>
                <span className="text-xs text-muted-foreground">v{rule.version}</span>
              </div>
              <h3 className={`text-sm font-medium ${rule.enabled ? 'text-foreground' : 'text-muted-foreground line-through'}`}>{rule.name}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">条件: {rule.condition}</p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2 py-0.5 rounded font-medium ${
                rule.action === 'block' ? 'bg-red-50 text-red-600' :
                rule.action === 'warn' ? 'bg-amber-50 text-amber-600' :
                'bg-blue-50 text-blue-600'
              }`}>{rule.action === 'block' ? '拦截' : rule.action === 'warn' ? '警告' : '建议'}</span>
              <span className="text-muted-foreground">P{rule.priority}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
