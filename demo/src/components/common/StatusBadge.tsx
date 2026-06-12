import { Badge } from '../ui/Badge';
import type { ContentItem } from '../../types';
import { statusConfig } from '../../constants/labels';

interface StatusBadgeProps {
  status: ContentItem['status'];
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];
  return <Badge variant={config.variant}>{config.text}</Badge>;
}
