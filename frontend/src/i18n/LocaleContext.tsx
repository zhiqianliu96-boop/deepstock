import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { locales, type Locale, type TranslationKey } from './locales';

interface LocaleContextValue {
  locale: Locale;
  toggleLocale: () => void;
  t: (key: TranslationKey) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function getInitialLocale(): Locale {
  try {
    const stored = localStorage.getItem('deepstock_locale');
    if (stored === 'en' || stored === 'zh') return stored;
  } catch {}
  return 'en';
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(getInitialLocale);

  const toggleLocale = useCallback(() => {
    setLocale((prev) => {
      const next = prev === 'en' ? 'zh' : 'en';
      try { localStorage.setItem('deepstock_locale', next); } catch {}
      return next;
    });
  }, []);

  const t = useCallback(
    (key: TranslationKey): string => {
      return locales[locale][key] ?? key;
    },
    [locale],
  );

  return (
    <LocaleContext.Provider value={{ locale, toggleLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error('useLocale must be used within LocaleProvider');
  return ctx;
}
