import { useAnalysisStore } from '../stores/analysisStore';
import { useLocale } from '../i18n/LocaleContext';

export default function SettingsPage() {
  const { aiProvider, setAiProvider } = useAnalysisStore();
  const { t } = useLocale();

  const providers = [
    { key: 'gemini', label: 'Gemini', desc: t('settings.gemini') },
    { key: 'anthropic', label: 'Claude', desc: t('settings.claude') },
    { key: 'openai', label: 'OpenAI', desc: t('settings.openai') },
    { key: 'deepseek', label: 'DeepSeek', desc: t('settings.deepseek') },
    { key: 'qwen', label: 'Qwen', desc: t('settings.qwen') },
  ];

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-text-primary mb-6">{t('settings.title')}</h1>

      <div className="bg-bg-card border border-border rounded-xl p-5">
        <h2 className="text-text-primary font-medium mb-4">{t('settings.ai_provider')}</h2>
        <p className="text-text-muted text-sm mb-4">
          {t('settings.ai_desc')}
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
        <h2 className="text-text-primary font-medium mb-3">{t('settings.api_keys')}</h2>
        <p className="text-text-muted text-sm leading-relaxed">
          {t('settings.api_desc')} <code className="text-accent-cyan bg-bg-primary px-1.5 py-0.5 rounded text-xs">.env</code> {t('settings.api_desc2')} <code className="text-accent-cyan bg-bg-primary px-1.5 py-0.5 rounded text-xs">.env.example</code> {t('settings.api_desc3')} <code className="text-accent-cyan bg-bg-primary px-1.5 py-0.5 rounded text-xs">.env</code> {t('settings.api_desc4')}
        </p>
        <div className="bg-bg-primary rounded-lg p-4 mt-3 text-xs text-text-secondary font-mono">
          <div>GEMINI_API_KEY=your_key_here</div>
          <div>ANTHROPIC_API_KEY=your_key_here</div>
          <div>OPENAI_API_KEY=your_key_here</div>
          <div>DEEPSEEK_API_KEY=your_key_here</div>
          <div>QWEN_API_KEY=your_key_here</div>
          <div>TAVILY_API_KEY=your_key_here</div>
          <div>BRAVE_API_KEY=your_key_here</div>
        </div>
      </div>
    </div>
  );
}
