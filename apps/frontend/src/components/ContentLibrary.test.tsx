import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ContentLibrary } from './ContentLibrary'

const mockDrafts = [
  { id: 'draft1', title: '猫咪驱虫指南', content_type: 'note', platform: 'xhs', status: 'draft', body: '春天到了...' },
  { id: 'draft2', title: '狗狗疫苗攻略', content_type: 'note', platform: 'douyin', status: 'reviewing', body: '疫苗很重要...' },
]

vi.mock('../stores/dashboardStore', () => ({
  useDashboardStore: (selector?: (s: unknown) => unknown) => {
    const store = {
      contentDrafts: mockDrafts,
      fetchContentDrafts: vi.fn(),
    }
    return selector ? selector(store) : store
  },
}))

describe('ContentLibrary', () => {
  it('renders content library title', () => {
    render(<MemoryRouter><ContentLibrary /></MemoryRouter>)
    expect(screen.getByText(/内容库/i)).toBeInTheDocument()
  })

  it('renders draft cards with title and platform', () => {
    render(<MemoryRouter><ContentLibrary /></MemoryRouter>)
    expect(screen.getByText('猫咪驱虫指南')).toBeInTheDocument()
    expect(screen.getByText('狗狗疫苗攻略')).toBeInTheDocument()
    expect(screen.getByText('xhs')).toBeInTheDocument()
    expect(screen.getByText('douyin')).toBeInTheDocument()
  })

  it('shows status badges for drafts', () => {
    render(<MemoryRouter><ContentLibrary /></MemoryRouter>)
    expect(screen.getByText('草稿')).toBeInTheDocument()
    expect(screen.getByText('审核中')).toBeInTheDocument()
  })

  it('has generate content button', () => {
    render(<MemoryRouter><ContentLibrary /></MemoryRouter>)
    expect(screen.getByRole('button', { name: /生成内容/i })).toBeInTheDocument()
  })
})
