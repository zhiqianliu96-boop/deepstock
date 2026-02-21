import { useAnalysisStore } from '../stores/analysisStore';
import StockSearchBar from '../components/common/StockSearchBar';
import ScoreGauge from '../components/common/ScoreGauge';
import VerdictBanner from '../components/common/VerdictBanner';
import RadarChart from '../components/charts/RadarChart';
import FundamentalPanel from '../components/fundamental/FundamentalPanel';
import TechnicalPanel from '../components/technical/TechnicalPanel';
import SentimentPanel from '../components/sentiment/SentimentPanel';

const tabs = [
  { key: 'fundamental' as const, label: 'Fundamental' },
  { key: 'technical' as const, label: 'Technical' },
  { key: 'sentiment' as const, label: 'Sentiment' },
];

export default function DashboardPage() {
  const { result, loading, error, activeTab, setActiveTab } = useAnalysisStore();

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-text-primary tracking-tight">
          Deep<span className="text-accent-cyan">Stock</span>
        </h1>
        <p className="text-text-muted text-sm">Data First, AI Second — Quantitative Stock Analysis</p>
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
          <p className="text-text-secondary text-sm">Running deep analysis...</p>
          <p className="text-text-muted text-xs mt-1">Computing fundamentals, technicals, and sentiment in parallel</p>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          {/* Stock Header */}
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold text-text-primary">
                {result.name || result.code}
              </h2>
              <span className="text-text-muted text-sm">
                {result.code} · {result.market}
                {result.sector && ` · ${result.sector}`}
              </span>
            </div>
          </div>

          {/* Verdict Banner */}
          <VerdictBanner
            verdict={result.verdict}
            composite={result.composite_score}
            confidence={result.ai_synthesis?.confidence}
            summary={result.ai_synthesis?.summary}
          />

          {/* Score Gauges + Radar */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-bg-card border border-border rounded-xl p-6">
              <h3 className="text-text-primary font-medium mb-6 text-center">Pillar Scores</h3>
              <div className="flex justify-center gap-8">
                <ScoreGauge score={result.fundamental_score} label="Fundamental" />
                <ScoreGauge score={result.technical_score} label="Technical" />
                <ScoreGauge score={result.sentiment_score} label="Sentiment" />
              </div>
            </div>
            <div className="bg-bg-card border border-border rounded-xl p-6">
              <h3 className="text-text-primary font-medium mb-4 text-center">Multi-Dimension Radar</h3>
              <RadarChart
                fundamental={result.fundamental_score}
                technical={result.technical_score}
                sentiment={result.sentiment_score}
                fundamentalDetail={result.fundamental_detail}
                technicalDetail={result.technical_detail}
                sentimentDetail={result.sentiment_detail}
              />
            </div>
          </div>

          {/* AI Insights */}
          {result.ai_synthesis && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {result.ai_synthesis.risks && result.ai_synthesis.risks.length > 0 && (
                <div className="bg-bg-card border border-border rounded-xl p-5">
                  <h3 className="text-accent-red font-medium mb-3">Key Risks</h3>
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
                  <h3 className="text-accent-green font-medium mb-3">Catalysts</h3>
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
          )}

          {/* Position Advice */}
          {result.ai_synthesis?.position_advice && (
            <div className="bg-bg-card border border-accent-cyan/20 rounded-xl p-5">
              <h3 className="text-accent-cyan font-medium mb-2">Position Advice</h3>
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

          {/* Tabbed Panels */}
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

          {/* AI Interpretation Details */}
          {result.ai_synthesis && (
            <div className="bg-bg-card border border-border rounded-xl p-5 space-y-4">
              <h3 className="text-text-primary font-medium">AI Interpretation</h3>
              {result.ai_synthesis.fundamental_interpretation && (
                <div>
                  <h4 className="text-accent-blue text-xs uppercase tracking-wider mb-1">Fundamental</h4>
                  <p className="text-text-secondary text-sm leading-relaxed">{result.ai_synthesis.fundamental_interpretation}</p>
                </div>
              )}
              {result.ai_synthesis.technical_interpretation && (
                <div>
                  <h4 className="text-accent-green text-xs uppercase tracking-wider mb-1">Technical</h4>
                  <p className="text-text-secondary text-sm leading-relaxed">{result.ai_synthesis.technical_interpretation}</p>
                </div>
              )}
              {result.ai_synthesis.sentiment_interpretation && (
                <div>
                  <h4 className="text-accent-yellow text-xs uppercase tracking-wider mb-1">Sentiment</h4>
                  <p className="text-text-secondary text-sm leading-relaxed">{result.ai_synthesis.sentiment_interpretation}</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
