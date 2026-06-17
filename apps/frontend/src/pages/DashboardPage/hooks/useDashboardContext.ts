import { useEffect } from "react";
import { useAICopilotStore } from "../../../stores/aiCopilotStore";
import { apiClient } from "../../../lib/api";
import { resolveNavigateAction } from "../../../lib/copilotCapabilities";

export interface DashboardActionHandler {
  navigate: (path: string) => void;
}

export function useDashboardContext(
  handler?: DashboardActionHandler,
  selectedContentId?: string,
  selectedContentTitle?: string,
) {
  const setContext = useAICopilotStore((s) => s.setContext);
  const setPageActionCards = useAICopilotStore((s) => s.setPageActionCards);
  const setPageActionHandler = useAICopilotStore((s) => s.setPageActionHandler);

  // ─── Context ───
  useEffect(() => {
    setContext({
      page: "/",
      pageTitle: "工作台",
      selectedItems: selectedContentId ? [selectedContentId] : [],
      selectedContent:
        selectedContentId && selectedContentTitle
          ? { title: selectedContentTitle, platformId: "" }
          : undefined,
    });
  }, [setContext, selectedContentId, selectedContentTitle]);

  // ─── Action Cards ───
  useEffect(() => {
    // Fetch action cards from backend
    apiClient<{ cards: unknown[] }>("/api/ai/copilot/action-cards?page=/")
      .then((res) => {
        const cards = (res.cards || []).map((c) => {
          const card = c as Record<string, unknown>;
          return {
            id: String(card.id),
            type: String(card.type) as
              | "decision"
              | "generation"
              | "suggestion"
              | "info",
            title: String(card.title),
            description: String(card.description),
            priority: Number(card.priority || 1),
            inputs: Array.isArray(card.inputs) ? card.inputs : [],
            actions: Array.isArray(card.actions) ? card.actions : [],
          };
        });
        setPageActionCards(cards);
      })
      .catch(() => {
        // Silently fail — Action Cards are best-effort
        setPageActionCards([]);
      });

    // Register action handler
    setPageActionHandler(async (cardId, actionId) => {
      if (!handler) return;

      // 1. 先走前端纯导航能力表（覆盖默认兜底卡片如 dashboard-create-task / create_task）
      const navCap = resolveNavigateAction(actionId);
      if (navCap) {
        handler.navigate(navCap.target);
        return;
      }

      // 2. 后端动态卡片自定义逻辑
      if (cardId === "dash-new-task" && actionId === "create") {
        handler.navigate("/generate/create");
      } else if (cardId === "dash-quick-generate" && actionId === "generate") {
        handler.navigate("/generate/create");
      } else if (cardId === "dash-go-review" && actionId === "review") {
        handler.navigate("/review");
      } else if (cardId === "dash-batch-review" && actionId === "batch") {
        handler.navigate("/review");
      }
    });

    // Cleanup
    return () => {
      setPageActionCards([]);
      setPageActionHandler(null);
    };
  }, [setPageActionCards, setPageActionHandler, handler]);
}
