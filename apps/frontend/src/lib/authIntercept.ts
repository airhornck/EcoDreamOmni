import { useAuthStore } from '../stores/authStore'

let originalFetch: typeof window.fetch | null = null
let isSetup = false

/**
 * 拦截 fetch 响应：当带 Authorization 的请求收到 401 时，
 * 自动清理登录态并跳转登录页。
 *
 * 注意：不拦截未带 Authorization 的请求（如登录失败本身返回 401），
 * 避免把登录页也重定向走。
 */
export function setupAuthIntercept(): () => void {
  if (isSetup || typeof window === 'undefined') {
    return () => {}
  }

  originalFetch = window.fetch
  isSetup = true

  window.fetch = async (...args: Parameters<typeof fetch>): Promise<Response> => {
    const response = await originalFetch!(...args)

    if (response.status === 401) {
      const [, init] = args
      const headers = new Headers(init?.headers)
      const authorization = headers.get('Authorization')

      if (authorization) {
        useAuthStore.getState().logout()
        window.location.href = '/login'
      }
    }

    return response
  }

  return () => {
    if (originalFetch) {
      window.fetch = originalFetch
      originalFetch = null
      isSetup = false
    }
  }
}
