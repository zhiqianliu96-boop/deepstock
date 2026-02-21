import { useState } from 'react';
import { useAnalysisStore } from '../../stores/analysisStore';

export default function StockSearchBar() {
  const [code, setCode] = useState('');
  const { analyze, loading } = useAnalysisStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = code.trim().toUpperCase();
    if (trimmed) {
      analyze(trimmed);
    }
  };

  const presets = [
    { label: '茅台', code: '600519' },
    { label: 'AAPL', code: 'AAPL' },
    { label: '腾讯', code: '00700' },
    { label: 'NVDA', code: 'NVDA' },
    { label: '宁德', code: '300750' },
  ];

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="flex gap-3">
        <div className="relative flex-1">
          <input
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter stock code (600519, AAPL, 00700...)"
            disabled={loading}
            className="w-full px-4 py-3 bg-bg-card border border-border rounded-lg text-text-primary
                       placeholder:text-text-muted focus:outline-none focus:border-accent-cyan
                       focus:ring-1 focus:ring-accent-cyan/30 transition-all text-sm"
          />
          {loading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="w-5 h-5 border-2 border-accent-cyan/30 border-t-accent-cyan rounded-full animate-spin" />
            </div>
          )}
        </div>
        <button
          type="submit"
          disabled={loading || !code.trim()}
          className="px-6 py-3 bg-accent-cyan/20 border border-accent-cyan/50 text-accent-cyan
                     rounded-lg hover:bg-accent-cyan/30 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-all text-sm font-medium"
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
      <div className="flex gap-2 mt-3 flex-wrap">
        {presets.map((p) => (
          <button
            key={p.code}
            type="button"
            onClick={() => { setCode(p.code); analyze(p.code); }}
            disabled={loading}
            className="px-3 py-1 text-xs bg-bg-card border border-border rounded-md
                       text-text-secondary hover:border-accent-cyan/50 hover:text-accent-cyan
                       disabled:opacity-40 transition-all"
          >
            {p.label} ({p.code})
          </button>
        ))}
      </div>
    </form>
  );
}
