import React, { useMemo, useState, useCallback, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import type { ChartData } from '../../types/analysis';
import { useLocale } from '../../i18n/LocaleContext';
import { getStockIntraday } from '../../api/client';

type Period = 'intraday' | '1W' | '1M' | '3M' | '6M' | '1Y' | '2Y';

interface KLineChartProps {
  chartData: ChartData;
  stockCode?: string;
}

function sliceChartData(chartData: ChartData, days: number): ChartData {
  const total = chartData.dates.length;
  const start = Math.max(0, total - days);
  const slice = <T,>(arr?: T[]): T[] | undefined =>
    arr && arr.length > 0 ? arr.slice(start) : arr;

  return {
    dates: chartData.dates.slice(start),
    ohlcv: chartData.ohlcv.slice(start),
    volumes: chartData.volumes.slice(start),
    ma5: slice(chartData.ma5),
    ma10: slice(chartData.ma10),
    ma20: slice(chartData.ma20),
    ma60: slice(chartData.ma60),
    ma120: slice(chartData.ma120),
    ma250: slice(chartData.ma250),
    macd_dif: slice(chartData.macd_dif),
    macd_dea: slice(chartData.macd_dea),
    macd_hist: slice(chartData.macd_hist),
    support_levels: chartData.support_levels,
    resistance_levels: chartData.resistance_levels,
  };
}

const KLineChart: React.FC<KLineChartProps> = ({ chartData, stockCode }) => {
  const { t } = useLocale();
  const [period, setPeriod] = useState<Period>('3M');
  const [intradayData, setIntradayData] = useState<ChartData | null>(null);
  const [intradayLoading, setIntradayLoading] = useState(false);

  const loadIntraday = useCallback(async () => {
    if (!stockCode) return;
    setIntradayLoading(true);
    try {
      const res = await getStockIntraday(stockCode, 5);
      if (res.data && res.data.length > 0) {
        const dates = res.data.map((d: any) => d.time || '');
        const ohlcv = res.data.map((d: any) => [d.open, d.close, d.low, d.high]);
        const volumes = res.data.map((d: any) => d.volume || 0);
        setIntradayData({ dates, ohlcv, volumes });
      }
    } catch (e) {
      console.error('Intraday fetch error:', e);
    } finally {
      setIntradayLoading(false);
    }
  }, [stockCode]);

  useEffect(() => {
    if (period === 'intraday') {
      loadIntraday();
    }
  }, [period, loadIntraday]);

  const periodDays: Record<Period, number> = {
    'intraday': 0,
    '1W': 5,
    '1M': 22,
    '3M': 66,
    '6M': 132,
    '1Y': 252,
    '2Y': 504,
  };

  const activeData = useMemo(() => {
    if (period === 'intraday') return intradayData;
    const days = periodDays[period];
    if (days === 0 || !chartData?.dates?.length) return chartData;
    return sliceChartData(chartData, days);
  }, [period, chartData, intradayData]);

  const option = useMemo(() => {
    if (!activeData || !activeData.dates || !activeData.ohlcv || activeData.ohlcv.length === 0) {
      return null;
    }

    const { dates, ohlcv, volumes, ma5, ma10, ma20, ma60, macd_dif, macd_dea, macd_hist, support_levels, resistance_levels } = activeData;

    const hasMacd = macd_dif && macd_dea && macd_hist && macd_dif.length > 0;

    const volumeColors = ohlcv.map((item) => {
      const [open, close] = item;
      return (close ?? 0) >= (open ?? 0) ? '#10b981' : '#ef4444';
    });

    const maSeries: any[] = [];
    const maConfig = [
      { data: ma5, name: 'MA5', color: '#f59e0b' },
      { data: ma10, name: 'MA10', color: '#06b6d4' },
      { data: ma20, name: 'MA20', color: '#8b5cf6' },
      { data: ma60, name: 'MA60', color: '#ec4899' },
    ];

    maConfig.forEach(({ data, name, color }) => {
      if (data && data.length > 0) {
        maSeries.push({
          name, type: 'line', data, smooth: true,
          lineStyle: { width: 1, color }, symbol: 'none',
          xAxisIndex: 0, yAxisIndex: 0,
        });
      }
    });

    const markLines: any[] = [];
    if (support_levels && support_levels.length > 0) {
      support_levels.forEach((level) => {
        if (level != null) {
          markLines.push({
            yAxis: level,
            lineStyle: { color: '#10b981', type: 'dashed', width: 1 },
            label: { show: true, formatter: `S: ${level.toFixed(2)}`, color: '#10b981', fontSize: 10, position: 'insideEndTop' },
          });
        }
      });
    }
    if (resistance_levels && resistance_levels.length > 0) {
      resistance_levels.forEach((level) => {
        if (level != null) {
          markLines.push({
            yAxis: level,
            lineStyle: { color: '#ef4444', type: 'dashed', width: 1 },
            label: { show: true, formatter: `R: ${level.toFixed(2)}`, color: '#ef4444', fontSize: 10, position: 'insideEndTop' },
          });
        }
      });
    }

    const macdSeries: any[] = [];
    if (hasMacd) {
      macdSeries.push(
        {
          name: 'MACD Hist', type: 'bar', data: macd_hist,
          xAxisIndex: 1, yAxisIndex: 3,
          itemStyle: { color: (params: any) => params.data >= 0 ? '#10b981' : '#ef4444' },
          barWidth: '60%',
        },
        {
          name: 'DIF', type: 'line', data: macd_dif,
          xAxisIndex: 1, yAxisIndex: 3,
          lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none', smooth: true,
        },
        {
          name: 'DEA', type: 'line', data: macd_dea,
          xAxisIndex: 1, yAxisIndex: 3,
          lineStyle: { width: 1, color: '#8b5cf6' }, symbol: 'none', smooth: true,
        }
      );
    }

    const grids = [{ left: '8%', right: '4%', top: '8%', height: '55%' }];
    if (hasMacd) grids.push({ left: '8%', right: '4%', top: '73%', height: '20%' });

    const xAxes: any[] = [{
      type: 'category', data: dates, gridIndex: 0,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { show: false }, boundaryGap: true,
      axisPointer: { label: { show: false } },
    }];
    if (hasMacd) {
      xAxes.push({
        type: 'category', data: dates, gridIndex: 1,
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { show: false }, splitLine: { show: false },
        boundaryGap: true, axisPointer: { label: { show: false } },
      });
    }

    const yAxes: any[] = [
      {
        type: 'value', gridIndex: 0, position: 'right',
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { color: '#94a3b8', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1e293b' } }, scale: true,
      },
      {
        type: 'value', gridIndex: 0, position: 'left',
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { show: false }, splitLine: { show: false },
        scale: true, max: (value: any) => value.max * 4,
      },
    ];
    if (hasMacd) {
      yAxes.push(
        { type: 'value', gridIndex: 1, show: false },
        {
          type: 'value', gridIndex: 1, position: 'right',
          axisLine: { show: false }, axisTick: { show: false },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { lineStyle: { color: '#1e293b' } }, scale: true,
        }
      );
    }

    const dataZoomStartPercent = Math.max(0, 100 - Math.min(100, Math.round((60 / dates.length) * 100)));

    const openLabel = t('kline.open');
    const closeLabel = t('kline.close');
    const lowLabel = t('kline.low');
    const highLabel = t('kline.high');
    const volumeLabel = t('kline.volume');

    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', crossStyle: { color: '#475569' } },
        backgroundColor: '#1e293b', borderColor: '#334155',
        textStyle: { color: '#e2e8f0', fontSize: 12 },
        formatter: (params: any[]) => {
          if (!params || params.length === 0) return '';
          const dateStr = params[0].axisValue;
          let html = `<div style="font-weight:600;margin-bottom:4px;">${dateStr}</div>`;
          const candleParam = params.find((p: any) => p.seriesName === 'K-Line');
          if (candleParam && candleParam.data) {
            const [open, close, low, high] = candleParam.data;
            const color = (close ?? 0) >= (open ?? 0) ? '#10b981' : '#ef4444';
            html += `<div style="color:${color}">${openLabel}: ${open?.toFixed(2)} &nbsp; ${closeLabel}: ${close?.toFixed(2)}</div>`;
            html += `<div style="color:${color}">${lowLabel}: ${low?.toFixed(2)} &nbsp; ${highLabel}: ${high?.toFixed(2)}</div>`;
          }
          const volParam = params.find((p: any) => p.seriesName === volumeLabel);
          if (volParam && volParam.data != null) {
            html += `<div>${volumeLabel}: ${Number(volParam.data).toLocaleString()}</div>`;
          }
          const indicatorParams = params.filter((p: any) =>
            ['MA5', 'MA10', 'MA20', 'MA60', 'DIF', 'DEA', 'MACD Hist'].includes(p.seriesName)
          );
          indicatorParams.forEach((p: any) => {
            if (p.data != null) {
              html += `<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:4px;"></span>${p.seriesName}: ${Number(p.data).toFixed(2)}</div>`;
            }
          });
          return html;
        },
      },
      legend: {
        data: [
          ...maConfig.filter(({ data }) => data && data.length > 0).map(({ name }) => name),
          ...(hasMacd ? ['DIF', 'DEA'] : []),
        ],
        top: 0, textStyle: { color: '#94a3b8', fontSize: 10 },
        itemWidth: 14, itemHeight: 8,
      },
      grid: grids,
      xAxis: xAxes,
      yAxis: yAxes,
      dataZoom: [
        {
          type: 'slider', xAxisIndex: hasMacd ? [0, 1] : [0],
          bottom: '2%', height: 20,
          start: dataZoomStartPercent, end: 100,
          borderColor: '#334155', backgroundColor: '#0f172a',
          fillerColor: 'rgba(59,130,246,0.15)',
          handleStyle: { color: '#3b82f6' },
          textStyle: { color: '#94a3b8' },
          dataBackground: { lineStyle: { color: '#334155' }, areaStyle: { color: '#1e293b' } },
        },
        {
          type: 'inside', xAxisIndex: hasMacd ? [0, 1] : [0],
          start: dataZoomStartPercent, end: 100,
        },
      ],
      series: [
        {
          name: 'K-Line', type: 'candlestick', data: ohlcv,
          xAxisIndex: 0, yAxisIndex: 0,
          itemStyle: {
            color: '#10b981', color0: '#ef4444',
            borderColor: '#10b981', borderColor0: '#ef4444',
          },
          markLine: markLines.length > 0 ? { silent: true, symbol: 'none', data: markLines } : undefined,
        },
        {
          name: volumeLabel, type: 'bar', data: volumes || [],
          xAxisIndex: 0, yAxisIndex: 1, barWidth: '50%',
          itemStyle: {
            color: (params: any) => volumeColors[params.dataIndex] || '#64748b',
            opacity: 0.5,
          },
        },
        ...maSeries,
        ...macdSeries,
      ],
    };
  }, [activeData, t]);

  const periods: { key: Period; label: string }[] = [
    { key: 'intraday', label: t('kline.intraday') },
    { key: '1W', label: '1W' },
    { key: '1M', label: '1M' },
    { key: '3M', label: '3M' },
    { key: '6M', label: '6M' },
    { key: '1Y', label: '1Y' },
    { key: '2Y', label: '2Y' },
  ];

  if (!chartData || !chartData.dates || !chartData.ohlcv || chartData.ohlcv.length === 0) {
    return (
      <div className="w-full h-[500px] flex items-center justify-center text-slate-400">
        <p>{t('chart.no_kline')}</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Period selector */}
      <div className="flex gap-1 mb-2">
        {periods.map((p) => (
          <button
            key={p.key}
            onClick={() => setPeriod(p.key)}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              period === p.key
                ? 'bg-accent-cyan/20 text-accent-cyan'
                : 'text-text-muted hover:text-text-secondary hover:bg-bg-card-hover'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Chart */}
      {intradayLoading ? (
        <div className="w-full h-[500px] flex items-center justify-center text-slate-400">
          <p>{t('chart.loading')}</p>
        </div>
      ) : option ? (
        <div className="w-full h-[500px]">
          <ReactECharts option={option} style={{ width: '100%', height: '100%' }} notMerge lazyUpdate />
        </div>
      ) : (
        <div className="w-full h-[500px] flex items-center justify-center text-slate-400">
          <p>{t('chart.loading')}</p>
        </div>
      )}
    </div>
  );
};

export default KLineChart;
