import { useEffect, useState } from 'react';
import { ChevronRight, ChevronLeft, X, Sparkles } from 'lucide-react';
import type { OnboardingStep } from '../hooks/useOnboarding';

interface Props {
  steps: OnboardingStep[];
  currentStep: number;
  isActive: boolean;
  progress: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
}

export default function OnboardingTour({ steps, currentStep, isActive, progress, onNext, onPrev, onSkip }: Props) {
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const step = steps[currentStep];
  const isCenter = step.placement === 'center' || !step.targetSelector;

  useEffect(() => {
    if (!isActive || !step.targetSelector) { setTargetRect(null); return; }
    const el = document.querySelector(step.targetSelector);
    if (el) setTargetRect(el.getBoundingClientRect());
    else setTargetRect(null);
  }, [isActive, currentStep, step]);

  if (!isActive) return null;

  return (
    <div className="fixed inset-0 z-[100]">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onSkip} />
      {targetRect && !isCenter && (
        <div className="absolute rounded-lg ring-2 ring-primary ring-offset-4 ring-offset-black/30 transition-all duration-500"
          style={{ top: targetRect.top - 6, left: targetRect.left - 6, width: targetRect.width + 12, height: targetRect.height + 12 }}
        />
      )}
      <div className={`absolute ${isCenter ? 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2' : ''} max-w-sm w-full animate-slide-in`}
        style={!isCenter && targetRect ? {
          top: targetRect.bottom + 14,
          left: Math.min(Math.max(targetRect.left + targetRect.width / 2 - 192, 16), window.innerWidth - 416),
        } : {}}>
        <div className="bg-white rounded-2xl shadow-2xl border border-border p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-semibold text-muted-foreground">步骤 {currentStep + 1} / {steps.length}</span>
            </div>
            <button onClick={onSkip} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
          </div>
          <div className="w-full h-1 bg-muted rounded-full mb-4 overflow-hidden">
            <div className="h-full bg-primary rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
          <h3 className="text-lg font-bold text-foreground mb-2">{step.title}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed mb-5">{step.description}</p>
          <div className="flex items-center justify-between">
            <button onClick={onPrev} disabled={currentStep === 0}
              className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-muted disabled:opacity-30 transition-all">
              <ChevronLeft className="w-4 h-4" /> 上一步
            </button>
            <div className="flex items-center gap-2">
              <button onClick={onSkip} className="px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors">跳过</button>
              <button onClick={onNext}
                className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-all">
                {currentStep === steps.length - 1 ? '完成' : '下一步'} <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
