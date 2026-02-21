import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface FinancialChartProps {
  metrics: Record<string, any>;
}

interface PeriodDataPoint {
  period: string;
  value: number;
}

const formatNumber = (value: number): string => {
  if (Math.abs(value) >= 1e9) {
    return (value / 1e9).toFixed(2) + 'B';
  }
  if (Math.abs(value) >= 1e6) {
    return (value / 1e6).toFixed(2) + 'M';
  }
  if (Math.abs(value) >= 1e3) {
    return (value / 1e3).toFixed(1) + 'K';
  }
  return value.toLocaleString();
};

const FinancialChart: React.FC<FinancialChartProps> = ({ metrics }) => {
  const chartConfig = useMemo(() => {
    if (!metrics) return null;

    // Strategy 1: Structured arrays with period data
    const revenueData: PeriodDataPoint[] | undefined =
      metrics.revenue_data || metrics.revenue_history;
    const profitData: PeriodDataPoint[] | undefined =
      metrics.profit_data || metrics.profit_history;
    const grossMarginData: PeriodDataPoint[] | undefined =
      metrics.gross_margin_data || metrics.margins_history?.gross;
    const netMarginData: PeriodDataPoint[] | undefined =
      metrics.net_margin_data || metrics.margins_history?.net;

    if (revenueData && Array.isArray(revenueData) && revenueData.length > 0) {
      const periods = revenueData.map((d) => d.period);
      const revenues = revenueData.map((d) => d.value);
      const profits = profitData
        ? profitData.map((d) => d.value)
        : new Array(periods.length).fill(0);
      const grossMargins = grossMarginData
        ? grossMarginData.map((d) => (typeof d.value === 'number' ? d.value : 0))
        : null;
      const netMargins = netMarginData
        ? netMarginData.map((d) => (typeof d.value === 'number' ? d.value : 0))
        : null;

      return buildFullChartOption(periods, revenues, profits, grossMargins, netMargins);
    }

    // Strategy 2: Simple arrays at top-level keys
    if (
      Array.isArray(metrics.revenue) &&
      metrics.revenue.length > 0 &&
      Array.isArray(metrics.periods)
    ) {
      const periods: string[] = metrics.periods;
      const revenues: number[] = metrics.revenue;
      const profits: number[] = metrics.net_profit || metrics.profit || [];
      const grossMargins: number[] | null = metrics.gross_margin || null;
      const netMargins: number[] | null = metrics.net_margin || null;
      return buildFullChartOption(periods, revenues, profits, grossMargins, netMargins);
    }

    // Strategy 3: Fallback — extract scalar metrics for card display
    return null;
  }, [metrics]);

  if (!metrics) {
    return (
      <div className="w-full h-[400px] flex items-center justify-center text-slate-400">
        <p>Financial chart data not available</p>
      </div>
    );
  }

  // If we couldn't build a chart, show metric cards as fallback
  if (!chartConfig) {
    return <MetricCards metrics={metrics} />;
  }

  return (
    <div className="w-full h-[400px]">
      <ReactECharts
        option={chartConfig}
        style={{ width: '100%', height: '100%' }}
        notMerge
        lazyUpdate
      />
    </div>
  );
};

function buildFullChartOption(
  periods: string[],
  revenues: number[],
  profits: number[],
  grossMargins: number[] | null,
  netMargins: number[] | null
) {
  const series: any[] = [
    {
      name: 'Revenue',
      type: 'bar',
      data: revenues,
      yAxisIndex: 0,
      barGap: '10%',
      itemStyle: {
        color: 'rgba(59,130,246,0.7)',
        borderRadius: [2, 2, 0, 0],
      },
    },
  ];

  if (profits && profits.length > 0) {
    series.push({
      name: 'Net Profit',
      type: 'bar',
      data: profits,
      yAxisIndex: 0,
      itemStyle: {
        color: 'rgba(16,185,129,0.7)',
        borderRadius: [2, 2, 0, 0],
      },
    });
  }

  const hasMargins = (grossMargins && grossMargins.length > 0) || (netMargins && netMargins.length > 0);

  if (grossMargins && grossMargins.length > 0) {
    series.push({
      name: 'Gross Margin %',
      type: 'line',
      data: grossMargins.map((v) => (typeof v === 'number' ? +(v * (v > 1 ? 1 : 100)).toFixed(2) : null)),
      yAxisIndex: 1,
      lineStyle: { width: 2, color: '#f59e0b' },
      itemStyle: { color: '#f59e0b' },
      symbol: 'circle',
      symbolSize: 6,
      smooth: true,
    });
  }

  if (netMargins && netMargins.length > 0) {
    series.push({
      name: 'Net Margin %',
      type: 'line',
      data: netMargins.map((v) => (typeof v === 'number' ? +(v * (v > 1 ? 1 : 100)).toFixed(2) : null)),
      yAxisIndex: 1,
      lineStyle: { width: 2, color: '#a78bfa' },
      itemStyle: { color: '#a78bfa' },
      symbol: 'circle',
      symbolSize: 6,
      smooth: true,
    });
  }

  const yAxes: any[] = [
    {
      type: 'value',
      position: 'left',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10,
        formatter: (value: number) => formatNumber(value),
      },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },
  ];

  if (hasMargins) {
    yAxes.push({
      type: 'value',
      position: 'right',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10,
        formatter: (value: number) => `${value}%`,
      },
      splitLine: { show: false },
      min: 0,
      max: 100,
    });
  }

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (params: any[]) => {
        if (!params || params.length === 0) return '';
        let html = `<div style="font-weight:600;margin-bottom:4px;">${params[0].axisValue}</div>`;
        params.forEach((p: any) => {
          if (p.data == null) return;
          const isPercent = p.seriesName.includes('%');
          const val = isPercent
            ? `${Number(p.data).toFixed(2)}%`
            : formatNumber(Number(p.data));
          html += `<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:6px;"></span>${p.seriesName}: ${val}</div>`;
        });
        return html;
      },
    },
    legend: {
      top: 0,
      textStyle: { color: '#94a3b8', fontSize: 11 },
      itemWidth: 14,
      itemHeight: 8,
    },
    grid: {
      left: '8%',
      right: hasMargins ? '8%' : '4%',
      top: '14%',
      bottom: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: periods,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { show: false },
    },
    yAxis: yAxes,
    series,
  };
}

// Fallback: styled metric cards grid
const MetricCards: React.FC<{ metrics: Record<string, any> }> = ({ metrics }) => {
  const displayMetrics = useMemo(() => {
    const result: { label: string; value: string }[] = [];

    const keyMap: Record<string, string> = {
      revenue: 'Revenue',
      revenue_ttm: 'Revenue (TTM)',
      net_income: 'Net Income',
      net_profit: 'Net Profit',
      gross_margin: 'Gross Margin',
      net_margin: 'Net Margin',
      operating_margin: 'Operating Margin',
      revenue_growth_yoy: 'Revenue Growth YoY',
      eps: 'EPS',
      pe_ratio: 'P/E Ratio',
      pb_ratio: 'P/B Ratio',
      roe: 'ROE',
      roa: 'ROA',
      debt_to_equity: 'Debt/Equity',
      current_ratio: 'Current Ratio',
      free_cash_flow: 'Free Cash Flow',
      dividend_yield: 'Dividend Yield',
      market_cap: 'Market Cap',
    };

    Object.entries(keyMap).forEach(([key, label]) => {
      const val = metrics[key];
      if (val != null && typeof val === 'number') {
        let formatted: string;
        if (key.includes('margin') || key.includes('growth') || key.includes('yield') || key === 'roe' || key === 'roa') {
          formatted = (val > 1 ? val : val * 100).toFixed(2) + '%';
        } else if (key.includes('ratio')) {
          formatted = val.toFixed(2);
        } else if (Math.abs(val) >= 1e6) {
          formatted = formatNumber(val);
        } else {
          formatted = val.toLocaleString(undefined, { maximumFractionDigits: 2 });
        }
        result.push({ label, value: formatted });
      }
    });

    return result;
  }, [metrics]);

  if (displayMetrics.length === 0) {
    return (
      <div className="w-full h-[400px] flex items-center justify-center text-slate-400">
        <p>Financial chart data not available</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[400px] overflow-y-auto p-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {displayMetrics.map((m) => (
          <div
            key={m.label}
            className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-3 flex flex-col items-center justify-center"
          >
            <span className="text-xs text-slate-400 mb-1 text-center">{m.label}</span>
            <span className="text-lg font-semibold text-slate-100">{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FinancialChart;
