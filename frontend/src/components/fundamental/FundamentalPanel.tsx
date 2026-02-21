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

  // Extract deep data from metrics/breakdown (fundamental.py puts them in both)
  const dupont = m.dupont || detail.breakdown?.dupont || null;
  const shareholders = m.shareholders || detail.breakdown?.shareholders || null;
  const analystConsensus = m.analyst_consensus || detail.breakdown?.analyst_consensus || null;

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

      {/* DuPont Decomposition */}
      {dupont && dupont.net_margin != null && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-4">{t('fundamental.dupont')}</h3>
          <div className="flex items-center justify-center gap-2 text-sm mb-4">
            <span className="text-text-muted">ROE</span>
            <span className="text-text-primary font-semibold font-mono-num">{dupont.roe?.toFixed(1) ?? '—'}%</span>
            <span className="text-text-muted">=</span>
            <span className="text-text-muted">{t('fundamental.dupont_margin')}</span>
            <span className="text-accent-cyan font-semibold font-mono-num">{dupont.net_margin?.toFixed(1) ?? '—'}%</span>
            <span className="text-text-muted">&times;</span>
            <span className="text-text-muted">{t('fundamental.dupont_turnover')}</span>
            <span className="text-accent-green font-semibold font-mono-num">{dupont.asset_turnover?.toFixed(2) ?? dupont.asset_turnover_x_leverage?.toFixed(4) ?? '—'}</span>
            {dupont.equity_multiplier != null && (
              <>
                <span className="text-text-muted">&times;</span>
                <span className="text-text-muted">{t('fundamental.dupont_leverage')}</span>
                <span className="text-accent-yellow font-semibold font-mono-num">{dupont.equity_multiplier.toFixed(2)}</span>
              </>
            )}
          </div>
          {/* Visual bars */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <div className="text-text-muted text-xs mb-1">{t('fundamental.dupont_margin')}</div>
              <div className="h-3 bg-bg-primary rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-accent-cyan" style={{ width: `${Math.min(100, Math.max(0, (dupont.net_margin ?? 0)))}%` }} />
              </div>
              <div className="text-text-secondary text-xs mt-1 font-mono-num">{dupont.net_margin?.toFixed(1)}%</div>
            </div>
            <div>
              <div className="text-text-muted text-xs mb-1">{t('fundamental.dupont_turnover')}</div>
              <div className="h-3 bg-bg-primary rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-accent-green" style={{ width: `${Math.min(100, (dupont.asset_turnover ?? 0) * 50)}%` }} />
              </div>
              <div className="text-text-secondary text-xs mt-1 font-mono-num">{dupont.asset_turnover?.toFixed(2) ?? '—'}</div>
            </div>
            {dupont.equity_multiplier != null && (
              <div>
                <div className="text-text-muted text-xs mb-1">{t('fundamental.dupont_leverage')}</div>
                <div className="h-3 bg-bg-primary rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-accent-yellow" style={{ width: `${Math.min(100, (dupont.equity_multiplier / 5) * 100)}%` }} />
                </div>
                <div className="text-text-secondary text-xs mt-1 font-mono-num">{dupont.equity_multiplier.toFixed(2)}x</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top Shareholders */}
      {shareholders && shareholders.top_holders && shareholders.top_holders.length > 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-3">
            {t('fundamental.shareholders')}
            {shareholders.top10_total_pct != null && (
              <span className="text-text-muted text-xs ml-2 font-normal">
                ({t('fundamental.top10_pct')}: {shareholders.top10_total_pct}%)
              </span>
            )}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/50">
                  <th className="text-left text-text-muted text-xs py-2 pr-4">#</th>
                  <th className="text-left text-text-muted text-xs py-2 pr-4">{t('fundamental.shareholder_name')}</th>
                  <th className="text-right text-text-muted text-xs py-2">{t('fundamental.shareholder_pct')}</th>
                </tr>
              </thead>
              <tbody>
                {shareholders.top_holders.slice(0, 10).map((h: any, i: number) => {
                  const name = h['股东名称'] || h['Holder'] || h['holder'] || Object.values(h)[0] || '—';
                  const pctKey = Object.keys(h).find(k => k.includes('比例') || k.includes('%') || k.includes('pct') || k.includes('Shares'));
                  const pct = pctKey ? h[pctKey] : null;
                  return (
                    <tr key={i} className="border-b border-border/30">
                      <td className="py-1.5 text-text-muted text-xs">{i + 1}</td>
                      <td className="py-1.5 text-text-secondary text-xs truncate max-w-[200px]">{String(name)}</td>
                      <td className="py-1.5 text-text-primary text-xs text-right font-mono-num">{pct != null ? `${Number(pct).toFixed(2)}%` : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Analyst Consensus */}
      {analystConsensus && (analystConsensus.buy != null || analystConsensus.ratings_distribution) && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-3">{t('fundamental.analyst_consensus')}</h3>
          {analystConsensus.buy != null && (
            <div className="mb-3">
              {/* Buy/Hold/Sell bar */}
              {(() => {
                const total = (analystConsensus.buy || 0) + (analystConsensus.hold || 0) + (analystConsensus.sell || 0);
                if (total === 0) return null;
                const buyPct = ((analystConsensus.buy || 0) / total) * 100;
                const holdPct = ((analystConsensus.hold || 0) / total) * 100;
                const sellPct = ((analystConsensus.sell || 0) / total) * 100;
                return (
                  <div>
                    <div className="flex h-4 rounded-full overflow-hidden mb-2">
                      {buyPct > 0 && <div className="bg-accent-green" style={{ width: `${buyPct}%` }} />}
                      {holdPct > 0 && <div className="bg-accent-yellow" style={{ width: `${holdPct}%` }} />}
                      {sellPct > 0 && <div className="bg-accent-red" style={{ width: `${sellPct}%` }} />}
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-accent-green">{t('fundamental.analyst_buy')}: {analystConsensus.buy}</span>
                      <span className="text-accent-yellow">{t('fundamental.analyst_hold')}: {analystConsensus.hold || 0}</span>
                      <span className="text-accent-red">{t('fundamental.analyst_sell')}: {analystConsensus.sell || 0}</span>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}
          {analystConsensus.ratings_distribution && (
            <div className="flex flex-wrap gap-2 mb-3">
              {Object.entries(analystConsensus.ratings_distribution).map(([rating, count]) => (
                <span key={rating} className="text-xs px-2 py-1 bg-bg-primary rounded text-text-secondary">
                  {rating}: {count}
                </span>
              ))}
            </div>
          )}
          {analystConsensus.target_price_mean != null && (
            <div className="text-sm text-text-secondary">
              <span className="text-text-muted">{t('fundamental.target_price')}: </span>
              <span className="text-text-primary font-semibold font-mono-num">{analystConsensus.target_price_mean}</span>
              {analystConsensus.target_price_low != null && analystConsensus.target_price_high != null && (
                <span className="text-text-muted ml-2">
                  ({analystConsensus.target_price_low} ~ {analystConsensus.target_price_high})
                </span>
              )}
            </div>
          )}
        </div>
      )}

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
