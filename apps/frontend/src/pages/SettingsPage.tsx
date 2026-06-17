import { useState } from 'react'
import { usePageCopilot } from '../hooks/usePageCopilot'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Settings, Key, Bell, Shield, Save } from 'lucide-react'

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'general' | 'api' | 'notifications' | 'security'>('general')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  usePageCopilot(
    [
      {
        id: 'settings-general',
        type: 'info',
        title: '⚙️ 通用设置',
        description: '配置平台名称、默认平台与时区',
        priority: 1,
        actions: [{ id: 'tab_general', label: '查看', variant: 'secondary' }],
      },
      {
        id: 'settings-api',
        type: 'info',
        title: '🔑 API 配置',
        description: '设置 API 基地址与请求超时',
        priority: 2,
        actions: [{ id: 'tab_api', label: '查看', variant: 'secondary' }],
      },
      {
        id: 'settings-notify',
        type: 'info',
        title: '🔔 通知开关',
        description: '管理发布、合规、Agent 等消息通知',
        priority: 3,
        actions: [{ id: 'tab_notifications', label: '查看', variant: 'secondary' }],
      },
      {
        id: 'settings-security',
        type: 'info',
        title: '🛡️ 安全设置',
        description: '访问控制与密码策略',
        priority: 4,
        actions: [{ id: 'tab_security', label: '查看', variant: 'secondary' }],
      },
      {
        id: 'settings-save',
        type: 'decision',
        title: '💾 保存当前配置',
        description: '保存当前 Tab 下的设置项',
        priority: 5,
        actions: [{ id: 'save', label: '保存', variant: 'primary' }],
      },
    ],
    async (_cardId, actionId) => {
      if (actionId === 'tab_general') setActiveTab('general')
      else if (actionId === 'tab_api') setActiveTab('api')
      else if (actionId === 'tab_notifications') setActiveTab('notifications')
      else if (actionId === 'tab_security') setActiveTab('security')
      else if (actionId === 'save') handleSave()
    }
  )

  return (
    <div className="space-y-6">
      <PageHeader
        title="系统设置"
        subtitle="平台全局配置与个性化选项"
      />

      <div className="flex gap-1 bg-secondary rounded-lg p-0.5 w-fit">
        {([
          { key: 'general' as const, label: '通用', icon: Settings },
          { key: 'api' as const, label: 'API', icon: Key },
          { key: 'notifications' as const, label: '通知', icon: Bell },
          { key: 'security' as const, label: '安全', icon: Shield },
        ]).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === tab.key ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <tab.icon className="w-3.5 h-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'general' && (
        <Card>
          <CardHeader className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold">通用设置</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">平台名称</label>
              <input
                type="text" defaultValue="EcoDreamOmni"
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">默认平台</label>
              <select className="h-10 px-3 rounded-lg border border-border bg-background text-sm">
                <option value="xhs">小红书</option>
                <option value="douyin">抖音</option>
                <option value="wechat_channels">视频号</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">时区</label>
              <select className="h-10 px-3 rounded-lg border border-border bg-background text-sm">
                <option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</option>
                <option value="UTC">UTC</option>
              </select>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSave}>
                <Save className="w-4 h-4" />
                {saved ? '已保存' : '保存'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'api' && (
        <Card>
          <CardHeader className="flex items-center gap-2">
            <Key className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold">API 配置</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">API 基地址</label>
              <input
                type="text" defaultValue="/api"
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">请求超时（秒）</label>
              <input
                type="number" defaultValue={30}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSave}>
                <Save className="w-4 h-4" />
                {saved ? '已保存' : '保存'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'notifications' && (
        <Card>
          <CardHeader className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold">通知设置</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: '发布成功通知', defaultChecked: true },
              { label: '合规拦截告警', defaultChecked: true },
              { label: '发布失败告警', defaultChecked: true },
              { label: '每日数据报表', defaultChecked: false },
              { label: 'Agent 离线告警', defaultChecked: true },
            ].map((item) => (
              <label key={item.label} className="flex items-center justify-between p-3 rounded-lg border border-border bg-secondary/20 cursor-pointer">
                <span className="text-sm text-foreground">{item.label}</span>
                <input type="checkbox" defaultChecked={item.defaultChecked} className="w-4 h-4" />
              </label>
            ))}
            <div className="flex justify-end">
              <Button onClick={handleSave}>
                <Save className="w-4 h-4" />
                {saved ? '已保存' : '保存'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'security' && (
        <Card>
          <CardHeader className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold">安全设置</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">当前密码</label>
              <input
                type="password" placeholder="输入当前密码"
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">新密码</label>
              <input
                type="password" placeholder="输入新密码"
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">确认新密码</label>
              <input
                type="password" placeholder="再次输入新密码"
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-secondary/20">
              <span className="text-sm text-foreground">启用双因素认证 (MFA)</span>
              <Badge variant="default">开发中</Badge>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSave}>
                <Save className="w-4 h-4" />
                {saved ? '已保存' : '保存'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
