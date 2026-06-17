import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Zap, Compass, Send, Monitor } from 'lucide-react'
import { useTaskHubStore } from '../stores/taskHubStore'
import { useStrategyStore } from '../stores/strategyStore'
import { useAICopilotStore, type PageActionCard } from '../stores/aiCopilotStore'
import { PageHeader } from '../components/common/PageHeader'
import { StepBasicConfig } from './TaskHubCreatePage/components/StepBasicConfig'
import { StepThemeStrategy } from './TaskHubCreatePage/components/StepThemeStrategy'
import { StepAgentSelect } from './TaskHubCreatePage/components/StepAgentSelect'
import { StepPublishConfirm } from './TaskHubCreatePage/components/StepPublishConfirm'
import { Stepper } from './TaskHubCreatePage/components/Stepper'
import { StepNodeCard } from './TaskHubCreatePage/components/StepNodeCard'
import { StepConnector } from './TaskHubCreatePage/components/StepConnector'
import {
  Step1Summary,
  Step2Summary,
  Step3Summary,
  Step4Summary,
} from './TaskHubCreatePage/components/StepSummary'
import { AGENT_RECOMMENDATIONS, PLATFORM_ID_LABELS } from './TaskHubCreatePage/constants'
import { fetchStrategyElementRecommendations } from '../api/strategyApi'
import { useStrategyElement } from '../hooks/useStrategyQueries'
import { showToast } from '../lib/toast'

const STEP_META = [
  { id: 0, label: '基础配置', icon: <Zap className="w-3.5 h-3.5" /> },
  { id: 1, label: '主题与策略', icon: <Compass className="w-3.5 h-3.5" /> },
  { id: 2, label: 'Agent 选择', icon: <Send className="w-3.5 h-3.5" /> },
  { id: 3, label: '发布确认', icon: <Monitor className="w-3.5 h-3.5" /> },
]

interface FormData {
  name: string
  platform: string
  contentFormat: string
  accountId: string
  personaId: string
  storyId: string
  nodeId: string
  agentId: string          // ★ v4.0 Agent-First: 替代 workflowTemplateId
  contentStrategy: string   // ★ v4.0 Strategy Element Architecture
  contentSeriesId: string
  newSeriesName: string
  scheduleMode: 'immediate' | 'scheduled' | 'cron'
  scheduledAt: string
  cronSchedule: string
  cronDateStart: string
  cronDateEnd: string
  cronTime: string
  cronMode: 'preset' | 'custom'
  priority: number
  promptVars: Record<string, string>
}

export function TaskHubCreatePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const {
    accounts,
    personas,
    personaStories,
    agents,                       // ★ v4.0 Agent-First 新增
    platformSchemas,
    fetchAccounts,
    fetchPersonas,
    fetchAgents,                  // ★ v4.0 Agent-First 新增
    fetchContentSeries,
    fetchPlatformSchemas,
    fetchPersonaStories,
    fetchPersonaStoryNodes,
    createTask,
    error: storeError,
  } = useTaskHubStore()

  const {
    currentStrategy,
    clearStrategy,
    addElementToStrategy,
  } = useStrategyStore()

  const {
    setPageActionCards,
    setQuickActions,
    setWelcomeMessage,
    setPageActionHandler,
  } = useAICopilotStore()

  const strategyElementId = searchParams.get('strategyElementId')
  const { data: seedElement, isSuccess: seedElementLoaded } = useStrategyElement(
    strategyElementId ?? '',
    !!strategyElementId
  )

  // 从策略元素页带入初始元素，仅执行一次后清理 URL
  useEffect(() => {
    if (strategyElementId && seedElementLoaded && seedElement) {
      addElementToStrategy(seedElement.element_id, { priority: 5 })
      const nextParams = new URLSearchParams(searchParams)
      nextParams.delete('strategyElementId')
      navigate({ pathname: '/generate/create', search: nextParams.toString() }, { replace: true })
    }
  }, [strategyElementId, seedElementLoaded, seedElement, addElementToStrategy, searchParams, navigate])

  // ★ 画布焦点状态：默认展开 Step 1
  const [activeStep, setActiveStep] = useState<number>(0)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [storyNodes, setStoryNodes] = useState<Array<{ id: string; theme: string; label?: string }>>([])
  const [recommendedAgentId, setRecommendedAgentId] = useState<string | null>(null)  // ★ v4.0
  const [formData, setFormData] = useState<FormData>({
    name: '',
    platform: '',
    contentFormat: '',
    accountId: '',
    personaId: '',
    storyId: '',
    nodeId: '',
    agentId: '',          // ★ v4.0 Agent-First: 替代 workflowTemplateId
    contentStrategy: '',    // ★ v4.0 Strategy Element Architecture
    contentSeriesId: '',
    newSeriesName: '',
    scheduleMode: 'immediate',
    scheduledAt: '',
    cronSchedule: '',
    cronDateStart: '',
    cronDateEnd: '',
    cronTime: '20:00',
    cronMode: 'preset',
    priority: 50,
    promptVars: {},
  })

  useEffect(() => {
    fetchAccounts()
    fetchPersonas()
    fetchAgents()          // ★ v4.0 Agent-First: 获取 Agent 列表
    fetchContentSeries()
    fetchPlatformSchemas()
  }, [fetchAccounts, fetchPersonas, fetchAgents, fetchContentSeries, fetchPlatformSchemas])

  useEffect(() => {
    if (formData.personaId) {
      fetchPersonaStories(formData.personaId)
    }
  }, [formData.personaId, fetchPersonaStories])

  useEffect(() => {
    if (formData.storyId) {
      fetchPersonaStoryNodes(formData.storyId).then((nodes) => {
        setStoryNodes(nodes)
      })
    }
  }, [formData.storyId, fetchPersonaStoryNodes])
  useEffect(() => {
    if (!formData.storyId) {
      const id = requestAnimationFrame(() => setStoryNodes([]))
      return () => cancelAnimationFrame(id)
    }
  }, [formData.storyId])

  /** ★ v4.0 Agent-First: 平台变化时重置账号、格式、Agent */
  const handlePlatformChange = (platformId: string) => {
    setFormData((prev) => ({
      ...prev,
      platform: platformId,
      accountId: '',
      contentFormat: '',
      agentId: '',
    }))
    setRecommendedAgentId(null)
    setErrors((prev) => {
      const next = { ...prev }
      delete next.platform
      delete next.accountId
      delete next.contentFormat
      delete next.agentId
      return next
    })
  }

  /** ★ v4.0 Agent-First: 内容格式变化时自动推荐 Agent */
  const handleContentFormatChange = (formatName: string) => {
    const platformId = formData.platform
    const key = `${platformId}-${formatName}`
    const recommended = AGENT_RECOMMENDATIONS[key] || null

    setFormData((prev) => ({
      ...prev,
      contentFormat: formatName,
      agentId: recommended || prev.agentId,
      promptVars: {},
    }))
    setRecommendedAgentId(recommended)
    setErrors((prev) => {
      const next = { ...prev }
      delete next.contentFormat
      delete next.agentId
      return next
    })
  }

  const updateField = <K extends keyof FormData>(key: K, value: FormData[K]) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => {
      const next = { ...prev }
      delete next[key]
      return next
    })
  }

  // Wrapper with looser types for child components
  const handleUpdateField = (key: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => {
      const next = { ...prev }
      delete next[key]
      return next
    })
  }

  const filteredAccounts = useMemo(() => {
    return accounts.filter((a) => !formData.platform || a.platform === formData.platform)
  }, [accounts, formData.platform])

  /** 当前选中的平台 Schema */
  const selectedPlatformSchema = useMemo(() => {
    return platformSchemas.find((s) => s.platform_id === formData.platform) || null
  }, [platformSchemas, formData.platform])

  /** 当前平台可用的内容格式 */
  const availableContentFormats = useMemo(() => {
    return selectedPlatformSchema?.content_formats || []
  }, [selectedPlatformSchema])

  /** 平台显示名称 */
  const platformDisplayName = useMemo(() => {
    const schema = selectedPlatformSchema
    if (schema) return schema.display_name
    return PLATFORM_ID_LABELS[formData.platform] || formData.platform
  }, [selectedPlatformSchema, formData.platform])

  /** 画布节点展开/收起 */
  const expandStep = useCallback((step: number) => {
    setActiveStep(step)
  }, [])

  const collapseStep = useCallback(() => {
    setActiveStep(-1)
  }, [])

  /** 验证表单并返回错误记录 */
  const validateForm = useCallback((): Record<string, string> => {
    const errs: Record<string, string> = {}
    if (!formData.name.trim()) errs.name = '请输入任务名称'
    if (!formData.platform) errs.platform = '请选择平台'
    if (!formData.contentFormat) errs.contentFormat = '请选择内容格式'
    if (!formData.accountId) errs.accountId = '请选择账号'
    if (!formData.agentId) errs.agentId = '请选择 Agent'
    return errs
  }, [formData])

  /** 根据当前激活节点构建 Copilot Action Cards */
  const buildCopilotCards = useCallback((): PageActionCard[] => {
    // 未聚焦任何节点
    if (activeStep < 0 || activeStep > 3) {
      return [
        {
          id: 'canvas-hint',
          type: 'info',
          title: '💡 画布提示',
          description: '点击画布中的任意节点即可展开深度配置。完成全部 4 步后可在 Copilot 中确认创建。',
          priority: 1,
        },
      ]
    }

    if (activeStep === 1) {
      const cards: PageActionCard[] = []

      // 智能推荐
      if (formData.name && formData.platform) {
        cards.push({
          id: 'strategy-recommend',
          type: 'suggestion',
          title: '🤖 智能推荐',
          description: `基于「${formData.name}」主题和「${platformDisplayName}」平台推荐策略元素`,
          priority: 3,
          actions: [{ id: 'recommend_elements', label: '获取推荐', variant: 'primary' }],
        })
      }

      return cards
    }

    if (activeStep === 0 || activeStep === 2) {
      const stepLabels = ['基础配置', '主题与策略', 'Agent 选择']
      // 导航操作已合并到 QuickActionBar，避免与 Page Action Card 重复
      return [
        {
          id: 'wizard-progress',
          type: 'info',
          title: '📝 创建向导',
          description: `当前步骤：${stepLabels[activeStep] || '配置中'}。完成全部 4 步后可在 Copilot 中确认创建。`,
          priority: 1,
        },
      ]
    }

    // Step 3: 发布确认 — 显示确认部署 Action Card
    const cards: PageActionCard[] = []

    cards.push({
      id: 'confirm-deploy',
      type: 'decision',
      title: '✅ 确认部署',
      description: [
        `任务名称：${formData.name || '（未填写）'}`,
        `平台：${platformDisplayName}`,
        `内容格式：${formData.contentFormat}`,
        `Agent：${agents.find((a) => a.id === formData.agentId)?.name || formData.agentId || '（未选择）'}`,
        `账号：${accounts.find((a) => a.id === formData.accountId)?.username || formData.accountId || '（未选择）'}`,
      ].join('\n'),
      priority: 1,
      actions: [
        { id: 'confirm_deploy', label: '确认部署', variant: 'primary' },
        { id: 'back', label: '返回修改', variant: 'secondary' },
      ],
    })

    return cards
  }, [activeStep, formData, platformDisplayName, agents, accounts, currentStrategy.elements.length])

  /** 获取 Quick Actions */
  const buildQuickActions = useCallback((): string[] => {
    const actions: string[] = []
    if (activeStep > 0) actions.push('上一步')
    if (activeStep < 3) actions.push('下一步')
    if (activeStep === 1 && formData.name && formData.platform) actions.push('获取推荐')
    if (activeStep === 1 && currentStrategy.elements.length > 0) actions.push('清空策略')
    if (activeStep === 3) actions.push('确认部署')
    actions.push('取消')
    return actions
  }, [activeStep, formData.name, formData.platform, currentStrategy.elements.length])

  /** 获取欢迎语 */
  const buildWelcomeMessage = useCallback((): string => {
    if (activeStep < 0) return '点击画布中的任意节点开始配置任务'
    if (activeStep === 0) return '配置任务基础信息，完成后进入主题与策略'
    if (activeStep === 1) return '我可基于主题推荐策略元素，或在左侧元素库中手动添加'
    if (activeStep === 2) return '已为你筛选可用 Agent，选择后进入发布确认'
    return '请检查配置信息，确认无误后点击「确认部署」'
  }, [activeStep])

  /** Copilot Action Handler */
  const handleCopilotAction = useCallback(
    async (_cardId: string, actionId: string, payload?: Record<string, unknown>) => {
      if (actionId === 'prev_step' || actionId === '上一步') {
        setActiveStep((s) => Math.max(0, s - 1))
        return
      }
      if (actionId === 'next_step' || actionId === '下一步') {
        setActiveStep((s) => Math.min(3, s + 1))
        return
      }
      if (actionId === 'cancel' || actionId === '取消') {
        navigate('/generate')
        return
      }
      if (actionId === 'clear_strategy') {
        clearStrategy()
        return
      }
      if (actionId === 'recommend_elements' || actionId === '获取推荐') {
        const topic = formData.name
        const platform = formData.platform
        console.log('[Copilot] recommend_elements clicked:', { topic, platform })
        if (!topic || !platform) {
          showToast.warning('无法获取推荐', '请先填写任务名称和选择平台')
          return
        }
        const loadingId = showToast.loading('正在获取智能推荐...')
        fetchStrategyElementRecommendations({ topic, platform, limit: 6 })
          .then((elements) => {
            console.log('[Copilot] recommend_elements received:', elements.length)
            if (elements.length === 0) {
              showToast.info('暂无推荐元素', '当前主题和平台下没有匹配的策略元素')
              return
            }
            const store = useStrategyStore.getState()
            let added = 0
            for (const el of elements) {
              if (!store.currentStrategy.elements.some((e) => e.element_id === el.element_id)) {
                store.addElementToStrategy(el.element_id, { priority: 5 })
                added++
              }
            }
            showToast.success(`已添加 ${added} 个推荐元素`, '可在策略组合面板中查看和调整优先级')
          })
          .catch((err) => {
            console.error('[Copilot] recommend_elements failed:', err)
            showToast.error('获取推荐失败', err instanceof Error ? err.message : '未知错误')
          })
          .finally(() => {
            showToast.dismiss(loadingId)
          })
        return
      }
      if (actionId === 'save_strategy_set') {
        const setName = payload?.set_name as string | undefined
        if (setName) {
          // TODO: 调用 API 保存策略组合
          console.log('保存策略组合:', setName, currentStrategy)
        }
        return
      }
      if (actionId === 'confirm' || actionId === '确认创建' || actionId === 'confirm_deploy' || actionId === '确认部署') {
        const errs = validateForm()
        if (Object.keys(errs).length > 0) {
          setErrors(errs)
          // 展开第一个有错误的节点
          if (errs.name || errs.platform || errs.contentFormat || errs.accountId) {
            setActiveStep(0)
          } else if (errs.agentId) {
            setActiveStep(2)
          }
          return
        }

        const strategyElementIds = currentStrategy.elements.map((el) => el.element_id)
        const safetyConstraintElementIds = currentStrategy.elements
          .filter((el) => el.element_type === 'safety_constraint')
          .map((el) => el.element_id)

        const taskPayload = {
          name: formData.name,
          platform: formData.platform,
          content_format: formData.contentFormat,
          account_id: formData.accountId,
          persona_id: formData.personaId || '',
          persona_story_id: formData.storyId || undefined,
          node_id: formData.nodeId || undefined,
          agent_id: formData.agentId,
          content_series_id: formData.contentSeriesId || undefined,
          scheduled_at: formData.scheduleMode === 'scheduled' ? formData.scheduledAt : undefined,
          cron_schedule: formData.scheduleMode === 'cron' ? formData.cronSchedule : undefined,
          cron_date_start: formData.scheduleMode === 'cron' && formData.cronMode === 'custom' ? formData.cronDateStart : undefined,
          cron_date_end: formData.scheduleMode === 'cron' && formData.cronMode === 'custom' ? formData.cronDateEnd : undefined,
          priority: formData.priority,
          content_strategy: formData.contentStrategy ? JSON.parse(formData.contentStrategy) : undefined,
          prompt_variables: {
            ...formData.promptVars,
            strategy_element_ids: strategyElementIds,
            safety_constraint_element_ids: safetyConstraintElementIds,
          },
        }

        const ok = await createTask(taskPayload)
        if (ok) {
          navigate('/generate')
        }
        return
      }
      if (actionId === 'back') {
        setActiveStep((s) => Math.max(0, s - 1))
        return
      }
    },
    [navigate, formData, validateForm, createTask, clearStrategy, currentStrategy],
  )

  // 使用 ref 保持 Copilot handler 引用最新，避免 useEffect 依赖循环
  const copilotHandlerRef = useRef(handleCopilotAction)
  useEffect(() => {
    copilotHandlerRef.current = handleCopilotAction
  }, [handleCopilotAction])

  /** 同步 Copilot 状态到面板 */
  useEffect(() => {
    setPageActionCards(buildCopilotCards())
    setQuickActions(buildQuickActions())
    setWelcomeMessage(buildWelcomeMessage())
    setPageActionHandler((_cardId, actionId, _payload) => {
      copilotHandlerRef.current(_cardId, actionId, _payload)
    })

    return () => {
      setPageActionCards([])
      setQuickActions([])
      setWelcomeMessage(null)
      setPageActionHandler(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeStep, formData.name, formData.platform, formData.contentFormat, formData.accountId, formData.agentId, formData.scheduleMode, recommendedAgentId, currentStrategy.elements.length])

  const selectedAccount = useMemo(
    () => accounts.find((a) => a.id === formData.accountId) || null,
    [accounts, formData.accountId],
  )
  const selectedPersona = useMemo(
    () => personas.find((p) => p.id === formData.personaId) || null,
    [personas, formData.personaId],
  )
  const selectedAgent = useMemo(
    () => agents.find((a) => a.id === formData.agentId) || null,
    [agents, formData.agentId],
  )
  const recommendedAgent = useMemo(
    () => agents.find((a) => a.id === recommendedAgentId) || null,
    [agents, recommendedAgentId],
  )

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="新建任务"
        subtitle="点击画布节点展开配置，完成全部 4 步后确认创建"
      />

      <Stepper currentStep={activeStep} onStepClick={expandStep} />

      {/* 画布区域 */}
      <div className="flex-1 min-h-0 overflow-auto relative">
        <div className="h-full overflow-x-auto overflow-y-auto">
          <div className="flex items-start justify-start min-w-max h-full px-6 py-8 gap-0">
            <StepNodeCard
              stepIndex={0}
              isActive={activeStep === 0}
              title={STEP_META[0].label}
              icon={STEP_META[0].icon}
              onActivate={() => expandStep(0)}
              onCollapse={() => collapseStep()}
              summary={
                <Step1Summary
                  name={formData.name}
                  platformDisplayName={platformDisplayName}
                  contentFormat={formData.contentFormat}
                  account={selectedAccount}
                  priority={formData.priority}
                />
              }
            >
              <StepBasicConfig
                name={formData.name}
                platform={formData.platform}
                contentFormat={formData.contentFormat}
                accountId={formData.accountId}
                priority={formData.priority}
                errors={errors}
                platformSchemas={platformSchemas}
                availableContentFormats={availableContentFormats}
                filteredAccounts={filteredAccounts}
                onPlatformChange={handlePlatformChange}
                onContentFormatChange={handleContentFormatChange}
                onUpdateField={handleUpdateField}
                onSave={() => collapseStep()}
                onCancel={() => collapseStep()}
                onClear={() => {
                  setFormData((prev) => ({
                    ...prev,
                    name: '',
                    platform: '',
                    contentFormat: '',
                    accountId: '',
                    priority: 50,
                  }))
                  setErrors({})
                  setRecommendedAgentId(null)
                }}
              />
            </StepNodeCard>

            <StepConnector />

            <StepNodeCard
              stepIndex={1}
              isActive={activeStep === 1}
              title={STEP_META[1].label}
              icon={STEP_META[1].icon}
              onActivate={() => expandStep(1)}
              onCollapse={() => collapseStep()}
              summary={
                <Step2Summary
                  persona={selectedPersona}
                  elementCount={currentStrategy.elements.length}
                  variableCount={Object.keys(currentStrategy.variables).length}
                />
              }
            >
              <StepThemeStrategy
                personaId={formData.personaId}
                storyId={formData.storyId}
                nodeId={formData.nodeId}
                platform={formData.platform}
                topic={formData.name}
                personas={personas}
                personaStories={personaStories}
                storyNodes={storyNodes}
                onUpdateField={handleUpdateField}
                onSave={() => collapseStep()}
                onCancel={() => collapseStep()}
                onClear={() => {
                  const store = useStrategyStore.getState()
                  store.clearStrategy()
                  setFormData((prev) => ({
                    ...prev,
                    personaId: '',
                    storyId: '',
                    nodeId: '',
                    contentStrategy: '',
                  }))
                  setStoryNodes([])
                }}
              />
            </StepNodeCard>

            <StepConnector />

            <StepNodeCard
              stepIndex={2}
              isActive={activeStep === 2}
              title={STEP_META[2].label}
              icon={STEP_META[2].icon}
              onActivate={() => expandStep(2)}
              onCollapse={() => collapseStep()}
              summary={
                <Step3Summary
                  agent={selectedAgent}
                  recommendedAgent={recommendedAgent}
                />
              }
            >
              <StepAgentSelect
                agents={agents}
                selectedAgentId={formData.agentId}
                recommendedAgentId={recommendedAgentId}
                platform={formData.platform}
                contentFormat={formData.contentFormat}
                safetyConstraintCount={
                  currentStrategy.elements.filter((el) => el.element_type === 'safety_constraint').length
                }
                error={errors.agentId}
                onSelect={(agentId) => {
                  updateField('agentId', agentId)
                  updateField('promptVars', {})
                }}
                onSave={() => collapseStep()}
                onClear={() => {
                  setFormData((prev) => ({
                    ...prev,
                    agentId: '',
                    promptVars: {},
                  }))
                  setRecommendedAgentId(null)
                }}
              />
            </StepNodeCard>

            <StepConnector />

            <StepNodeCard
              stepIndex={3}
              isActive={activeStep === 3}
              title={STEP_META[3].label}
              icon={STEP_META[3].icon}
              onActivate={() => expandStep(3)}
              onCollapse={() => collapseStep()}
              summary={
                <Step4Summary
                  scheduleMode={formData.scheduleMode}
                  scheduledAt={formData.scheduledAt}
                  cronSchedule={formData.cronSchedule}
                  cronDateStart={formData.cronDateStart}
                  cronDateEnd={formData.cronDateEnd}
                  cronTime={formData.cronTime}
                  cronMode={formData.cronMode}
                />
              }
            >
              <StepPublishConfirm
                name={formData.name}
                platform={formData.platform}
                contentFormat={formData.contentFormat}
                accountId={formData.accountId}
                personaId={formData.personaId}
                agentId={formData.agentId}
                priority={formData.priority}
                scheduleMode={formData.scheduleMode}
                scheduledAt={formData.scheduledAt}
                cronSchedule={formData.cronSchedule}
                cronDateStart={formData.cronDateStart}
                cronDateEnd={formData.cronDateEnd}
                cronTime={formData.cronTime}
                cronMode={formData.cronMode}
                platformDisplayName={platformDisplayName}
                accounts={accounts}
                personas={personas}
                agents={agents}
                onUpdateField={handleUpdateField}
                onSave={() => {
                  // 复用 Copilot 确认部署逻辑
                  copilotHandlerRef.current('confirm-deploy', 'confirm_deploy', {})
                }}
                onCancel={() => collapseStep()}
              />
            </StepNodeCard>
          </div>
        </div>
      </div>

      {/* Global Error */}
      {storeError && (
        <div className="mx-4 mb-4 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {storeError}
        </div>
      )}

      {/* 提示文本 */}
      <div className="flex items-center justify-center py-2 border-t border-border bg-card/50">
        <p className="text-xs text-muted-foreground">
          配置预览模式 — 请在右侧 Copilot 面板中操作或点击画布节点编辑
        </p>
      </div>
    </div>
  )
}
