import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AssetPoolPage } from '../AssetPoolPage'

const mockStore = {
  assets: [] as unknown[],
  isLoading: false,
  error: null as string | null,
  fetchAssets: vi.fn(),
  createAsset: vi.fn(),
  deleteAsset: vi.fn(),
}

vi.mock('../../stores/assetPoolStore', () => ({
  useAssetPoolStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('AssetPoolPage — Copilot 适配', () => {
  beforeEach(() => {
    mockStore.assets = []
    mockStore.error = null
    vi.clearAllMocks()
  })

  it('renders page header', () => {
    render(<MemoryRouter><AssetPoolPage /></MemoryRouter>)
    expect(screen.getByText('素材库')).toBeInTheDocument()
    expect(screen.getByText('添加素材')).toBeInTheDocument()
  })

  it('uses xl breakpoint for asset grid', () => {
    const { container } = render(<MemoryRouter><AssetPoolPage /></MemoryRouter>)
    const grid = container.querySelector('.grid.grid-cols-1.md\\:grid-cols-2.xl\\:grid-cols-3')
    expect(grid).toBeInTheDocument()
  })

  it('asset list card has shrink protection', () => {
    const { container } = render(<MemoryRouter><AssetPoolPage /></MemoryRouter>)
    const card = container.querySelector('.bg-card.rounded-xl.border.border-border.min-w-0.overflow-hidden')
    expect(card).toBeInTheDocument()
  })

  it('renders asset cards', () => {
    mockStore.assets = [
      { id: 'a1', name: '封面图', type: 'image', url: 'https://example.com/img.jpg', tags: ['封面'] },
    ]
    render(<MemoryRouter><AssetPoolPage /></MemoryRouter>)
    expect(screen.getByText('封面图')).toBeInTheDocument()
    expect(screen.getByText('image')).toBeInTheDocument()
  })

  it('opens create form when clicking add button', () => {
    render(<MemoryRouter><AssetPoolPage /></MemoryRouter>)
    fireEvent.click(screen.getByText('添加素材'))
    expect(screen.getByPlaceholderText('素材名称')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('URL 链接')).toBeInTheDocument()
  })
})
