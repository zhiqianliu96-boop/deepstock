import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalysisStore } from '../stores/analysisStore';
import { useLocale } from '../i18n/LocaleContext';

const verdictColors: Record<string, string> = {
  strong_buy: 'text-accent-green',
  buy: 'text-accent-cyan',
  hold: 'text-accent-yellow',
  sell: 'text-orange-400',
  strong_sell: 'text-accent-red',
};

export default function HistoryPage() {
  const { history, historyLoading, fetchHistory, loadHistoryDetail } = useAnalysisStore();
  const navigate = useNavigate();
  const { t } = useLocale();

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleClick = async (id: number) => {
    await loadHistoryDetail(id);
    navigate('/');
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-text-primary mb-6">{t('history.title')}</h1>

      {historyLoading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-accent-cyan/20 border-t-accent-cyan rounded-full animate-spin mx-auto" />
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-12 text-text-muted">
          {t('history.empty')}
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((record) => (
            <button
              key={record.id}
              onClick={() => handleClick(record.id)}
              className="w-full bg-bg-card border border-border rounded-xl p-4 hover:border-accent-cyan/30
                         transition-all text-left flex items-center gap-4"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-text-primary font-medium">{record.name || record.code}</span>
                  <span className="text-text-muted text-xs">{record.code}</span>
                  <span className="text-text-muted text-xs px-1.5 py-0.5 bg-bg-primary rounded">{record.market}</span>
                </div>
                <div className="text-text-muted text-xs mt-1">
                  {new Date(record.analysis_date).toLocaleString()}
                  {record.ai_provider && ` · ${record.ai_provider}`}
                </div>
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <div className="text-center">
                  <div className="text-text-muted text-xs">F</div>
                  <div className="text-text-primary text-sm font-medium">{record.fundamental_score?.toFixed(0)}</div>
                </div>
                <div className="text-center">
                  <div className="text-text-muted text-xs">T</div>
                  <div className="text-text-primary text-sm font-medium">{record.technical_score?.toFixed(0)}</div>
                </div>
                <div className="text-center">
                  <div className="text-text-muted text-xs">S</div>
                  <div className="text-text-primary text-sm font-medium">{record.sentiment_score?.toFixed(0)}</div>
                </div>
                <div className="text-center border-l border-border pl-4">
                  <div className="text-text-muted text-xs">{t('history.score')}</div>
                  <div className="text-accent-cyan text-sm font-bold">{record.composite_score?.toFixed(0)}</div>
                </div>
                <span className={`text-sm font-medium uppercase ${verdictColors[record.verdict] || 'text-text-secondary'}`}>
                  {record.verdict?.replace('_', ' ')}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
