import { useState } from 'react';
import { TrendingUp, Search, Flame, AlertTriangle, Wand2, Sparkles } from 'lucide-react';
import { mockTrends, stageLabels } from '../data/mockData';
import { useNavigate } from 'react-router-dom';

export default function TrendsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [filterStage, setFilterStage] = useState<string>('all');

  const filtered = mockTrends.filter((t) => {
    const matchSearch = !search || t.title.toLowerCase().includes(search.toLowerCase());
    const matchStage = filterStage === 'all' || t.stage === filterStage;
    return matchSearch && matchStage;
  });

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-foreground">趋势侦察</h2>
      </div>

      <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 flex items-start gap-3">
        <Flame className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-amber-800">数据来源说明</p>
          <p className="text-xs text-amber-600 mt-1">当前展示 Mock 数据源 + 手动导入的热点数据。真实爬取为 Phase 2+ 可选能力，须单独法务评审。</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索热点话题..."
            className="w-full pl-9 pr-4 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
        </div>
        <select value={filterStage} onChange={(e) => setFilterStage(e.target.value)}
          className="px-3 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
          <option value="all">全部阶段</option>
          {Object.entries(stageLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      {/* Trend list */}
      <div className="space-y-3">
        {filtered.map((t) => (
          <div key={t.id} className="bg-card rounded-xl border border-border p-4 card-hover">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                  t.rank <= 3 ? 'bg-amber-50 text-amber-600' : 'bg-muted text-muted-foreground'
                }`}>
                  {t.rank}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">{t.title}</h3>
                  <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                    <span className="px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">{stageLabels[t.stage]}</span>
                    <span>结构: {t.titleStructure}</span>
                    <span>互动: {t.engagementHint}</span>
                    <span>{t.postTime}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {t.tags.map((tag) => (
                      <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">{tag}</span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="flex flex-col items-end gap-1">
                  {t.riskLevel > 0.3 && (
                    <span className="flex items-center gap-1 text-xs text-red-500">
                      <AlertTriangle className="w-3 h-3" /> 风险 {Math.round(t.riskLevel * 100)}%
                    </span>
                  )}
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${t.riskLevel > 0.25 ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
                    审核{t.riskLevel > 0.25 ? '较严' : '正常'}
                  </span>
                </div>
                <button onClick={() => navigate('/content/create')}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-primary/10 text-primary hover:bg-primary/20 transition-all">
                  <Sparkles className="w-3 h-3" /> 一键生成
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
