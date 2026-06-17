import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserCircle, Camera, Save, ArrowLeft } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { useAuthStore } from '../stores/authStore'

const AVATAR_PRESETS = [
  'https://api.dicebear.com/7.x/notionists/svg?seed=cat',
  'https://api.dicebear.com/7.x/notionists/svg?seed=dog',
  'https://api.dicebear.com/7.x/notionists/svg?seed=pet',
  'https://api.dicebear.com/7.x/notionists/svg?seed=eco',
]

export function ProfilePage() {
  const navigate = useNavigate()
  const { user, updateUser } = useAuthStore()

  const [nickname, setNickname] = useState(user?.username ?? '')
  const [avatar, setAvatar] = useState(
    user?.avatar ?? AVATAR_PRESETS[0],
  )
  const [remark, setRemark] = useState(user?.remark ?? '')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    updateUser({
      username: nickname.trim() || user?.username || '用户',
      avatar: avatar.trim(),
      remark: remark.trim(),
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <PageHeader
        title="个人信息"
        subtitle="查看并编辑你的基础资料"
        action={
          <Button variant="secondary" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4" />
            返回
          </Button>
        }
      />

      <Card>
        <CardHeader className="flex items-center gap-2">
          <UserCircle className="w-4 h-4 text-primary" />
          <h3 className="text-base font-semibold">基础信息</h3>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 头像 */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              头像
            </label>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 overflow-hidden border border-border flex items-center justify-center">
                {avatar ? (
                  <img
                    src={avatar}
                    alt="avatar"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <Camera className="w-6 h-6 text-primary" />
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {AVATAR_PRESETS.map((url) => (
                  <button
                    key={url}
                    type="button"
                    onClick={() => setAvatar(url)}
                    className={`w-10 h-10 rounded-full overflow-hidden border-2 transition-colors ${
                      avatar === url ? 'border-primary' : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <img src={url} alt="preset" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>
            <input
              type="text"
              value={avatar}
              onChange={(e) => setAvatar(e.target.value)}
              placeholder="或输入头像图片 URL"
              className="mt-3 w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            />
          </div>

          {/* 昵称 */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              昵称
            </label>
            <input
              type="text"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="输入昵称"
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            />
          </div>

          {/* 备注 */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              备注
            </label>
            <textarea
              value={remark}
              onChange={(e) => setRemark(e.target.value)}
              placeholder="写点什么介绍自己…"
              rows={4}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            {saved && (
              <span className="text-sm text-success">资料已保存</span>
            )}
            <div className="ml-auto">
              <Button onClick={handleSave}>
                <Save className="w-4 h-4" />
                {saved ? '已保存' : '保存'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
