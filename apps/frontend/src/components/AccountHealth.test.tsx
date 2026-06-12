import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AccountHealth } from './AccountHealth'

const mockAccounts = [
  { id: 'acc1', account_id: 'pool_xhs_001', nickname: '素人号001', health_score: 92, status: 'active', lifecycle_phase: 'growth' },
  { id: 'acc2', account_id: 'pool_dy_001', nickname: '抖音素人001', health_score: 45, status: 'warming', lifecycle_phase: 'cold_start' },
  { id: 'acc3', account_id: 'pool_xhs_002', nickname: '素人号002', health_score: 78, status: 'active', lifecycle_phase: 'mature' },
]

vi.mock('../stores/dashboardStore', () => ({
  useDashboardStore: (selector?: (s: unknown) => unknown) => {
    const store = {
      accountPool: mockAccounts,
      fetchAccountPool: vi.fn(),
    }
    return selector ? selector(store) : store
  },
}))

describe('AccountHealth', () => {
  it('renders account health title', () => {
    render(<AccountHealth />)
    expect(screen.getByText(/账号健康/i)).toBeInTheDocument()
  })

  it('renders account rows with health scores', () => {
    render(<AccountHealth />)
    expect(screen.getByText('素人号001')).toBeInTheDocument()
    expect(screen.getByText('92')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
    expect(screen.getByText('78')).toBeInTheDocument()
  })

  it('shows lifecycle phase labels', () => {
    render(<AccountHealth />)
    expect(screen.getByText('growth')).toBeInTheDocument()
    expect(screen.getByText('cold_start')).toBeInTheDocument()
  })

  it('shows status indicators', () => {
    render(<AccountHealth />)
    expect(screen.getAllByText('active').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('warming')).toBeInTheDocument()
  })
})
