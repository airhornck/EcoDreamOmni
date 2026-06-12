import { usePlaygroundStore } from '../../stores/playgroundStore'
import { FileText, ChevronDown } from 'lucide-react'

const MOCK_TEMPLATES = [
  {
    id: 'tmpl_001',
    name: '驱虫种草模板',
    prompt_template:
      '作为一名{{persona}}，我发现很多铲屎官都在为{{problem}}烦恼。今天分享一个{{solution}}，我家{{pet_name}}用了{{duration}}，效果{{effect}}。',
    variables: [
      { key: 'persona', label: '人设', default_value: '省钱狗爸', current_value: '省钱狗爸' },
      { key: 'problem', label: '痛点', default_value: '狗狗驱虫贵', current_value: '狗狗驱虫贵' },
      { key: 'solution', label: '解决方案', default_value: '平价驱虫药', current_value: '平价驱虫药' },
      { key: 'pet_name', label: '宠物名', default_value: '豆豆', current_value: '豆豆' },
      { key: 'duration', label: '使用时长', default_value: '3个月', current_value: '3个月' },
      { key: 'effect', label: '效果描述', default_value: '非常好', current_value: '非常好' },
    ],
  },
  {
    id: 'tmpl_002',
    name: '测评对比模板',
    prompt_template:
      '花了{{amount}}测评了{{product_count}}款{{category}}，结果发现{{finding}}。',
    variables: [
      { key: 'amount', label: '花费', default_value: '500元', current_value: '500元' },
      { key: 'product_count', label: '产品数量', default_value: '5', current_value: '5' },
      { key: 'category', label: '品类', default_value: '驱虫药', current_value: '驱虫药' },
      { key: 'finding', label: '发现', default_value: ' cheapest 的效果最好', current_value: ' cheapest 的效果最好' },
    ],
  },
]

export function TemplateGenZone() {
  const { templates, selectedTemplateId, setTemplates, selectTemplate } = usePlaygroundStore()

  // Load mock templates on first render if empty
  if (templates.length === 0) {
    setTemplates(MOCK_TEMPLATES)
  }

  const selected = templates.find((t) => t.id === selectedTemplateId)

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-3">
      <div className="flex items-center gap-2">
        <FileText className="w-4 h-4 text-warning" />
        <h3 className="text-sm font-semibold">模板生成</h3>
      </div>

      <div className="relative">
        <select
          value={selectedTemplateId || ''}
          onChange={(e) => selectTemplate(e.target.value)}
          className="w-full appearance-none px-3 py-2 pr-8 rounded-lg bg-secondary text-sm outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">选择模板...</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
      </div>

      {selected && (
        <div className="p-2.5 rounded-lg bg-secondary text-xs leading-relaxed font-mono text-muted-foreground">
          {selected.prompt_template}
        </div>
      )}
    </div>
  )
}
