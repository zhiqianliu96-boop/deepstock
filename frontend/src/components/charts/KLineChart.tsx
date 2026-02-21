import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { ChartData } from '../../types/analysis';

interface KLineChartProps {
  chartData: ChartData;
}

const KLineChart: React.FC<KLineChartProps> = ({ chartData }) => {
  const option = useMemo(() => {
    if (!chartData || !chartData.dates || !chartData.ohlcv || chartData.ohlcv.length === 0) {
      return null;
    }

    const { dates, ohlcv, volumes, ma5, ma10, ma20, ma60, macd_dif, macd_dea, macd_hist, support_levels, resistance_levels } = chartData;

    const hasMacd = macd_dif && macd_dea && macd_hist && macd_dif.length > 0;

    // Volume colors based on candle direction (close >= open = green, else red)
    const volumeColors = ohlcv.map((item) => {
      const [open, close] = item;
      return close >= open ? '#10b981' : '#ef4444';
    });

    // Build MA line series
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
          name,
          type: 'line',
          data,
          smooth: true,
          lineStyle: { width: 1, color },
          symbol: 'none',
          xAxisIndex: 0,
          yAxisIndex: 0,
        });
      }
    });

    // Support & resistance marklines on candlestick
    const markLines: any[] = [];
    if (support_levels && support_levels.length > 0) {
      support_levels.forEach((level) => {
        markLines.push({
          yAxis: level,
          lineStyle: { color: '#10b981', type: 'dashed', width: 1 },
          label: { show: true, formatter: `S: ${level.toFixed(2)}`, color: '#10b981', fontSize: 10, position: 'insideEndTop' },
        });
      });
    }
    if (resistance_levels && resistance_levels.length > 0) {
      resistance_levels.forEach((level) => {
        markLines.push({
          yAxis: level,
          lineStyle: { color: '#ef4444', type: 'dashed', width: 1 },
          label: { show: true, formatter: `R: ${level.toFixed(2)}`, color: '#ef4444', fontSize: 10, position: 'insideEndTop' },
        });
      });
    }

    // MACD series
    const macdSeries: any[] = [];
    if (hasMacd) {
      macdSeries.push(
        {
          name: 'MACD Hist',
          type: 'bar',
          data: macd_hist,
          xAxisIndex: 1,
          yAxisIndex: 3,
          itemStyle: {
            color: (params: any) => {
              return params.data >= 0 ? '#10b981' : '#ef4444';
            },
          },
          barWidth: '60%',
        },
        {
          name: 'DIF',
          type: 'line',
          data: macd_dif,
          xAxisIndex: 1,
          yAxisIndex: 3,
          lineStyle: { width: 1, color: '#f59e0b' },
          symbol: 'none',
          smooth: true,
        },
        {
          name: 'DEA',
          type: 'line',
          data: macd_dea,
          xAxisIndex: 1,
          yAxisIndex: 3,
          lineStyle: { width: 1, color: '#8b5cf6' },
          symbol: 'none',
          smooth: true,
        }
      );
    }

    const grids = [
      // Main chart grid
      { left: '8%', right: '4%', top: '8%', height: '55%' },
    ];

    if (hasMacd) {
      // MACD grid
      grids.push({ left: '8%', right: '4%', top: '73%', height: '20%' });
    }

    const xAxes: any[] = [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#94a3b8', fontSize: 10 },
        splitLine: { show: false },
        boundaryGap: true,
        axisPointer: { label: { show: false } },
      },
    ];

    if (hasMacd) {
      xAxes.push({
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { show: false },
        splitLine: { show: false },
        boundaryGap: true,
        axisPointer: { label: { show: false } },
      });
    }

    const yAxes: any[] = [
      // Main chart price axis
      {
        type: 'value',
        gridIndex: 0,
        position: 'right',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94a3b8', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1e293b' } },
        scale: true,
      },
      // Volume axis (overlaid on main chart)
      {
        type: 'value',
        gridIndex: 0,
        position: 'left',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false },
        scale: true,
        max: (value: any) => value.max * 4, // shrink volume bars to bottom ~25%
      },
    ];

    if (hasMacd) {
      // Dummy yAxis for grid alignment (some echarts versions need matching indices)
      yAxes.push(
        {
          type: 'value',
          gridIndex: 1,
          show: false,
        },
        {
          type: 'value',
          gridIndex: 1,
          position: 'right',
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: '#94a3b8', fontSize: 10 },
          splitLine: { lineStyle: { color: '#1e293b' } },
          scale: true,
        }
      );
    }

    const dataZoomStartPercent = Math.max(0, 100 - Math.min(100, Math.round((60 / dates.length) * 100)));

    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', crossStyle: { color: '#475569' } },
        backgroundColor: '#1e293b',
        borderColor: '#334155',
        textStyle: { color: '#e2e8f0', fontSize: 12 },
        formatter: (params: any[]) => {
          if (!params || params.length === 0) return '';
          const dateStr = params[0].axisValue;
          let html = `<div style="font-weight:600;margin-bottom:4px;">${dateStr}</div>`;

          const candleParam = params.find((p: any) => p.seriesName === 'K-Line');
          if (candleParam && candleParam.data) {
            const [open, close, low, high] = candleParam.data;
            const color = close >= open ? '#10b981' : '#ef4444';
            html += `<div style="color:${color}">Open: ${open?.toFixed(2)} &nbsp; Close: ${close?.toFixed(2)}</div>`;
            html += `<div style="color:${color}">Low: ${low?.toFixed(2)} &nbsp; High: ${high?.toFixed(2)}</div>`;
          }

          const volParam = params.find((p: any) => p.seriesName === 'Volume');
          if (volParam && volParam.data != null) {
            html += `<div>Volume: ${Number(volParam.data).toLocaleString()}</div>`;
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
        top: 0,
        textStyle: { color: '#94a3b8', fontSize: 10 },
        itemWidth: 14,
        itemHeight: 8,
      },
      grid: grids,
      xAxis: xAxes,
      yAxis: yAxes,
      dataZoom: [
        {
          type: 'slider',
          xAxisIndex: hasMacd ? [0, 1] : [0],
          bottom: '2%',
          height: 20,
          start: dataZoomStartPercent,
          end: 100,
          borderColor: '#334155',
          backgroundColor: '#0f172a',
          fillerColor: 'rgba(59,130,246,0.15)',
          handleStyle: { color: '#3b82f6' },
          textStyle: { color: '#94a3b8' },
          dataBackground: {
            lineStyle: { color: '#334155' },
            areaStyle: { color: '#1e293b' },
          },
        },
        {
          type: 'inside',
          xAxisIndex: hasMacd ? [0, 1] : [0],
          start: dataZoomStartPercent,
          end: 100,
        },
      ],
      series: [
        // Candlestick
        {
          name: 'K-Line',
          type: 'candlestick',
          data: ohlcv,
          xAxisIndex: 0,
          yAxisIndex: 0,
          itemStyle: {
            color: '#10b981',       // up fill
            color0: '#ef4444',      // down fill
            borderColor: '#10b981', // up border
            borderColor0: '#ef4444', // down border
          },
          markLine: markLines.length > 0
            ? {
                silent: true,
                symbol: 'none',
                data: markLines,
              }
            : undefined,
        },
        // Volume bars overlaid on main chart
        {
          name: 'Volume',
          type: 'bar',
          data: volumes || [],
          xAxisIndex: 0,
          yAxisIndex: 1,
          barWidth: '50%',
          itemStyle: {
            color: (params: any) => {
              return volumeColors[params.dataIndex] || '#64748b';
            },
            opacity: 0.5,
          },
        },
        // MA lines
        ...maSeries,
        // MACD series
        ...macdSeries,
      ],
    };
  }, [chartData]);

  if (!chartData || !chartData.dates || !chartData.ohlcv || chartData.ohlcv.length === 0) {
    return (
      <div className="w-full h-[500px] flex items-center justify-center text-slate-400">
        <p>No K-Line chart data available</p>
      </div>
    );
  }

  if (!option) {
    return (
      <div className="w-full h-[500px] flex items-center justify-center text-slate-400">
        <p>Loading chart...</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[500px]">
      <ReactECharts
        option={option}
        style={{ width: '100%', height: '100%' }}
        notMerge
        lazyUpdate
      />
    </div>
  );
};

export default KLineChart;
