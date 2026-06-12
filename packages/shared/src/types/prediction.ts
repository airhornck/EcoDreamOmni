/**
 * PoolPredictor shared types aligned with detailed design §5.1.
 * Must stay in sync with backend Pydantic schema and frontend Zod schema.
 */

export interface MetricInterval {
  lower: number;
  median: number;
  upper: number;
}

export interface PredictionResponse {
  prediction_id: string;
  account_id: string;
  topic: string;
  likes: MetricInterval;
  comments: MetricInterval;
  saves: MetricInterval;
  interval_mode: "prior" | "fitted";
  confidence: number;
  feature_version: string;
  features: Record<string, number>;
  latency_ms?: number;
}

export interface PredictionRequest {
  account_id: string;
  content_type?: "note" | "video" | "carousel";
  topic?: string;
  lifecycle_phase?: "cold_start" | "growth" | "mature" | "dormant";
  platform?: "xhs" | "douyin" | "wechat_channels";
  word_count?: number;
  has_image?: boolean;
  has_video?: boolean;
  publish_hour?: number;
  n_posts_effective?: number;
}

export interface BatchPredictionRequest {
  items: Array<{
    account_id: string;
    content_type?: string;
    topic?: string;
    lifecycle_phase?: string;
    platform?: string;
    n_posts_effective?: number;
  }>;
}
