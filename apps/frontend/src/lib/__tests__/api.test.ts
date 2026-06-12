import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient, unwrapResponse, ApiError, authHeaders } from '../api'

describe('api', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('authHeaders', () => {
    it('returns headers with token and tenant', () => {
      localStorage.setItem('token', 'abc123')
      localStorage.setItem('tenant_id', 'tenant_001')
      const h = authHeaders()
      expect(h['Authorization']).toBe('Bearer abc123')
      expect(h['X-Tenant-ID']).toBe('tenant_001')
      expect(h['Content-Type']).toBe('application/json')
    })

    it('skips Content-Type for FormData', () => {
      const h = authHeaders(false)
      expect(h['Content-Type']).toBeUndefined()
    })
  })

  describe('unwrapResponse', () => {
    it('unwraps standard response format', () => {
      const json = { code: 'OK', message: 'success', data: { foo: 1 } }
      expect(unwrapResponse<{ foo: number }>(json)).toEqual({ foo: 1 })
    })

    it('unwraps CREATED code', () => {
      const json = { code: 'CREATED', message: 'created', data: { id: 'x' } }
      expect(unwrapResponse<{ id: string }>(json)).toEqual({ id: 'x' })
    })

    it('throws ApiError on error code', () => {
      const json = { code: 'VALIDATION_ERROR', message: 'bad', data: null }
      expect(() => unwrapResponse(json)).toThrow(ApiError)
    })

    it('returns raw data for legacy format', () => {
      const json = { metrics: { count: 5 } }
      expect(unwrapResponse(json)).toEqual({ metrics: { count: 5 } })
    })
  })

  describe('apiClient', () => {
    it('prepends /api if missing', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ code: 'OK', data: {} }),
      })
      vi.stubGlobal('fetch', mockFetch)

      await apiClient('/dashboard/overview')
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/dashboard/overview',
        expect.objectContaining({ headers: expect.any(Object) })
      )
    })

    it('returns unwrapped data', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ code: 'OK', data: { count: 5 } }),
      })
      vi.stubGlobal('fetch', mockFetch)

      const result = await apiClient<{ count: number }>('/test')
      expect(result).toEqual({ count: 5 })
    })

    it('throws ApiError on HTTP error with body', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ code: 'VALIDATION_ERROR', message: 'invalid', trace_id: 't1' }),
      })
      vi.stubGlobal('fetch', mockFetch)

      await expect(apiClient('/test')).rejects.toThrow(ApiError)
    })

    it('throws ApiError on HTTP error without body', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Server Error',
        json: async () => { throw new Error('fail') },
      })
      vi.stubGlobal('fetch', mockFetch)

      await expect(apiClient('/test')).rejects.toThrow(ApiError)
    })
  })
})
