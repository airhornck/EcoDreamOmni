import { useState } from 'react';
import { Cpu, Layers, Shield, Puzzle, Users, Zap, Search, ChevronRight } from 'lucide-react';

const skills = [
  { id: 'sk-1', name: 'content-generate', level: 'L1', desc: '基于人设与选题自动生成小红书图文', tags: ['内容生成', 'AIPL'], usage: 12480 },
  { id: 'sk-2', name: 'compliance-check', level: 'L1', desc: '四层合规扫描引擎', tags: ['合规', '风控'], usage: 34200 },
  { id: 'sk-3', name: 'fingerprint-gen', level: 'L1', desc: '浏览器设备指纹生成', tags: ['指纹', '反检测'], usage: 8900 },
  { id: 'sk-4', name: 'health-score', level: 'L1', desc: '账号健康评分计算', tags: ['账号健康'], usage: 15600 },
  { id: 'sk-5', name: 'engagement-predict', level: 'L1', desc: '互动量区间预测', tags: ['预测', '区间'], usage: 7800 },
  { id: 'sk-6', name: 'publish-schedule', level: 'L1', desc: '错峰调度发布任务', tags: ['发布', '调度'], usage: 11200 },
  { id: 'sk-7', name: 'xhs-publisher', level: 'L2', desc: '小红书平台发布器', tags: ['发布', '平台适配'], usage: 5600 },
  { id: 'sk-8', name: 'trend-analyzer', level: 'L2', desc: '趋势分析与选题建议', tags: ['趋势', '选题'], usage: 3200 },
  { id: 'sk-9', name: 'my-cat-voice', level: 'L3', desc: '用户自定义猫宠品牌Voice', tags: ['人设', 'Voice'], usage: 450 },
  { id: 'sk-10', name: 'evolved-cta-optimizer', level: 'L4', desc: 'SkillSmith进化的高转化CTA', tags: ['进化', 'CTA'], usage: 1200 },
];

const layerBadge: Record<string, string> = {
  L1: 'bg-blue-50 text-blue-700 border-blue-200',
  L2: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  L3: 'bg-amber-50 text-amber-700 border-amber-200',
  L4: 'bg-violet-50 text-violet-700 border-violet-200',
};

const agents = [
  { name: 'ContentCreator', role: '内容创作者', skills: ['content-generate', 'compliance-check', 'engagement-predict', 'xhs-publisher', 'my-cat-voice'] },
  { name: 'TrendScout', role: '趋势侦察兵', skills: ['trend-analyzer', 'health-score'] },
  { name: 'ComplianceGuard', role: '合规守卫', skills: ['compliance-check', 'fingerprint-gen'] },
  { name: 'SkillSmith', role: '技能铁匠', skills: ['evolved-cta-optimizer'] },
];

export default function SkillHubPage() {
  const [search, setSearch] = useState('');
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'skills' | 'agents'>('skills');

  const filtered = skills.filter((s) => {
    const matchSearch = !search || s.name.includes(search) || s.desc.includes(search);
    const matchLevel = filterLevel === 'all' || s.level === filterLevel;
    return matchSearch && matchLevel;
  });

  return (
    <div className="space-y-5 animate-fade-in">
      <h2 className="text-xl font-bold text-foreground">技能中枢</h2>

      {/* Layer overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { level: 'L1', title: 'Built-in', desc: '系统原生技能', icon: Shield, color: 'bg-blue-50 text-blue-600 border-blue-200' },
          { level: 'L2', title: 'Project', desc: '组织共享技能', icon: Layers, color: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
          { level: 'L3', title: 'User', desc: '用户自定义技能', icon: Users, color: 'bg-amber-50 text-amber-600 border-amber-200' },
          { level: 'L4', title: 'Evolved', desc: 'AI自进化技能', icon: Zap, color: 'bg-violet-50 text-violet-600 border-violet-200' },
        ].map((l) => (
          <div key={l.level} className={`p-4 rounded-xl border ${l.color}`}>
            <l.icon className="w-5 h-5 mb-2" />
            <div className="text-sm font-bold">{l.level} {l.title}</div>
            <div className="text-xs opacity-80">{l.desc}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-muted rounded-lg p-1 w-fit">
        <button onClick={() => setActiveTab('skills')}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${activeTab === 'skills' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
          <Puzzle className="w-3.5 h-3.5 inline mr-1" /> 技能库
        </button>
        <button onClick={() => setActiveTab('agents')}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${activeTab === 'agents' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
          <Cpu className="w-3.5 h-3.5 inline mr-1" /> Agent 绑定
        </button>
      </div>

      {activeTab === 'skills' ? (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="搜索技能..."
                className="w-full pl-9 pr-4 py-2 border border-input rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
            {['all', 'L1', 'L2', 'L3', 'L4'].map((l) => (
              <button key={l} onClick={() => setFilterLevel(l)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filterLevel === l ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground hover:bg-muted'}`}>
                {l === 'all' ? '全部' : l}
              </button>
            ))}
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            {filtered.map((s) => (
              <div key={s.id} className="bg-card rounded-xl border border-border p-4 card-hover">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${layerBadge[s.level]}`}>{s.level}</span>
                  <h3 className="text-sm font-semibold text-foreground">{s.name}</h3>
                </div>
                <p className="text-xs text-muted-foreground mb-2">{s.desc}</p>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {s.tags.map((t) => <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">{t}</span>)}
                  </div>
                  <span className="text-xs text-muted-foreground">{s.usage.toLocaleString()} 次调用</span>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="space-y-3">
          {agents.map((agent) => (
            <div key={agent.name} className="bg-card rounded-xl border border-border p-4">
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-bold text-foreground">{agent.name}</h3>
                <span className="text-xs text-muted-foreground">{agent.role}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {agent.skills.map((sk, i) => (
                  <span key={sk} className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-muted text-foreground">
                    <span className="text-muted-foreground">{i + 1}.</span> {sk}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
