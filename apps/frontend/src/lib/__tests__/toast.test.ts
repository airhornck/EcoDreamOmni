import { describe, it, expect, vi } from 'vitest'

// Mock sonner before importing toast module
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
    promise: vi.fn(),
  },
}))

import { toast } from 'sonner'
import { showToast } from '../toast'

describe('showToast', () => {
  it('calls toast.success', () => {
    showToast.success('Saved', 'Data persisted')
    expect(toast.success).toHaveBeenCalledWith('Saved', { description: 'Data persisted' })
  })

  it('calls toast.error', () => {
    showToast.error('Failed', 'Network error')
    expect(toast.error).toHaveBeenCalledWith('Failed', { description: 'Network error' })
  })

  it('calls toast.warning', () => {
    showToast.warning('Warn')
    expect(toast.warning).toHaveBeenCalledWith('Warn', { description: undefined })
  })

  it('calls toast.info', () => {
    showToast.info('Info')
    expect(toast.info).toHaveBeenCalledWith('Info', { description: undefined })
  })

  it('calls toast.loading and returns id', () => {
    const mockId = 'toast-123'
    vi.mocked(toast.loading).mockReturnValue(mockId as unknown as number)
    const id = showToast.loading('Loading...')
    expect(toast.loading).toHaveBeenCalledWith('Loading...', { description: undefined })
    expect(id).toBe(mockId)
  })

  it('calls toast.dismiss', () => {
    showToast.dismiss('toast-123')
    expect(toast.dismiss).toHaveBeenCalledWith('toast-123')
  })

  it('calls toast.promise', async () => {
    const p = Promise.resolve(42)
    showToast.promise(p, {
      loading: 'Working',
      success: 'Done',
      error: 'Oops',
    })
    expect(toast.promise).toHaveBeenCalledWith(p, {
      loading: 'Working',
      success: 'Done',
      error: 'Oops',
    })
  })
})
