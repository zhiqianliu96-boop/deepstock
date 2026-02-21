import type { SentimentDetail, ScoredArticle } from '../../types/analysis';

interface Props {
  detail: SentimentDetail;
}

function SubScoreBar({ label, score, max }: { label: string; score: number; max: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color = pct >= 75 ? '#10b981' : pct >= 50 ? '#06b6d4' : pct >= 30 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-3">
      <span className="text-text-secondary text-xs w-28 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-bg-primary rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-text-primary text-xs w-12 text-right">{score.toFixed(1)}/{max}</span>
    </div>
  );
}

function ArticleCard({ article }: { article: ScoredArticle }) {
  const scoreColor = article.score > 0.1 ? 'text-accent-green' :
    article.score < -0.1 ? 'text-accent-red' : 'text-text-secondary';
  const scoreBg = article.score > 0.1 ? 'bg-accent-green/10' :
    article.score < -0.1 ? 'bg-accent-red/10' : 'bg-bg-primary';

  return (
    <div className="bg-bg-primary border border-border/50 rounded-lg p-4 hover:border-border-light transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-text-primary text-sm hover:text-accent-cyan transition-colors line-clamp-2"
          >
            {article.title}
          </a>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-text-muted text-xs px-2 py-0.5 bg-bg-card rounded capitalize">
              {article.category}
            </span>
            {article.published_date && (
              <span className="text-text-muted text-xs">
                {new Date(article.published_date).toLocaleDateString()}
              </span>
            )}
            <span className="text-text-muted text-xs">
              Quality: {(article.source_quality * 100).toFixed(0)}%
            </span>
          </div>
        </div>
        <div className={`${scoreBg} ${scoreColor} px-2 py-1 rounded text-sm font-medium shrink-0`}>
          {article.score > 0 ? '+' : ''}{article.score.toFixed(2)}
        </div>
      </div>
    </div>
  );
}

function CategoryPill({ name, data }: { name: string; data: { count: number; avg_score: number } }) {
  const color = data.avg_score > 0.1 ? 'border-accent-green/50 text-accent-green' :
    data.avg_score < -0.1 ? 'border-accent-red/50 text-accent-red' : 'border-border text-text-secondary';
  return (
    <div className={`border rounded-lg p-3 ${color}`}>
      <div className="text-xs capitalize font-medium">{name}</div>
      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-lg font-bold">{data.count}</span>
        <span className="text-xs opacity-70">
          avg: {data.avg_score > 0 ? '+' : ''}{data.avg_score.toFixed(2)}
        </span>
      </div>
    </div>
  );
}

export default function SentimentPanel({ detail }: Props) {
  const articles = detail.articles || [];
  const categories = detail.category_summary || {};

  return (
    <div className="space-y-6">
      {/* Sub-scores */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">Sentiment Sub-scores</h3>
        <div className="space-y-3">
          <SubScoreBar label="News Sentiment" score={detail.news_sentiment_score} max={40} />
          <SubScoreBar label="Event Impact" score={detail.event_impact_score} max={30} />
          <SubScoreBar label="Market Attention" score={detail.market_attention_score} max={15} />
          <SubScoreBar label="Source Quality" score={detail.source_quality_score} max={15} />
        </div>
      </div>

      {/* Sentiment Distribution */}
      {detail.breakdown?.distribution && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-4">Sentiment Distribution</h3>
          <div className="flex gap-4">
            <div className="flex-1 text-center">
              <div className="text-2xl font-bold text-accent-green">
                {detail.breakdown.distribution.positive || 0}
              </div>
              <div className="text-text-muted text-xs mt-1">Positive</div>
            </div>
            <div className="flex-1 text-center">
              <div className="text-2xl font-bold text-text-secondary">
                {detail.breakdown.distribution.neutral || 0}
              </div>
              <div className="text-text-muted text-xs mt-1">Neutral</div>
            </div>
            <div className="flex-1 text-center">
              <div className="text-2xl font-bold text-accent-red">
                {detail.breakdown.distribution.negative || 0}
              </div>
              <div className="text-text-muted text-xs mt-1">Negative</div>
            </div>
          </div>
          {/* Visual bar */}
          <div className="flex h-3 rounded-full overflow-hidden mt-4 bg-bg-primary">
            {(() => {
              const d = detail.breakdown.distribution;
              const total = (d.positive || 0) + (d.neutral || 0) + (d.negative || 0);
              if (total === 0) return null;
              return (
                <>
                  <div className="bg-accent-green" style={{ width: `${(d.positive / total) * 100}%` }} />
                  <div className="bg-gray-500" style={{ width: `${(d.neutral / total) * 100}%` }} />
                  <div className="bg-accent-red" style={{ width: `${(d.negative / total) * 100}%` }} />
                </>
              );
            })()}
          </div>
        </div>
      )}

      {/* Categories */}
      {Object.keys(categories).length > 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-5">
          <h3 className="text-text-primary font-medium mb-4">News Categories</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(categories).map(([name, data]) => (
              <CategoryPill key={name} name={name} data={data} />
            ))}
          </div>
        </div>
      )}

      {/* News Timeline */}
      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h3 className="text-text-primary font-medium mb-4">
          News Articles ({articles.length})
        </h3>
        {articles.length === 0 ? (
          <div className="text-text-muted text-sm text-center py-8">
            No news articles found. Set TAVILY_API_KEY in .env for news analysis.
          </div>
        ) : (
          <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
            {articles.map((article, i) => (
              <ArticleCard key={i} article={article} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
