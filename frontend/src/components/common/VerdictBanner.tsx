import { useLocale } from '../../i18n/LocaleContext';

interface VerdictBannerProps {
  verdict: string;
  composite: number;
  confidence?: number;
  summary?: string;
}

const verdictColorMap: Record<string, { color: string; bg: string }> = {
  strong_buy: { color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
  buy: { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)' },
  hold: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
  sell: { color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
  strong_sell: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
};

const verdictLabelKeys: Record<string, string> = {
  strong_buy: 'verdict.strong_buy',
  buy: 'verdict.buy',
  hold: 'verdict.hold',
  sell: 'verdict.sell',
  strong_sell: 'verdict.strong_sell',
};

export default function VerdictBanner({ verdict, composite, confidence, summary }: VerdictBannerProps) {
  const { t } = useLocale();
  const colors = verdictColorMap[verdict] || verdictColorMap.hold;
  const labelKey = verdictLabelKeys[verdict] || 'verdict.hold';

  return (
    <div
      className="rounded-xl border p-6 backdrop-blur-sm"
      style={{
        backgroundColor: colors.bg,
        borderColor: `${colors.color}30`,
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-4">
          <span
            className="text-3xl font-bold tracking-wider"
            style={{ color: colors.color }}
          >
            {t(labelKey as any)}
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-text-secondary text-sm">{t('verdict.composite')}</span>
            <span className="text-xl font-semibold text-text-primary">
              {composite.toFixed(1)}
            </span>
            <span className="text-text-muted text-xs">/100</span>
          </div>
        </div>
        {confidence != null && (
          <div className="text-right">
            <span className="text-text-secondary text-xs">{t('verdict.confidence')}</span>
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
