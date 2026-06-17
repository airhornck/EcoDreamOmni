import { useEffect, useCallback } from 'react'
import { useAICopilotStore } from '../../stores/aiCopilotStore'
import { usePlaygroundStore } from '../../stores/playgroundStore'
import { useViralAnalyze } from '../../hooks/useViralAnalyze'
import { useViralTemplate } from '../../hooks/useViralTemplate'
import { NoteEditorZone } from '../playground/NoteEditorZone'
import { AnalysisPreviewZone } from '../playground/AnalysisPreviewZone'
import { ReportDetailZone } from '../playground/ReportDetailZone'
import { TemplatePreviewZone } from '../playground/TemplatePreviewZone'
import { Button } from '../ui/Button'
import {
  FileText,
  Sparkles,
  Loader2,
  Trash2,
  History,
  AlertTriangle,
} from 'lucide-react'

const TAB_CONFIG = [
  { key: 'edit' as const, label: '📝 笔记编辑', icon: FileText },
  { key: 'preview' as const, label: '🔍 分析预览', icon: Sparkles },
  { key: 'report' as const, label: '📋 报告详情', icon: FileText },
  { key: 'template' as const, label: '📐 模板预览', icon: Sparkles },
]

export function ViralAnalyzerCapability() {
  const {
    activeTab,
    setActiveTab,
    noteInput,
    analysisReport,
    viralTemplate,
    isAnalyzing,
    isGeneratingTemplate,
    copilotState,
    setAnalysisReport,
    setViralTemplate,
    setIsAnalyzing,
    setIsGeneratingTemplate,
    setCopilotState,
    reset,
  } = usePlaygroundStore()

  const { setContext } = useAICopilotStore()

  const analyzeMutation = useViralAnalyze()
  const templateMutation = useViralTemplate()

  // ─── Copilot Context ───
  useEffect(() => {
    setContext({
      page: '/lab',
      pageTitle: '实验室 · 爆款笔记分析',
      selectedItems: analysisReport ? [analysisReport.note_id] : [],
      selectedContent: noteInput
        ? { title: noteInput.title, content: noteInput.content.slice(0, 200), platformId: '' }
        : undefined,
    })
  }, [setContext, noteInput, analysisReport])

  // ─── Copilot Action Cards ───
  const handleAnalyze = useCallback(async () => {
    if (!noteInput) return
    setIsAnalyzing(true)
    try {
      const report = await analyzeMutation.mutateAsync(noteInput)
      setAnalysisReport(report)
    } catch (err) {
      console.error('Analyze failed:', err)
      setCopilotState('input_ready')
    } finally {
      setIsAnalyzing(false)
    }
  }, [noteInput, analyzeMutation, setAnalysisReport, setIsAnalyzing, setCopilotState])

  const handleGenerateTemplate = useCallback(async () => {
    if (!analysisReport) return
    setIsGeneratingTemplate(true)
    try {
      const template = await templateMutation.mutateAsync({
        analysis_report: analysisReport,
        template_name: `${analysisReport.structure_type}模板`,
      })
      setViralTemplate(template)
    } catch (err) {
      console.error('Template generation failed:', err)
    } finally {
      setIsGeneratingTemplate(false)
    }
  }, [analysisReport, templateMutation, setViralTemplate, setIsGeneratingTemplate])

  const handleSaveTemplate = useCallback(() => {
    if (!viralTemplate) return
    console.log('Save template:', viralTemplate.template_id)
  }, [viralTemplate])

  const handleExportTemplate = useCallback(() => {
    if (!viralTemplate) return
    const blob = new Blob([JSON.stringify(viralTemplate, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${viralTemplate.name}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [viralTemplate])

  const handleReset = useCallback(() => {
    reset()
  }, [reset])

  // ─── Render Tab Content ───
  const renderTabContent = () => {
    switch (activeTab) {
      case 'edit':
        return <NoteEditorZone />
      case 'preview':
        return <AnalysisPreviewZone report={analysisReport} isLoading={isAnalyzing} />
      case 'report':
        return <ReportDetailZone report={analysisReport} />
      case 'template':
        return <TemplatePreviewZone template={viralTemplate} />
      default:
        return null
    }
  }

  // ─── Copilot Action Cards Renderer ───
  const renderCopilotActionCards = () => {
    switch (copilotState) {
      case 'empty':
        return (
          <ActionCard icon="📤" title="粘贴笔记内容" description="支持粘贴链接、拖拽截图或直接输入正文">
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">在左侧「笔记编辑」Tab 中填写标题和正文，AI 会自动感知输入内容。</p>
            </div>
          </ActionCard>
        )

      case 'input_ready':
        return (
          <ActionCard icon="🔍" title="开始分析" description="识别结构类型、关键词匹配、情绪曲线">
            <Button
              size="sm"
              className="w-full"
              onClick={handleAnalyze}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                  分析中...
                </>
              ) : (
                '开始分析'
              )}
            </Button>
          </ActionCard>
        )

      case 'analyzing':
        return (
          <ActionCard icon="⏳" title="分析进行中" description="AI 正在解析笔记结构和爆款因子">
            <div className="space-y-2">
              <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                <div className="h-full bg-primary rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
              <p className="text-[10px] text-muted-foreground">预计耗时 3-5 秒...</p>
            </div>
          </ActionCard>
        )

      case 'analyzed':
        return (
          <>
            <ActionCard icon="📋" title="查看报告" description={`爆款评分 ${analysisReport?.viral_score} 分 · ${analysisReport?.structure_type}`}>
              <Button size="sm" variant="outline" className="w-full" onClick={() => setActiveTab('preview')}>
                切换到分析预览
              </Button>
            </ActionCard>
            <ActionCard icon="📐" title="生成模板" description="基于分析报告生成 ContentTemplate">
              <Button
                size="sm"
                className="w-full"
                onClick={handleGenerateTemplate}
                disabled={isGeneratingTemplate}
              >
                {isGeneratingTemplate ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                    生成中...
                  </>
                ) : (
                  '生成模板'
                )}
              </Button>
            </ActionCard>
          </>
        )

      case 'template_ready':
        return (
          <>
            <ActionCard icon="💾" title="保存模板" description="保存到模板库，供内容生产调用">
              <Button size="sm" className="w-full" onClick={handleSaveTemplate}>
                保存到模板库
              </Button>
            </ActionCard>
            <ActionCard icon="📥" title="导出模板" description="下载 JSON 文件">
              <Button size="sm" variant="outline" className="w-full" onClick={handleExportTemplate}>
                导出 JSON
              </Button>
            </ActionCard>
          </>
        )

      default:
        return null
    }
  }

  return (
    <div className="space-y-4">
      {/* Error banner */}
      {(analyzeMutation.error || templateMutation.error) && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          <span>{(analyzeMutation.error || templateMutation.error)?.message || '操作失败'}</span>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-secondary/50 p-1 rounded-lg w-fit">
        {TAB_CONFIG.map((tab) => {
          const isActive = activeTab === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                isActive
                  ? 'bg-primary text-white'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              }`}
            >
              <span>{tab.label.split(' ')[0]}</span>
              <span className="hidden sm:inline">{tab.label.split(' ')[1]}</span>
            </button>
          )
        })}
      </div>

      {/* Main Content: Canvas + Copilot */}
      <div className="flex gap-6 items-start">
        {/* Canvas */}
        <div className="flex-1 min-w-0">
          {renderTabContent()}
        </div>

        {/* Copilot Panel */}
        <div className="w-72 shrink-0 space-y-3">
          {/* Context Bar */}
          <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
            <p className="text-[10px] text-primary font-medium mb-1">当前上下文</p>
            <p className="text-[11px] text-muted-foreground">页面: 实验室</p>
            <p className="text-[11px] text-muted-foreground">能力: 爆款笔记分析</p>
            <p className="text-[11px] text-muted-foreground">
              状态: {copilotState === 'empty' ? '等待输入' : copilotState === 'input_ready' ? '笔记已填充' : copilotState === 'analyzing' ? '分析中' : copilotState === 'analyzed' ? '分析完成' : '模板就绪'}
            </p>
          </div>

          {/* Action Cards */}
          {renderCopilotActionCards()}

          {/* Common Canvas Actions */}
          {copilotState !== 'analyzing' && (
            <div className="flex gap-2">
              <QuickAction icon={<History className="w-3.5 h-3.5" />} label="历史记录" />
              <QuickAction icon={<Trash2 className="w-3.5 h-3.5" />} label="清空画布" onClick={handleReset} />
            </div>
          )}

          {/* AI Message */}
          {copilotState !== 'empty' && (
            <div className="flex gap-2">
              <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                <Sparkles className="w-3 h-3 text-primary" />
              </div>
              <div className="bg-secondary/50 rounded-lg rounded-tl-none px-3 py-2">
                <p className="text-xs text-foreground">
                  {copilotState === 'input_ready' && '我已检测到笔记内容。点击「开始分析」，我将为您解析结构类型、关键词匹配和爆款评分。'}
                  {copilotState === 'analyzing' && '正在分析中...已识别结构关键词，正在计算情绪曲线。'}
                  {copilotState === 'analyzed' && `分析完成！这篇笔记的结构类型是「${analysisReport?.structure_type}」，爆款评分 ${analysisReport?.viral_score} 分。`}
                  {copilotState === 'template_ready' && `模板已生成，包含 ${viralTemplate?.variables.length} 个变量。您可以保存到模板库或导出 JSON。`}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── sub-components ── */

function ActionCard({ icon, title, description, children }: {
  icon: string
  title: string
  description: string
  children?: React.ReactNode
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-3 card-hover">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <div>
          <p className="text-sm font-medium">{title}</p>
          <p className="text-[10px] text-muted-foreground">{description}</p>
        </div>
      </div>
      {children}
    </div>
  )
}

function QuickAction({ icon, label, onClick }: {
  icon: React.ReactNode
  label: string
  onClick?: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg border border-border text-[11px] text-muted-foreground hover:bg-secondary transition-colors"
    >
      {icon}
      <span>{label}</span>
    </button>
  )
}
