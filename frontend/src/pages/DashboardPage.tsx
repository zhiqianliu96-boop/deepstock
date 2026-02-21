import { useAnalysisStore } from '../stores/analysisStore';
import StockSearchBar from '../components/common/StockSearchBar';
import StockInfoBar from '../components/common/StockInfoBar';
import KLineChart from '../components/charts/KLineChart';
import FundamentalPanel from '../components/fundamental/FundamentalPanel';
import TechnicalPanel from '../components/technical/TechnicalPanel';
import SentimentPanel from '../components/sentiment/SentimentPanel';
import { useLocale } from '../i18n/LocaleContext';

export default function DashboardPage() {
  const { result, loading, error, activeTab, setActiveTab } = useAnalysisStore();
  const { t } = useLocale();

  const tabs = [
    { key: 'fundamental' as const, label: t('tab.fundamental') },
    { key: 'technical' as const, label: t('tab.technical') },
    { key: 'sentiment' as const, label: t('tab.sentiment') },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-text-primary tracking-tight">
          Deep<span className="text-accent-cyan">Stock</span>
        </h1>
        <p className="text-text-muted text-sm">{t('dashboard.subtitle')}</p>
      </div>

      {/* Search */}
      <StockSearchBar />

      {/* Error */}
      {error && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-4 text-accent-red text-sm">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-20">
          <div className="w-12 h-12 border-3 border-accent-cyan/20 border-t-accent-cyan rounded-full animate-spin mx-auto mb-4" />
          <p className="text-text-secondary text-sm">{t('dashboard.running')}</p>
          <p className="text-text-muted text-xs mt-1">{t('dashboard.running_sub')}</p>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          {/* 1. Stock Info Bar */}
          <StockInfoBar result={result} />

          {/* 2. K-Line Chart — full width with period selector */}
          <div className="bg-bg-card border border-border rounded-xl p-5">
            <KLineChart
              chartData={result.chart_data || result.technical_detail?.chart_data}
              stockCode={result.code}
            />
          </div>

          {/* 3. Tabbed Analysis Panels */}
          <div>
            <div className="flex border-b border-border mb-6">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-6 py-3 text-sm font-medium transition-all border-b-2 -mb-px ${
                    activeTab === tab.key
                      ? 'text-accent-cyan border-accent-cyan'
                      : 'text-text-muted border-transparent hover:text-text-secondary hover:border-border-light'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === 'fundamental' && result.fundamental_detail && (
              <FundamentalPanel detail={result.fundamental_detail} />
            )}
            {activeTab === 'technical' && result.technical_detail && (
              <TechnicalPanel detail={result.technical_detail} />
            )}
            {activeTab === 'sentiment' && result.sentiment_detail && (
              <SentimentPanel detail={result.sentiment_detail} />
            )}
          </div>

          {/* 4. AI Synthesis Section — full width at bottom */}
          {result.ai_synthesis && (
            <div className="space-y-6">
              {/* Risks + Catalysts side by side */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {result.ai_synthesis.risks && result.ai_synthesis.risks.length > 0 && (
                  <div className="bg-bg-card border border-border rounded-xl p-5">
                    <h3 className="text-accent-red font-medium mb-3">{t('dashboard.key_risks')}</h3>
                    <ul className="space-y-2">
                      {result.ai_synthesis.risks.map((r, i) => (
                        <li key={i} className="flex gap-2 text-text-secondary text-sm">
                          <span className="text-accent-red shrink-0">-</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {result.ai_synthesis.catalysts && result.ai_synthesis.catalysts.length > 0 && (
                  <div className="bg-bg-card border border-border rounded-xl p-5">
                    <h3 className="text-accent-green font-medium mb-3">{t('dashboard.catalysts')}</h3>
                    <ul className="space-y-2">
                      {result.ai_synthesis.catalysts.map((c, i) => (
                        <li key={i} className="flex gap-2 text-text-secondary text-sm">
                          <span className="text-accent-green shrink-0">+</span>
                          <span>{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Position Advice */}
              {result.ai_synthesis.position_advice && (
                <div className="bg-bg-card border border-accent-cyan/20 rounded-xl p-5">
                  <h3 className="text-accent-cyan font-medium mb-2">{t('dashboard.position_advice')}</h3>
                  <p className="text-text-secondary text-sm leading-relaxed">
                    {result.ai_synthesis.position_advice}
                  </p>
                  {result.ai_synthesis.time_horizon && (
                    <span className="inline-block mt-2 text-xs px-2 py-1 bg-accent-cyan/10 text-accent-cyan rounded">
                      {result.ai_synthesis.time_horizon.replace('_', ' ')}
                    </span>
                  )}
                </div>
              )}

              {/* Dashboard — Action Checklist + News Digest */}
              {result.ai_synthesis.dashboard && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {result.ai_synthesis.dashboard.action_checklist && result.ai_synthesis.dashboard.action_checklist.length > 0 && (
                    <div className="bg-bg-card border border-border rounded-xl p-5">
                      <h3 className="text-text-primary font-medium mb-3">{t('dashboard.action_checklist')}</h3>
                      <ul className="space-y-2">
                        {result.ai_synthesis.dashboard.action_checklist.map((item, i) => (
                          <li key={i} className="flex gap-2 text-text-secondary text-sm">
                            <span className="text-accent-cyan shrink-0">{i + 1}.</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                      <div className="flex flex-wrap gap-2 mt-4">
                        {result.ai_synthesis.dashboard.bias_check && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            result.ai_synthesis.dashboard.bias_check === 'safe' ? 'bg-accent-green/10 text-accent-green' :
                            result.ai_synthesis.dashboard.bias_check === 'caution' ? 'bg-accent-yellow/10 text-accent-yellow' :
                            'bg-accent-red/10 text-accent-red'
                          }`}>
                            {t('dashboard.bias_check')}: {result.ai_synthesis.dashboard.bias_check}
                          </span>
                        )}
                        {result.ai_synthesis.dashboard.volume_signal && (
                          <span className="text-xs px-2 py-1 rounded bg-accent-cyan/10 text-accent-cyan">
                            {t('dashboard.volume_signal')}: {result.ai_synthesis.dashboard.volume_signal}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  <div className="bg-bg-card border border-border rounded-xl p-5 space-y-3">
                    {result.ai_synthesis.dashboard.news_digest && (
                      <div>
                        <h3 className="text-text-primary font-medium mb-2">{t('dashboard.news_digest')}</h3>
                        <p className="text-text-secondary text-sm leading-relaxed">
                          {result.ai_synthesis.dashboard.news_digest}
                        </p>
                      </div>
                    )}
                    {result.ai_synthesis.dashboard.ma_alignment && (
                      <div>
                        <h4 className="text-text-muted text-xs uppercase tracking-wider mb-1">{t('dashboard.ma_alignment')}</h4>
                        <p className="text-text-secondary text-sm">{result.ai_synthesis.dashboard.ma_alignment}</p>
                      </div>
                    )}
                    {result.ai_synthesis.dashboard.chip_health && (
                      <div>
                        <h4 className="text-text-muted text-xs uppercase tracking-wider mb-1">{t('dashboard.chip_health')}</h4>
                        <p className="text-text-secondary text-sm">{result.ai_synthesis.dashboard.chip_health}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* AI Interpretation Details */}
              <div className="bg-bg-card border border-border rounded-xl p-5 space-y-4">
                <h3 className="text-text-primary font-medium">{t('dashboard.ai_interpretation')}</h3>
                {result.ai_synthesis.fundamental_interpretation && (
                  <div>
                    <h4 className="text-accent-blue text-xs uppercase tracking-wider mb-1">{t('tab.fundamental')}</h4>
                    <p className="text-text-secondary text-sm leading-relaxed">{result.ai_synthesis.fundamental_interpretation}</p>
                  </div>
                )}
                {result.ai_synthesis.technical_interpretation && (
                  <div>
                    <h4 className="text-accent-green text-xs uppercase tracking-wider mb-1">{t('tab.technical')}</h4>
                    <p className="text-text-secondary text-sm leading-relaxed">{result.ai_synthesis.technical_interpretation}</p>
                  </div>
                )}
                {result.ai_synthesis.sentiment_interpretation && (
                  <div>
                    <h4 className="text-accent-yellow text-xs uppercase tracking-wider mb-1">{t('tab.sentiment')}</h4>
                    <p className="text-text-secondary text-sm leading-relaxed">{result.ai_synthesis.sentiment_interpretation}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
