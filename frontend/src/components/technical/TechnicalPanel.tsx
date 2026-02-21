import type { TechnicalDetail } from '../../types/analysis';
import KLineChart from '../charts/KLineChart';
import { useLocale } from '../../i18n/LocaleContext';

interface Props {
  detail: TechnicalDetail;
}

function SubScoreBar({ label, score, max }: { label: string; score: number; max: number }) {
  const pct = Math.min(((score ?? 0) / max) * 100, 100);
  const color = pct >= 75 ? '#10b981' : pct >= 50 ? '#06b6d4' : pct >= 30 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-3">
      <span className="text-text-secondary text-xs w-24 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-bg-primary rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-text-primary text-xs w-12 text-right">{(score ?? 0).toFixed(1)}/{max}</span>
    </div>
  );
}

function IndicatorBadge({ label, value, signal }: { label: string; value: string; signal?: string }) {
  const signalColor = signal === 'bullish' || signal === 'oversold' ? 'text-accent-green'
    : signal === 'bearish' || signal === 'overbought' ? 'text-accent-red'
    : 'text-text-secondary';
  return (
    <div className="bg-bg-primary rounded-lg p-3 border border-border/50">
      <div className="text-text-muted text-xs mb-1">{label}</div>
      <div className="text-text-primary font-medium text-sm">{value}</div>
      {signal && <div className={`text-xs mt-1 ${signalColor}`}>{signal}</div>}
    </div>
  );
}

export default function TechnicalPanel({ detail }: Props) {
  const ind = detail.indicators || {};
  const sr = detail.support_resistance || {};
  const flow = detail.institutional_flow || {};
  const chip = detail.chip_data || {};
  const { t } = useLocale();

  return (
    <div className="space-y-6">
      {/* Sub-scores */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">{t('technical.subscores')}</h3>
        <div className="space-y-3">
          <SubScoreBar label={t('technical.trend')} score={detail.trend_score} max={30} />
          <SubScoreBar label={t('technical.momentum')} score={detail.momentum_score} max={20} />
          <SubScoreBar label={t('technical.volume')} score={detail.volume_score} max={20} />
          <SubScoreBar label={t('technical.structure')} score={detail.structure_score} max={15} />
          <SubScoreBar label={t('technical.pattern')} score={detail.pattern_score} max={15} />
        </div>
      </div>

      {/* K-Line Chart */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">{t('technical.kline')}</h3>
        {detail.chart_data ? (
          <KLineChart chartData={detail.chart_data} />
        ) : (
          <div className="h-[400px] flex items-center justify-center text-text-muted">
            {t('technical.kline_empty')}
          </div>
        )}
      </div>

      {/* Technical Indicators */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">{t('technical.indicators')}</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {ind.rsi != null && (
            <IndicatorBadge label="RSI(14)" value={Number(ind.rsi).toFixed(1)} signal={ind.rsi_zone} />
          )}
          {ind.macd_signal && (
            <IndicatorBadge label="MACD" value={ind.macd_signal} signal={ind.macd_signal?.includes('bull') ? 'bullish' : ind.macd_signal?.includes('bear') ? 'bearish' : undefined} />
          )}
          {ind.kdj_k != null && (
            <IndicatorBadge label="KDJ" value={`K:${Number(ind.kdj_k).toFixed(0)} D:${Number(ind.kdj_d).toFixed(0)} J:${Number(ind.kdj_j).toFixed(0)}`} signal={ind.kdj_signal} />
          )}
          {ind.bollinger_pct_b != null && (
            <IndicatorBadge label="Bollinger %B" value={Number(ind.bollinger_pct_b).toFixed(2)} signal={ind.bollinger_pct_b > 0.8 ? 'overbought' : ind.bollinger_pct_b < 0.2 ? 'oversold' : undefined} />
          )}
          {ind.ma_alignment && (
            <IndicatorBadge label="MA Alignment" value={ind.ma_alignment} signal={ind.ma_alignment === 'bullish' ? 'bullish' : ind.ma_alignment === 'bearish' ? 'bearish' : undefined} />
          )}
          {ind.golden_cross && (
            <IndicatorBadge label="Cross Signal" value={ind.golden_cross} signal={ind.golden_cross.includes('golden') ? 'bullish' : 'bearish'} />
          )}
        </div>
      </div>

      {/* Support & Resistance */}
      {sr.levels && Array.isArray(sr.levels) && sr.levels.length > 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-4">{t('technical.sr')}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-accent-green text-xs mb-2 uppercase tracking-wider">{t('technical.support')}</h4>
              <div className="space-y-1">
                {sr.levels.filter((l: any) => l.role === 'support' || l.type === 'support').slice(0, 5).map((l: any, i: number) => {
                  const price = Number(l.level ?? l.price);
                  return (
                    <div key={i} className="flex justify-between text-sm">
                      <span className="text-text-secondary">{l.sources?.join(', ') || l.source || 'Level'}</span>
                      <span className="text-accent-green font-medium">{isNaN(price) ? 'N/A' : price.toFixed(2)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
            <div>
              <h4 className="text-accent-red text-xs mb-2 uppercase tracking-wider">{t('technical.resistance')}</h4>
              <div className="space-y-1">
                {sr.levels.filter((l: any) => l.role === 'resistance' || l.type === 'resistance').slice(0, 5).map((l: any, i: number) => {
                  const price = Number(l.level ?? l.price);
                  return (
                    <div key={i} className="flex justify-between text-sm">
                      <span className="text-text-secondary">{l.sources?.join(', ') || l.source || 'Level'}</span>
                      <span className="text-accent-red font-medium">{isNaN(price) ? 'N/A' : price.toFixed(2)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Institutional Flow (CN Only) */}
      {flow.classification && flow.classification !== 'unavailable' && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-4">{t('technical.fund_flow')}</h3>
          <div className="flex items-center gap-4 mb-3">
            <span className="text-text-secondary text-sm">{t('technical.classification')}:</span>
            <span className={`font-medium ${
              flow.classification === 'accumulating' ? 'text-accent-green' :
              flow.classification === 'distributing' ? 'text-accent-red' : 'text-text-secondary'
            }`}>{flow.classification}</span>
          </div>
          {flow.main_force_flow && (
            <div className="grid grid-cols-3 gap-3 text-sm">
              {Object.entries(flow.main_force_flow).map(([period, val]) => (
                <div key={period} className="bg-bg-primary rounded p-2 text-center">
                  <div className="text-text-muted text-xs">{period}</div>
                  <div className={Number(val) >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                    {Number(val) >= 0 ? '+' : ''}{Number(val).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Chip Distribution (CN Only) */}
      {chip.health && chip.health !== 'unavailable' && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-3">{t('technical.chip')}</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            {chip.profit_ratio != null && (
              <div className="bg-bg-primary rounded p-3">
                <div className="text-text-muted text-xs">{t('technical.profit_ratio')}</div>
                <div className="text-text-primary font-medium">{Number(chip.profit_ratio).toFixed(1)}%</div>
              </div>
            )}
            {chip.avg_cost != null && (
              <div className="bg-bg-primary rounded p-3">
                <div className="text-text-muted text-xs">{t('technical.avg_cost')}</div>
                <div className="text-text-primary font-medium">{Number(chip.avg_cost).toFixed(2)}</div>
              </div>
            )}
            {chip.concentration != null && (
              <div className="bg-bg-primary rounded p-3">
                <div className="text-text-muted text-xs">{t('technical.concentration')}</div>
                <div className="text-text-primary font-medium">{Number(chip.concentration).toFixed(1)}%</div>
              </div>
            )}
            {chip.health && (
              <div className="bg-bg-primary rounded p-3">
                <div className="text-text-muted text-xs">{t('technical.chip_health')}</div>
                <div className={`font-medium ${chip.health === 'healthy' ? 'text-accent-green' : chip.health === 'risky' ? 'text-accent-red' : 'text-text-secondary'}`}>{chip.health}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pattern Recognition */}
      {detail.patterns && detail.patterns.length > 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-3">{t('technical.patterns')}</h3>
          <div className="space-y-2">
            {detail.patterns.map((p, i) => (
              <div key={i} className="flex items-center gap-3 bg-bg-primary rounded-lg p-3">
                <div className={`w-2 h-2 rounded-full ${
                  p.type === 'bullish' ? 'bg-accent-green' : p.type === 'bearish' ? 'bg-accent-red' : 'bg-accent-yellow'
                }`} />
                <span className="text-text-primary text-sm font-medium flex-1">{p.pattern}</span>
                <span className="text-text-muted text-xs">{p.date}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  p.type === 'bullish' ? 'bg-accent-green/10 text-accent-green' :
                  p.type === 'bearish' ? 'bg-accent-red/10 text-accent-red' :
                  'bg-accent-yellow/10 text-accent-yellow'
                }`}>{p.type}</span>
                <span className="text-text-muted text-xs">{p.reliability}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
