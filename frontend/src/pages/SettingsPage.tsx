import { useAnalysisStore } from '../stores/analysisStore';

const providers = [
  { key: 'gemini', label: 'Gemini', desc: 'Google Gemini 2.0 Flash' },
  { key: 'anthropic', label: 'Claude', desc: 'Anthropic Claude Sonnet' },
  { key: 'openai', label: 'OpenAI', desc: 'GPT-4o Mini' },
];

export default function SettingsPage() {
  const { aiProvider, setAiProvider } = useAnalysisStore();

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-text-primary mb-6">Settings</h1>

      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h2 className="text-text-primary font-medium mb-4">AI Provider</h2>
        <p className="text-text-muted text-sm mb-4">
          Select which AI model to use for synthesis. Configure API keys in the backend .env file.
        </p>
        <div className="space-y-2">
          {providers.map((p) => (
            <button
              key={p.key}
              onClick={() => setAiProvider(p.key)}
              className={`w-full flex items-center gap-4 p-4 rounded-lg border transition-all text-left ${
                aiProvider === p.key
                  ? 'border-accent-cyan bg-accent-cyan/5'
                  : 'border-border hover:border-border-light'
              }`}
            >
              <div className={`w-3 h-3 rounded-full border-2 ${
                aiProvider === p.key ? 'border-accent-cyan bg-accent-cyan' : 'border-border-light'
              }`} />
              <div>
                <div className="text-text-primary text-sm font-medium">{p.label}</div>
                <div className="text-text-muted text-xs">{p.desc}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-bg-card border border-border rounded-xl p-5 mt-6">
        <h2 className="text-text-primary font-medium mb-3">API Keys</h2>
        <p className="text-text-muted text-sm leading-relaxed">
          API keys are configured server-side in the <code className="text-accent-cyan bg-bg-primary px-1.5 py-0.5 rounded text-xs">.env</code> file.
          Copy <code className="text-accent-cyan bg-bg-primary px-1.5 py-0.5 rounded text-xs">.env.example</code> to <code className="text-accent-cyan bg-bg-primary px-1.5 py-0.5 rounded text-xs">.env</code> and
          fill in your keys:
        </p>
        <div className="bg-bg-primary rounded-lg p-4 mt-3 text-xs text-text-secondary font-mono">
          <div>GEMINI_API_KEY=your_key_here</div>
          <div>ANTHROPIC_API_KEY=your_key_here</div>
          <div>OPENAI_API_KEY=your_key_here</div>
          <div>TAVILY_API_KEY=your_key_here</div>
        </div>
      </div>
    </div>
  );
}
