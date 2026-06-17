/**
 * 全局错误过滤器：屏蔽浏览器扩展（content scripts）注入脚本产生的无关节面报错。
 *
 * 这些错误通常表现为：
 *   - 文件名是 chrome-extension://.../share-modal.js
 *   - 扩展脚本在页面未找到预期 DOM 时抛出 TypeError
 *
 * 它们不是应用代码的问题，却会污染浏览器控制台/Sentry。
 */

const EXTENSION_ORIGINS = [
  'chrome-extension://',
  'moz-extension://',
  'edge://',
  'safari-extension://',
  'safari-web-extension://',
]

const KNOWN_EXTENSION_FILES = [
  'share-modal.js',
]

function looksLikeExtensionError(source: string | undefined): boolean {
  if (!source) return false
  const lower = source.toLowerCase()
  return (
    EXTENSION_ORIGINS.some((origin) => lower.startsWith(origin)) ||
    KNOWN_EXTENSION_FILES.some((file) => lower.includes(file))
  )
}

function normalizeErrorSource(event: ErrorEvent): string | undefined {
  return (
    // 标准属性
    event.filename ||
    // 部分扩展脚本不会设置 filename，从 stack 里尝试提取
    (event.error as Error | undefined)?.stack ||
    (event.message as string | undefined)
  )
}

export function suppressExtensionErrors(): void {
  if (typeof window === 'undefined') return
  // 避免在单元测试（jsdom）里注册全局事件监听器
  if ((import.meta.env as Record<string, unknown>).VITEST) return

  window.addEventListener(
    'error',
    (event) => {
      const source = normalizeErrorSource(event)
      if (looksLikeExtensionError(source)) {
        // 阻止冒泡，避免继续上报到 Sentry 等监控服务
        event.preventDefault()
        event.stopImmediatePropagation()
        // 只在开发环境保留一条低级别提示，方便确认过滤生效
        if (import.meta.env.DEV) {
          console.debug('[suppressExtensionErrors] ignored extension error:', event.message, source)
        }
      }
    },
    true,
  )

  // 扩展脚本的 Promise 异常 rejection 也可能走这里
  window.addEventListener(
    'unhandledrejection',
    (event) => {
      const reason = event.reason
      const source =
        (typeof reason === 'string' ? reason : (reason as Error | undefined)?.stack) ||
        (reason as { source?: string } | undefined)?.source
      if (looksLikeExtensionError(source)) {
        event.preventDefault()
        event.stopImmediatePropagation()
        if (import.meta.env.DEV) {
          console.debug('[suppressExtensionErrors] ignored extension rejection:', source)
        }
      }
    },
    true,
  )
}
