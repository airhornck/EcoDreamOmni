import type { ContentItem, Account, PlatformRule } from '../types';

export const stageLabels: Record<string, string> = {
  AWARENESS: '认知期',
  INTEREST: '兴趣期',
  PURCHASE: '购买期',
  LOYALTY: '忠诚期',
};

export type ContentStatus = ContentItem['status'];

export const statusConfig: Record<ContentStatus, { text: string; variant: 'default' | 'success' | 'warning' | 'danger' | 'info' }> = {
  draft: { text: '草稿', variant: 'default' },
  reviewing: { text: '审核中', variant: 'warning' },
  approved: { text: '已通过', variant: 'success' },
  published: { text: '已发布', variant: 'info' },
  rejected: { text: '已驳回', variant: 'danger' },
};

export const platformLabels: Record<string, string> = {
  xhs: '小红书',
  douyin: '抖音',
  shipinhao: '视频号',
};

export const lifecycleLabels: Record<string, string> = {
  cold_start: '冷启动',
  growth: '成长期',
  mature: '成熟期',
};

export const accountStatusConfig: Record<Account['status'], { text: string; variant: 'default' | 'success' | 'warning' | 'danger' }> = {
  active: { text: '正常', variant: 'success' },
  warming: { text: '养号中', variant: 'warning' },
  restricted: { text: '限流', variant: 'danger' },
  banned: { text: '封禁', variant: 'default' },
};

export const ruleActionConfig: Record<PlatformRule['action'], { text: string; variant: 'danger' | 'warning' | 'info' }> = {
  block: { text: '拦截', variant: 'danger' },
  warn: { text: '警告', variant: 'warning' },
  suggest: { text: '建议', variant: 'info' },
};

export const layerNames: Record<string, string> = {
  l1: 'L1 法律红线',
  l2: 'L2 平台规则',
  l3: 'L3 账号策略',
  l4: 'L4 动态风控',
};

export const layerDescriptions: Record<string, string> = {
  l1: '处方药、诊断、治疗承诺关键词拦截',
  l2: '敏感词语义模型评分，>0.7 触发警告',
  l3: '频率阶梯校验：冷启动1篇/日，成长3篇/日',
  l4: '节日临时策略、时段竞争系数、自定义规则',
};
