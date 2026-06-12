import { useState } from 'react';
import { Users, Shield, Activity, Smartphone, Fingerprint, RefreshCw, AlertTriangle } from 'lucide-react';
import { mockAccounts, platformLabels, lifecycleLabels } from '../data/mockData';
import type { Account } from '../types';

export default function AccountsPage() {
  const [accounts] = useState<Account[]>(mockAccounts);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  const getStatusBadge = (status: Account['status']) => {
    const map: Record<string, { text: string; color: string; bg: string }> = {
      active: { text: '正常', color: 'text-emerald-600', bg: 'bg-emerald-50' },
      warming: { text: '养号中', color: 'text-amber-600', bg: 'bg-amber-50' },
      restricted: { text: '限流', color: 'text-red-600', bg: 'bg-red-50' },
      banned: { text: '封禁', color: 'text-slate-500', bg: 'bg-slate-100' },
    };
    return map[status] || map.active;
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <h2 className="text-xl font-bold text-foreground">账号池</h2>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((acc) => {
          const status = getStatusBadge(acc.status);
          return (
            <div key={acc.id} onClick={() => setSelectedAccount(acc)}
              className="bg-card rounded-xl border border-border p-4 cursor-pointer card-hover">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <img src={acc.avatar} alt="" className="w-10 h-10 rounded-full bg-muted" />
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">{acc.nickname}</h3>
                    <p className="text-xs text-muted-foreground">{platformLabels[acc.platform]}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${status.bg} ${status.color}`}>{status.text}</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                <div><span className="text-muted-foreground text-xs">粉丝</span> <div className="font-medium">{acc.followers.toLocaleString()}</div></div>
                <div><span className="text-muted-foreground text-xs">健康分</span> <div className={`font-medium ${getHealthColor(acc.healthScore)}`}>{acc.healthScore}</div></div>
                <div><span className="text-muted-foreground text-xs">今日发布</span> <div className="font-medium">{acc.todayPublished}/{acc.dailyLimit}</div></div>
                <div><span className="text-muted-foreground text-xs">生命周期</span> <div className="font-medium">{lifecycleLabels[acc.lifecycle]}</div></div>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Fingerprint className="w-3 h-3" />
                <span className="font-mono">{acc.fingerprint}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Account detail modal */}
      {selectedAccount && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setSelectedAccount(null)} />
          <div className="relative bg-card rounded-2xl border border-border shadow-2xl w-full max-w-md p-6 animate-slide-in">
            <div className="flex items-center gap-3 mb-4">
              <img src={selectedAccount.avatar} alt="" className="w-12 h-12 rounded-full bg-muted" />
              <div>
                <h3 className="text-base font-bold text-foreground">{selectedAccount.nickname}</h3>
                <p className="text-xs text-muted-foreground">{platformLabels[selectedAccount.platform]} · {lifecycleLabels[selectedAccount.lifecycle]}</p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">状态</span><span className={`font-medium ${getStatusBadge(selectedAccount.status).color}`}>{getStatusBadge(selectedAccount.status).text}</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">粉丝数</span><span className="font-medium">{selectedAccount.followers.toLocaleString()}</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">健康评分</span><span className={`font-medium ${getHealthColor(selectedAccount.healthScore)}`}>{selectedAccount.healthScore}/100</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">日发限额</span><span className="font-medium">{selectedAccount.todayPublished}/{selectedAccount.dailyLimit} 篇</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">最后登录</span><span className="font-medium">{selectedAccount.lastLogin}</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">设备指纹</span><span className="font-mono text-xs">{selectedAccount.fingerprint}</span></div>
            </div>
            {selectedAccount.status === 'restricted' && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                <p className="text-xs text-red-700">该账号已被平台限流，建议暂停发布并检查近期内容合规情况。</p>
              </div>
            )}
            <div className="mt-4 flex gap-2">
              <button className="btn-primary flex-1 text-sm"><RefreshCw className="w-3.5 h-3.5" /> 刷新登录态</button>
              <button onClick={() => setSelectedAccount(null)} className="btn-outline flex-1 text-sm">关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
