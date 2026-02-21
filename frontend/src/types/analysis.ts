export interface AnalysisRequest {
  code: string;
  ai_provider?: string;
  lang?: string;
}

export interface FundamentalDetail {
  total: number;
  valuation_score: number;
  profitability_score: number;
  growth_score: number;
  health_score: number;
  breakdown: Record<string, any>;
  metrics: Record<string, any>;
  peer_comparison: Record<string, number>;
  company_profile: Record<string, any>;
}

export interface TechnicalDetail {
  total: number;
  trend_score: number;
  momentum_score: number;
  volume_score: number;
  structure_score: number;
  pattern_score: number;
  breakdown: Record<string, any>;
  indicators: Record<string, any>;
  support_resistance: Record<string, any>;
  institutional_flow: Record<string, any>;
  chip_data: Record<string, any>;
  patterns: PatternAlert[];
  chart_data: ChartData;
}

export interface PatternAlert {
  date: string;
  pattern: string;
  type: 'bullish' | 'bearish' | 'neutral';
  reliability: 'high' | 'medium' | 'low';
}

export interface ChartData {
  dates: string[];
  ohlcv: number[][];
  volumes: number[];
  ma5?: number[];
  ma10?: number[];
  ma20?: number[];
  ma60?: number[];
  ma120?: number[];
  ma250?: number[];
  macd_dif?: number[];
  macd_dea?: number[];
  macd_hist?: number[];
  support_levels?: number[];
  resistance_levels?: number[];
}

export interface ScoredArticle {
  title: string;
  url: string;
  score: number;
  category: string;
  source_quality: number;
  published_date?: string;
  positive_matches: string[];
  negative_matches: string[];
}

export interface SentimentDetail {
  total: number;
  news_sentiment_score: number;
  event_impact_score: number;
  market_attention_score: number;
  source_quality_score: number;
  breakdown: Record<string, any>;
  articles: ScoredArticle[];
  timeline: ScoredArticle[];
  category_summary: Record<string, { count: number; avg_score: number; impact: string }>;
}

export interface AIDashboard {
  bias_check?: 'safe' | 'caution' | 'danger';
  ma_alignment?: string;
  chip_health?: string;
  volume_signal?: string;
  action_checklist?: string[];
  news_digest?: string;
}

export interface AISynthesis {
  verdict: string;
  confidence: number;
  summary: string;
  fundamental_interpretation: string;
  technical_interpretation: string;
  sentiment_interpretation: string;
  risks: string[];
  catalysts: string[];
  price_targets: {
    support: number | null;
    resistance: number | null;
    fair_value_range: [number, number] | null;
  };
  position_advice: string;
  time_horizon: string;
  dashboard?: AIDashboard;
}

export interface AnalysisResult {
  code: string;
  name: string;
  market: string;
  sector: string;
  industry: string;
  fundamental_score: number;
  technical_score: number;
  sentiment_score: number;
  composite_score: number;
  verdict: string;
  fundamental_detail: FundamentalDetail;
  technical_detail: TechnicalDetail;
  sentiment_detail: SentimentDetail;
  ai_synthesis: AISynthesis;
  chart_data: ChartData;
}

export interface HistoryRecord {
  id: number;
  code: string;
  name: string;
  market: string;
  analysis_date: string;
  fundamental_score: number;
  technical_score: number;
  sentiment_score: number;
  composite_score: number;
  verdict: string;
  ai_provider: string;
}
