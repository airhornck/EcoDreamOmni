import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AgentFlowBar } from '../AgentFlowBar'
import { useAgentFlowStore } from '../../../stores/agentFlowStore'

describe('AgentFlowBar', () => {
  beforeEach(() => {
    useAgentFlowStore.setState({ execution: null, isConnected: false, wsError: null })
  })

  it('shows empty state when no execution', () => {
    render(<AgentFlowBar />)
    expect(screen.getByText('暂无执行中的 Pipeline')).toBeInTheDocument()
  })

  it('renders execution summary with progress', () => {
    useAgentFlowStore.setState({
      execution: {
        executionId: 'exec_abc123',
        templateName: '内容生产标准',
        status: 'RUNNING',
        startedAt: new Date().toISOString(),
        nodes: [
          { id: 'n1', name: '选题洞察', type: 'AGENT', status: 'SUCCESS' },
          { id: 'n2', name: '结构分析', type: 'AGENT', status: 'RUNNING' },
          { id: 'n3', name: '内容生成', type: 'AGENT', status: 'PENDING' },
        ],
      },
    })

    render(<AgentFlowBar />)
    expect(screen.getByText('内容生产标准')).toBeInTheDocument()
    expect(screen.getByText('1/3')).toBeInTheDocument()
    expect(screen.getByText('33%')).toBeInTheDocument()
  })

  it('expands and collapses details', () => {
    useAgentFlowStore.setState({
      execution: {
        executionId: 'exec_abc123',
        templateName: '内容生产标准',
        status: 'RUNNING',
        startedAt: new Date().toISOString(),
        nodes: [
          { id: 'n1', name: '选题洞察', type: 'AGENT', status: 'SUCCESS' },
          { id: 'n2', name: '结构分析', type: 'AGENT', status: 'RUNNING' },
        ],
      },
    })

    render(<AgentFlowBar />)

    fireEvent.click(screen.getByText('展开详情'))
    expect(screen.getByText('选题洞察')).toBeInTheDocument()
    expect(screen.getByText('结构分析')).toBeInTheDocument()

    fireEvent.click(screen.getByText('收起'))
    expect(screen.queryByText('选题洞察')).not.toBeInTheDocument()
  })
})
