/** v4.0 Agent-First: 平台+格式 → 推荐 Agent ID 映射（10 个面向平台+格式的 Agent） */
export const AGENT_RECOMMENDATIONS: Record<string, string> = {
  // 小红书
  'xiaohongshu-图文': 'content_forge_xhs_image',
  'xiaohongshu-视频': 'content_forge_xhs_video',
  'xiaohongshu-仅文字': 'content_forge_xhs_text',
  // 抖音
  'douyin-视频': 'content_forge_douyin_video',
  'douyin-视频复刻': 'content_forge_douyin_clone',
  // 视频号
  'wechat_channels-图文': 'content_forge_wx_text',
  'wechat_channels-视频': 'content_forge_wx_video',
  // B站
  'bilibili-视频': 'content_forge_bili_video',
  'bilibili-视频复刻': 'content_forge_bili_clone',
}

/** 4 步向导步骤定义 */
export const STEPS = [
  { id: 0, label: '基础配置' },
  { id: 1, label: '主题与策略' },
  { id: 2, label: 'Agent 选择' },
  { id: 3, label: '发布确认' },
] as const

/** 平台ID → 显示名称映射（从 PlatformSchema 加载，兜底用） */
export const PLATFORM_ID_LABELS: Record<string, string> = {
  xiaohongshu: '小红书',
  douyin: '抖音',
  wechat_channels: '视频号',
  bilibili: '哔哩哔哩',
}
