import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'ecodream_demo_onboarding_v1';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  targetSelector?: string;
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

export function useOnboarding(steps: OnboardingStep[]) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const completed = localStorage.getItem(STORAGE_KEY) === 'true';
    if (!completed) {
      const timer = setTimeout(() => setIsActive(true), 1200);
      return () => clearTimeout(timer);
    }
  }, []);

  const next = useCallback(() => {
    if (currentStep < steps.length - 1) setCurrentStep((s) => s + 1);
    else complete();
  }, [currentStep, steps.length]);

  const prev = useCallback(() => setCurrentStep((s) => Math.max(0, s - 1)), []);
  const skip = useCallback(() => { setIsActive(false); localStorage.setItem(STORAGE_KEY, 'true'); }, []);
  const complete = useCallback(() => { setIsActive(false); localStorage.setItem(STORAGE_KEY, 'true'); }, []);
  const restart = useCallback(() => { setCurrentStep(0); setIsActive(true); }, []);

  return { isActive, currentStep, step: steps[currentStep], progress: ((currentStep + 1) / steps.length) * 100, next, prev, skip, complete, restart };
}
