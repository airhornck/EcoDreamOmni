import {
  Zap,
  Compass,
  Send,
  Monitor,
  CheckCircle,
} from 'lucide-react'

const STEPS = [
  { id: 0, label: '基础配置', icon: Zap },
  { id: 1, label: '主题与策略', icon: Compass },
  { id: 2, label: 'Agent 选择', icon: Send },
  { id: 3, label: '发布确认', icon: Monitor },
]

interface StepperProps {
  currentStep: number
  onStepClick: (step: number) => void
}

export function Stepper({ currentStep, onStepClick }: StepperProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {STEPS.map((step, idx) => {
        const isCompleted = idx < currentStep
        const isCurrent = idx === currentStep
        const isPending = idx > currentStep
        const Icon = step.icon
        return (
          <div key={step.id} className="flex items-center gap-2">
            <button
              onClick={() => isCompleted && onStepClick(idx)}
              disabled={isPending}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                isCurrent
                  ? 'bg-primary text-primary-foreground'
                  : isCompleted
                  ? 'bg-success/10 text-success hover:bg-success/20'
                  : 'bg-muted text-muted-foreground'
              } ${isCompleted ? 'cursor-pointer' : isPending ? 'cursor-not-allowed opacity-60' : 'cursor-default'}`}
            >
              {isCompleted ? (
                <CheckCircle className="w-3.5 h-3.5" />
              ) : (
                <Icon className="w-3.5 h-3.5" />
              )}
              {step.label}
            </button>
            {idx < STEPS.length - 1 && (
              <div
                className={`w-8 h-0.5 rounded ${
                  isCompleted ? 'bg-success' : 'bg-muted'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
