import { useLocale } from '../../i18n/LocaleContext';
import type { AnalysisResult } from '../../types/analysis';

interface Props {
  result: AnalysisResult;
}

function formatMarketCap(val: number | null | undefined): string {
  if (val == null) return 'N/A';
  if (val >= 1e12) return (val / 1e12).toFixed(2) + 'T';
  if (val >= 1e9) return (val / 1e9).toFixed(2) + 'B';
  if (val >= 1e8) return (val / 1e8).toFixed(2) + '亿';
  if (val >= 1e6) return (val / 1e6).toFixed(0) + 'M';
  return String(val);
}

function formatNum(val: any, decimals = 2): string {
  if (val == null || val === '') return '—';
  const n = Number(val);
  if (isNaN(n)) return '—';
  return n.toFixed(decimals);
}

export default function StockInfoBar({ result }: Props) {
  const { t } = useLocale();
  const ai = result.ai_synthesis;
  const rt = (ai as any)?.realtime_quote || {};

  // Try to get price from various sources
  const price = rt.price
    ?? result.fundamental_detail?.metrics?.price
    ?? null;

  // Compute change from chart data if available
  const chartData = result.chart_data || result.technical_detail?.chart_data;
  let change: number | null = null;
  let changePct: number | null = null;

  if (chartData?.ohlcv && chartData.ohlcv.length >= 2) {
    const lastCandle = chartData.ohlcv[chartData.ohlcv.length - 1];
    const prevCandle = chartData.ohlcv[chartData.ohlcv.length - 2];
    const lastClose = lastCandle[1]; // [open, close, low, high]
    const prevClose = prevCandle[1];
    if (lastClose != null && prevClose != null && prevClose !== 0) {
      change = lastClose - prevClose;
      changePct = (change / prevClose) * 100;
    }
  }

  const isUp = change != null ? change >= 0 : true;
  const priceColor = isUp ? 'text-accent-green' : 'text-accent-red';

  const metrics = result.fundamental_detail?.metrics || {};
  const pe = metrics.pe ?? rt.pe;
  const pb = metrics.pb ?? rt.pb;
  const marketCap = metrics.market_cap ?? rt.market_cap;
  const volume = rt.volume;
  const turnoverRate = rt.turnover_rate;
  const high52 = rt['52w_high'];
  const low52 = rt['52w_low'];

  const verdictColors: Record<string, string> = {
    strong_buy: 'text-accent-green',
    buy: 'text-accent-cyan',
    hold: 'text-accent-yellow',
    sell: 'text-orange-400',
    strong_sell: 'text-accent-red',
  };

  const verdictKeys: Record<string, string> = {
    strong_buy: 'verdict.strong_buy',
    buy: 'verdict.buy',
    hold: 'verdict.hold',
    sell: 'verdict.sell',
    strong_sell: 'verdict.strong_sell',
  };

  return (
    <div className="bg-bg-card border border-border rounded-xl p-4">
      {/* Row 1: Stock identity + price */}
      <div className="flex items-baseline justify-between flex-wrap gap-3 mb-3">
        <div className="flex items-baseline gap-3">
          <h2 className="text-xl font-bold text-text-primary">
            {result.name || result.code}
          </h2>
          <span className="text-text-muted text-sm">{result.code}</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan">
            {result.market}
          </span>
          {result.sector && (
            <span className="text-text-muted text-xs">{result.sector}</span>
          )}
        </div>

        <div className="flex items-baseline gap-4">
          {/* Verdict + Confidence */}
          {ai?.verdict && (
            <span className={`text-sm font-semibold ${verdictColors[ai.verdict] || 'text-text-secondary'}`}>
              {t((verdictKeys[ai.verdict] || 'verdict.hold') as any)}
            </span>
          )}
          {ai?.confidence != null && (
            <span className="text-text-muted text-xs">
              {t('verdict.confidence')}: {(ai.confidence * 100).toFixed(0)}%
            </span>
          )}
          <span className="text-text-muted text-xs">
            {t('verdict.composite')}: <span className="text-text-primary font-medium">{result.composite_score.toFixed(1)}</span>/100
          </span>
        </div>
      </div>

      {/* Row 2: Price + change */}
      <div className="flex items-baseline gap-4 mb-3">
        {price != null && (
          <span className={`text-3xl font-bold font-mono-num ${priceColor}`}>
            {formatNum(price)}
          </span>
        )}
        {change != null && (
          <span className={`text-sm font-medium font-mono-num ${priceColor}`}>
            {isUp ? '+' : ''}{formatNum(change)}
          </span>
        )}
        {changePct != null && (
          <span className={`text-sm font-medium font-mono-num ${priceColor}`}>
            ({isUp ? '+' : ''}{formatNum(changePct)}%)
          </span>
        )}
      </div>

      {/* Row 3: Key metrics bar */}
      <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs">
        {pe != null && (
          <span className="text-text-muted">
            PE <span className="text-text-secondary font-mono-num">{formatNum(pe, 1)}</span>
          </span>
        )}
        {pb != null && (
          <span className="text-text-muted">
            PB <span className="text-text-secondary font-mono-num">{formatNum(pb)}</span>
          </span>
        )}
        {marketCap != null && (
          <span className="text-text-muted">
            {t('fundamental.market_cap')} <span className="text-text-secondary font-mono-num">{formatMarketCap(marketCap)}</span>
          </span>
        )}
        {volume != null && (
          <span className="text-text-muted">
            {t('kline.volume')} <span className="text-text-secondary font-mono-num">{Number(volume).toLocaleString()}</span>
          </span>
        )}
        {turnoverRate != null && (
          <span className="text-text-muted">
            {t('stockinfo.turnover_rate')} <span className="text-text-secondary font-mono-num">{formatNum(turnoverRate, 2)}%</span>
          </span>
        )}
        {high52 != null && low52 != null && (
          <span className="text-text-muted">
            52W <span className="text-accent-red font-mono-num">{formatNum(low52)}</span>
            {' - '}
            <span className="text-accent-green font-mono-num">{formatNum(high52)}</span>
          </span>
        )}
      </div>

      {/* AI Summary inline */}
      {ai?.summary && (
        <p className="text-text-secondary text-sm mt-3 leading-relaxed border-t border-border/50 pt-3">
          {ai.summary}
        </p>
      )}
    </div>
  );
}
