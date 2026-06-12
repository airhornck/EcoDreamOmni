export interface BaseResponse<T = unknown> {
  code: string;
  message: string;
  data: T;
  trace_id?: string;
  timestamp?: string;
}

export interface PaginatedResponse<T> extends BaseResponse<T[]> {
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

// ─── Agent Types (v4.0 Agent-First 新增) ───

export interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  avatar_url?: string;
  skills: string[];
  supported_platforms: string[];
  supported_formats: string[];
  config: Record<string, unknown>;
  success_rate: number;
  recent_tasks_1h: number;
  status: 'ACTIVE' | 'DEGRADED' | 'OFFLINE' | 'PAUSED';
  created_at: string;
  updated_at: string;
}

export interface AgentRecommendation {
  recommended_agent_id: string;
  confidence: number;
  reason: string;
  alternatives: Array<{
    agent_id: string;
    name: string;
    confidence: number;
    reason: string;
  }>;
  matched_capabilities: string[];
}

export interface AgentPromptVariable {
  key: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'text' | 'select';
  required?: boolean;
  default?: string | number | boolean;
  options?: Array<{ label: string; value: string }>;
  description?: string;
}
