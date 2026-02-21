interface VerdictBannerProps {
  verdict: string;
  composite: number;
  confidence?: number;
  summary?: string;
}

const verdictConfig: Record<string, { label: string; color: string; bg: string }> = {
  strong_buy: { label: 'STRONG BUY', color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
  buy: { label: 'BUY', color: '#06b6d4', bg: 'rgba(6,182,212,0.1)' },
  hold: { label: 'HOLD', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
  sell: { label: 'SELL', color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
  strong_sell: { label: 'STRONG SELL', color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
};

export default function VerdictBanner({ verdict, composite, confidence, summary }: VerdictBannerProps) {
  const config = verdictConfig[verdict] || verdictConfig.hold;

  return (
    <div
      className="rounded-xl border p-6 backdrop-blur-sm"
      style={{
        backgroundColor: config.bg,
        borderColor: `${config.color}30`,
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-4">
          <span
            className="text-3xl font-bold tracking-wider"
            style={{ color: config.color }}
          >
            {config.label}
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-text-secondary text-sm">Composite</span>
            <span className="text-xl font-semibold text-text-primary">
              {composite.toFixed(1)}
            </span>
            <span className="text-text-muted text-xs">/100</span>
          </div>
        </div>
        {confidence != null && (
          <div className="text-right">
            <span className="text-text-secondary text-xs">Confidence</span>
            <div className="text-text-primary font-medium">
              {(confidence * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>
      {summary && (
        <p className="text-text-secondary text-sm leading-relaxed">{summary}</p>
      )}
    </div>
  );
}
