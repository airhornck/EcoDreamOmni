import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ArrowLeft, Construction, ExternalLink } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface PlaceholderPageProps {
  title: string
  subtitle?: string
  description?: string
  relatedLinks?: Array<{ label: string; path: string }>
  icon?: LucideIcon
}

export function PlaceholderPage({
  title,
  subtitle = '功能模块',
  description = '该功能模块正在开发中，部分接口已就绪。您可以通过下方相关链接访问已实现的功能。',
  relatedLinks = [],
  icon,
}: PlaceholderPageProps) {
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        subtitle={subtitle}
        action={
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-1" />
            返回
          </Button>
        }
      />

      <Card className="p-8">
        <EmptyState
          icon={icon || Construction}
          title={`${title} 开发中`}
          description={description}
        />

        {relatedLinks.length > 0 && (
          <div className="mt-8 pt-6 border-t border-border">
            <h3 className="text-sm font-medium text-foreground mb-4">相关功能</h3>
            <div className="flex flex-wrap gap-3">
              {relatedLinks.map((link) => (
                <Button
                  key={link.path}
                  variant="secondary"
                  size="sm"
                  onClick={() => navigate(link.path)}
                >
                  {link.label}
                  <ExternalLink className="w-3.5 h-3.5 ml-1 opacity-60" />
                </Button>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
