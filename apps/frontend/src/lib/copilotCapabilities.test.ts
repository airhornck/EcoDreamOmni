import { describe, it, expect } from 'vitest'
import {
  resolveNavigateAction,
  FRONTEND_NAVIGATE_MAP,
  QUICK_ACTION_NAVIGATE_MAP,
} from './copilotCapabilities'

describe('copilotCapabilities', () => {
  it('maps default generate action ids to /generate/create', () => {
    expect(resolveNavigateAction('create_task')?.target).toBe('/generate/create')
    expect(resolveNavigateAction('quick_create')?.target).toBe('/generate/create')
    expect(resolveNavigateAction('open_wizard')?.target).toBe('/generate/create')
  })

  it('maps dashboard/create quick action texts', () => {
    expect(QUICK_ACTION_NAVIGATE_MAP['新建任务']?.target).toBe('/generate/create')
    expect(QUICK_ACTION_NAVIGATE_MAP['新建内容']?.target).toBe('/generate/create')
    expect(QUICK_ACTION_NAVIGATE_MAP['查看全部']?.target).toBe('/generate')
    expect(QUICK_ACTION_NAVIGATE_MAP['查看趋势']?.target).toBe('/analytics')
  })

  it('keeps existing navigation capabilities', () => {
    expect(FRONTEND_NAVIGATE_MAP['create']?.target).toBe('/generate/create')
    expect(FRONTEND_NAVIGATE_MAP['review']?.target).toBe('/review')
    expect(QUICK_ACTION_NAVIGATE_MAP['检查合规风险']?.target).toBe('/review')
  })
})
