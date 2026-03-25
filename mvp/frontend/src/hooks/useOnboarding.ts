'use client';

import { useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'onboarding_completed';
const STEP_KEY = 'onboarding_current_step';
const USE_CASES_KEY = 'onboarding_use_cases';

export interface UseOnboardingReturn {
  isCompleted: boolean;
  currentStep: number;
  selectedUseCases: string[];
  shouldShowWizard: boolean;
  setCurrentStep: (step: number) => void;
  setSelectedUseCases: (useCases: string[]) => void;
  toggleUseCase: (useCase: string) => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
}

export function useOnboarding(): UseOnboardingReturn {
  const [isCompleted, setIsCompleted] = useState<boolean>(true);
  const [currentStep, setCurrentStepState] = useState<number>(0);
  const [selectedUseCases, setSelectedUseCasesState] = useState<string[]>([]);
  const [hydrated, setHydrated] = useState(false);

  // Hydrate from localStorage on mount
  useEffect(() => {
    try {
      const completed = localStorage.getItem(STORAGE_KEY);
      setIsCompleted(completed === 'true');

      const savedStep = localStorage.getItem(STEP_KEY);
      if (savedStep) {
        setCurrentStepState(parseInt(savedStep, 10));
      }

      const savedUseCases = localStorage.getItem(USE_CASES_KEY);
      if (savedUseCases) {
        setSelectedUseCasesState(JSON.parse(savedUseCases));
      }
    } catch {
      // localStorage may not be available
    }
    setHydrated(true);
  }, []);

  const setCurrentStep = useCallback((step: number) => {
    setCurrentStepState(step);
    try {
      localStorage.setItem(STEP_KEY, String(step));
    } catch {
      // ignore
    }
  }, []);

  const setSelectedUseCases = useCallback((useCases: string[]) => {
    setSelectedUseCasesState(useCases);
    try {
      localStorage.setItem(USE_CASES_KEY, JSON.stringify(useCases));
    } catch {
      // ignore
    }
  }, []);

  const toggleUseCase = useCallback((useCase: string) => {
    setSelectedUseCasesState((prev) => {
      const next = prev.includes(useCase)
        ? prev.filter((uc) => uc !== useCase)
        : [...prev, useCase];
      try {
        localStorage.setItem(USE_CASES_KEY, JSON.stringify(next));
      } catch {
        // ignore
      }
      return next;
    });
  }, []);

  const completeOnboarding = useCallback(() => {
    setIsCompleted(true);
    try {
      localStorage.setItem(STORAGE_KEY, 'true');
      localStorage.removeItem(STEP_KEY);
      localStorage.removeItem(USE_CASES_KEY);
    } catch {
      // ignore
    }
  }, []);

  const resetOnboarding = useCallback(() => {
    setIsCompleted(false);
    setCurrentStepState(0);
    setSelectedUseCasesState([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(STEP_KEY);
      localStorage.removeItem(USE_CASES_KEY);
    } catch {
      // ignore
    }
  }, []);

  const shouldShowWizard = hydrated && !isCompleted;

  return {
    isCompleted,
    currentStep,
    selectedUseCases,
    shouldShowWizard,
    setCurrentStep,
    setSelectedUseCases,
    toggleUseCase,
    completeOnboarding,
    resetOnboarding,
  };
}

export default useOnboarding;
