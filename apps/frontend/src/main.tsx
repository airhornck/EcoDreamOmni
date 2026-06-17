import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";
import App from "./App.tsx";
import { Toaster } from "./components/ui/Toaster";
import { setupAuthIntercept } from "./lib/authIntercept";
import { suppressExtensionErrors } from "./lib/suppressExtensionErrors";

// 全局 401 拦截：过期/无效 token 自动登出并回登录页
setupAuthIntercept();

// 屏蔽浏览器扩展 content script 注入导致的无关节面报错（如 share-modal.js）
suppressExtensionErrors();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error) => {
        // 不重试 401/403 错误
        if (error instanceof Error) {
          const code = (error as { code?: string }).code;
          if (code === "UNAUTHORIZED" || code === "FORBIDDEN") return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster />
    </QueryClientProvider>
  </StrictMode>,
);
