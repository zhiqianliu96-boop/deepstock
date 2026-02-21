import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { useLocale } from '../../i18n/LocaleContext';

interface RadarChartProps {
  fundamental: number;
  technical: number;
  sentiment: number;
  fundamentalDetail?: any;
  technicalDetail?: any;
  sentimentDetail?: any;
}

const RadarChart: React.FC<RadarChartProps> = ({
  fundamental,
  technical,
  sentiment,
  fundamentalDetail,
  technicalDetail,
  sentimentDetail,
}) => {
  const { t } = useLocale();

  const option = useMemo(() => {
    // Extract sub-dimension scores and normalize to 0-100
    const normalize = (value: number | undefined | null, max: number): number => {
      if (value == null || isNaN(value)) return 0;
      return Math.min(100, Math.max(0, (value / max) * 100));
    };

    // Valuation: from fundamentalDetail.valuation_score (0-25 scale)
    let valuationScore: number;
    if (fundamentalDetail?.valuation_score != null) {
      valuationScore = normalize(fundamentalDetail.valuation_score, 25);
    } else {
      valuationScore = normalize(fundamental, 100) ;
    }

    // Profitability: from fundamentalDetail.profitability_score (0-25 scale)
    let profitabilityScore: number;
    if (fundamentalDetail?.profitability_score != null) {
      profitabilityScore = normalize(fundamentalDetail.profitability_score, 25);
    } else {
      profitabilityScore = normalize(fundamental, 100);
    }

    // Growth: from fundamentalDetail.growth_score (0-25 scale)
    let growthScore: number;
    if (fundamentalDetail?.growth_score != null) {
      growthScore = normalize(fundamentalDetail.growth_score, 25);
    } else {
      growthScore = normalize(fundamental, 100);
    }

    // Trend: from technicalDetail.trend_score (0-30 scale)
    let trendScore: number;
    if (technicalDetail?.trend_score != null) {
      trendScore = normalize(technicalDetail.trend_score, 30);
    } else {
      trendScore = normalize(technical, 100);
    }

    // Momentum: from technicalDetail.momentum_score (0-20 scale)
    let momentumScore: number;
    if (technicalDetail?.momentum_score != null) {
      momentumScore = normalize(technicalDetail.momentum_score, 20);
    } else {
      momentumScore = normalize(technical, 100);
    }

    // Sentiment: already 0-100 scale
    const sentimentScore = normalize(
      sentimentDetail?.total ?? sentimentDetail?.score ?? sentiment,
      100
    );

    const indicatorNames = [
      t('radar.valuation'),
      t('radar.profitability'),
      t('radar.growth'),
      t('radar.trend'),
      t('radar.momentum'),
      t('radar.sentiment'),
    ];

    const dataValues = [
      +valuationScore.toFixed(1),
      +profitabilityScore.toFixed(1),
      +growthScore.toFixed(1),
      +trendScore.toFixed(1),
      +momentumScore.toFixed(1),
      +sentimentScore.toFixed(1),
    ];

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#1e293b',
        borderColor: '#334155',
        textStyle: { color: '#e2e8f0', fontSize: 12 },
        formatter: (params: any) => {
          if (!params || !params.data || !params.data.value) return '';
          let html = `<div style="font-weight:600;margin-bottom:4px;">${params.name}</div>`;
          params.data.value.forEach((val: number, idx: number) => {
            html += `<div>${indicatorNames[idx]}: <span style="font-weight:600;">${val}</span>/100</div>`;
          });
          return html;
        },
      },
      radar: {
        shape: 'polygon',
        center: ['50%', '55%'],
        radius: '65%',
        indicator: indicatorNames.map((name) => ({ name, max: 100 })),
        axisName: {
          color: '#94a3b8',
          fontSize: 11,
          fontWeight: 500,
        },
        splitNumber: 4,
        axisLine: {
          lineStyle: { color: 'rgba(71,85,105,0.5)' },
        },
        splitLine: {
          lineStyle: { color: 'rgba(51,65,85,0.6)' },
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(15,23,42,0.3)', 'rgba(30,41,59,0.2)'],
          },
        },
      },
      series: [
        {
          name: t('radar.series_name'),
          type: 'radar',
          data: [
            {
              name: t('radar.series_name'),
              value: dataValues,
              symbol: 'circle',
              symbolSize: 5,
              lineStyle: {
                width: 2,
                color: '#06b6d4',
              },
              itemStyle: {
                color: '#06b6d4',
                borderColor: '#06b6d4',
                borderWidth: 1,
              },
              areaStyle: {
                color: 'rgba(6,182,212,0.1)',
              },
            },
          ],
        },
      ],
    };
  }, [fundamental, technical, sentiment, fundamentalDetail, technicalDetail, sentimentDetail, t]);

  // Guard: all scores zero or missing
  const hasAnyData = fundamental > 0 || technical > 0 || sentiment > 0;

  if (!hasAnyData) {
    return (
      <div className="w-full h-[350px] flex items-center justify-center text-slate-400">
        <p>{t('chart.no_radar')}</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[350px]">
      <ReactECharts
        option={option}
        style={{ width: '100%', height: '100%' }}
        notMerge
        lazyUpdate
      />
    </div>
  );
};

export default RadarChart;
