import { create } from "zustand";
import { persist } from "zustand/middleware";

export type CopilotStatus =
  | "idle"
  | "thinking"
  | "streaming"
  | "completed"
  | "error";

export interface CopilotMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  actionCard?: ActionCard;
}

export interface ActionCard {
  id: string;
  type: "DIFF" | "CONFIRM" | "MULTI_SELECT" | "INFO";
  title: string;
  description?: string;
  diff?: { before: string; after: string };
  options?: { label: string; value: string }[];
}

/**
 * Copilot-Driven 页面级 Action Card — v4.0 Step 3
 * 由页面组件动态注入，渲染在 Copilot Panel 的 Action Card 区域
 */
export interface PageActionCard {
  id: string;
  type: "decision" | "generation" | "suggestion" | "info";
  title: string;
  description: string;
  priority?: number;
  inputs?: Array<{
    name: string;
    label: string;
    type: string;
    placeholder?: string;
  }>;
  actions?: Array<{
    id: string;
    label: string;
    variant: "primary" | "secondary" | "ghost";
    needs_reason?: boolean;
  }>;
}

/**
 * Copilot 上下文 — 对齐设计规范 §5.3
 */
export interface CopilotContext {
  page?: string; // 当前页面路由
  pageTitle?: string; // 当前页面标题
  selectedItems?: string[]; // 选中的内容/任务 ID
  selectedContent?: {
    // 选中的内容摘要
    title: string;
    content?: string;
    platformId?: string;
  };
  activeTask?: string; // 当前活跃任务
}

export type PageActionHandler = (
  cardId: string,
  actionId: string,
  payload?: Record<string, unknown>,
) => void | Promise<void>;

interface AICopilotState {
  isOpen: boolean;
  status: CopilotStatus;
  messages: CopilotMessage[];
  context: CopilotContext;
  error: string | null;
  welcomeMessage: string | null;
  quickActions: string[];
  pageActionCards: PageActionCard[];
  pageActionHandler: PageActionHandler | null;

  toggle: () => void;
  open: () => void;
  close: () => void;
  setStatus: (status: CopilotStatus) => void;
  addMessage: (msg: CopilotMessage) => void;
  updateMessage: (
    id: string,
    updater: (msg: CopilotMessage) => CopilotMessage,
  ) => void;
  setContext: (ctx: Partial<CopilotContext>) => void;
  setError: (error: string | null) => void;
  setWelcomeMessage: (msg: string | null) => void;
  setQuickActions: (actions: string[]) => void;
  clearMessages: () => void;
  applyActionCard: (
    messageId: string,
    action: string,
    payload?: unknown,
  ) => void;
  setPageActionCards: (cards: PageActionCard[]) => void;
  setPageActionHandler: (handler: PageActionHandler | null) => void;
  setMessages: (messages: CopilotMessage[]) => void;
}

export const useAICopilotStore = create<AICopilotState>()(
  persist(
    (set) => ({
      isOpen: true,
      status: "idle",
      messages: [],
      context: {},
      error: null,
      welcomeMessage: null,
      quickActions: [
        "为@省钱狗爸生成驱虫内容",
        "分析最近7天爆款趋势",
        "优化这条文案的标题",
        "检查合规风险",
      ],
      pageActionCards: [],
      pageActionHandler: null,

      toggle: () => set((s) => ({ isOpen: !s.isOpen })),
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      setStatus: (status) => set({ status }),
      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      updateMessage: (id, updater) =>
        set((s) => ({
          messages: s.messages.map((m) => (m.id === id ? updater(m) : m)),
        })),
      setContext: (ctx) => set((s) => ({ context: { ...s.context, ...ctx } })),
      setError: (error) => set({ error }),
      setWelcomeMessage: (msg) => set({ welcomeMessage: msg }),
      setQuickActions: (actions) => set({ quickActions: actions }),
      clearMessages: () => set({ messages: [], status: "idle", error: null, welcomeMessage: null }),

      applyActionCard: (messageId, action, payload) => {
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === messageId ? { ...m, actionCard: undefined } : m,
          ),
        }));
        console.log("Action card applied:", { messageId, action, payload });
      },

      setPageActionCards: (cards) => set({ pageActionCards: cards }),
      setPageActionHandler: (handler) => set({ pageActionHandler: handler }),
      setMessages: (messages) => set({ messages }),
    }),
    {
      name: "ai-copilot-store",
      partialize: (state) => ({ isOpen: state.isOpen }),
    },
  ),
);
