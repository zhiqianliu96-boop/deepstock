import type { FundamentalDetail } from '../../types/analysis';
import FinancialChart from '../charts/FinancialChart';
import { useLocale } from '../../i18n/LocaleContext';

interface Props {
  detail: FundamentalDetail;
}

function MetricCard({ label, value, unit = '', good }: {
  label: string; value: any; unit?: string; good?: boolean | null;
}) {
  const color = good === true ? 'text-accent-green' : good === false ? 'text-accent-red' : 'text-text-primary';
  const displayVal = value == null ? 'N/A' : typeof value === 'number' ? value.toFixed(2) : String(value);
  return (
    <div className="bg-bg-card border border-border rounded-lg p-3">
      <div className="text-text-muted text-xs mb-1">{label}</div>
      <div className={`text-lg font-semibold ${color}`}>
        {displayVal}{unit && <span className="text-xs text-text-muted ml-1">{unit}</span>}
      </div>
    </div>
  );
}

function SubScoreBar({ label, score, max }: { label: string; score: number; max: number }) {
  const pct = Math.min(((score ?? 0) / max) * 100, 100);
  const color = pct >= 75 ? '#10b981' : pct >= 50 ? '#06b6d4' : pct >= 30 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-3">
      <span className="text-text-secondary text-xs w-28 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-bg-primary rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-text-primary text-xs w-12 text-right">{(score ?? 0).toFixed(1)}/{max}</span>
    </div>
  );
}

export default function FundamentalPanel({ detail }: Props) {
  const m = detail.metrics || {};
  const profile = detail.company_profile || {};
  const { t } = useLocale();

  return (
    <div className="space-y-6">
      {/* Sub-scores */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">{t('fundamental.subscores')}</h3>
        <div className="space-y-3">
          <SubScoreBar label={t('fundamental.valuation')} score={detail.valuation_score} max={25} />
          <SubScoreBar label={t('fundamental.profitability')} score={detail.profitability_score} max={25} />
          <SubScoreBar label={t('fundamental.growth')} score={detail.growth_score} max={25} />
          <SubScoreBar label={t('fundamental.health')} score={detail.health_score} max={25} />
        </div>
      </div>

      {/* Key Ratios Grid */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">{t('fundamental.key_ratios')}</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <MetricCard label={t('fundamental.pe')} value={m.pe} good={m.pe != null ? m.pe < 25 : null} />
          <MetricCard label={t('fundamental.pb')} value={m.pb} good={m.pb != null ? m.pb < 3 : null} />
          <MetricCard label={t('fundamental.ps')} value={m.ps} good={m.ps != null ? m.ps < 5 : null} />
          <MetricCard label={t('fundamental.peg')} value={m.peg} good={m.peg != null ? m.peg < 1 : null} />
          <MetricCard label={t('fundamental.roe')} value={m.roe} unit="%" good={m.roe != null ? m.roe > 15 : null} />
          <MetricCard label={t('fundamental.roa')} value={m.roa} unit="%" good={m.roa != null ? m.roa > 5 : null} />
          <MetricCard label={t('fundamental.gross_margin')} value={m.gross_margin} unit="%" good={m.gross_margin != null ? m.gross_margin > 30 : null} />
          <MetricCard label={t('fundamental.net_margin')} value={m.net_margin} unit="%" good={m.net_margin != null ? m.net_margin > 10 : null} />
          <MetricCard label={t('fundamental.revenue_growth')} value={m.revenue_growth_yoy} unit="%" good={m.revenue_growth_yoy != null ? m.revenue_growth_yoy > 0 : null} />
          <MetricCard label={t('fundamental.profit_growth')} value={m.profit_growth_yoy} unit="%" good={m.profit_growth_yoy != null ? m.profit_growth_yoy > 0 : null} />
          <MetricCard label={t('fundamental.debt_equity')} value={m.debt_to_equity} good={m.debt_to_equity != null ? m.debt_to_equity < 0.5 : null} />
          <MetricCard label={t('fundamental.current_ratio')} value={m.current_ratio} good={m.current_ratio != null ? m.current_ratio > 1.5 : null} />
          <MetricCard label={t('fundamental.fcf_yield')} value={m.fcf_yield} unit="%" good={m.fcf_yield != null ? m.fcf_yield > 3 : null} />
          <MetricCard label={t('fundamental.eps')} value={m.eps} />
          <MetricCard label={t('fundamental.dividend_yield')} value={m.dividend_yield} unit="%" />
          <MetricCard
            label={t('fundamental.market_cap')}
            value={m.market_cap ? (m.market_cap >= 1e12 ? (m.market_cap / 1e12).toFixed(1) + 'T' : m.market_cap >= 1e9 ? (m.market_cap / 1e9).toFixed(1) + 'B' : m.market_cap >= 1e8 ? (m.market_cap / 1e8).toFixed(1) + '亿' : (m.market_cap / 1e6).toFixed(0) + 'M') : null}
          />
        </div>
      </div>

      {/* Financial Chart */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">{t('fundamental.financial_trends')}</h3>
        <FinancialChart metrics={m} />
      </div>

      {/* Company Profile */}
      {Object.keys(profile).length > 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-3">{t('fundamental.company_profile')}</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {profile.sector && (
              <div><span className="text-text-muted">{t('fundamental.sector')}: </span><span className="text-text-secondary">{profile.sector}</span></div>
            )}
            {profile.industry && (
              <div><span className="text-text-muted">{t('fundamental.industry')}: </span><span className="text-text-secondary">{profile.industry}</span></div>
            )}
          </div>
          {profile.description && (
            <p className="text-text-muted text-xs mt-3 leading-relaxed line-clamp-4">{profile.description}</p>
          )}
        </div>
      )}

      {/* Peer Comparison */}
      {detail.peer_comparison && Object.keys(detail.peer_comparison).length > 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-3">{t('fundamental.peer_comparison')}</h3>
          <div className="space-y-2">
            {Object.entries(detail.peer_comparison).map(([key, pct]) => (
              <div key={key} className="flex items-center gap-3">
                <span className="text-text-secondary text-xs w-32 shrink-0 capitalize">{key.replace(/_/g, ' ')}</span>
                <div className="flex-1 h-2 bg-bg-primary rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-accent-cyan"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-text-primary text-xs w-10 text-right">{pct.toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
