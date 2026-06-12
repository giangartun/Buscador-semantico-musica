'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import esMessages from '../../messages/es.json';
import enMessages from '../../messages/en.json';
import frMessages from '../../messages/fr.json';

const LOCALES = ['es', 'en', 'fr'] as const;
export type Locale = (typeof LOCALES)[number];

const STORAGE_KEY = 'music-search-locale';

type Messages = typeof esMessages;

const MESSAGES: Record<Locale, Messages> = {
  es: esMessages,
  en: enMessages,
  fr: frMessages,
};

interface LanguageContextValue {
  locale: Locale;
  setLocale: (nextLocale: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(
  undefined
);

function getNestedValue(source: Messages, path: string): string | undefined {
  const parts = path.split('.');
  let current: unknown = source;

  for (const part of parts) {
    if (!current || typeof current !== 'object') {
      return undefined;
    }
    current = (current as Record<string, unknown>)[part];
  }

  return typeof current === 'string' ? current : undefined;
}

function interpolate(
  template: string,
  vars?: Record<string, string | number>
): string {
  if (!vars) {
    return template;
  }

  return template.replace(/\{(\w+)\}/g, (match, key) => {
    const value = vars[key];
    return value === undefined ? match : String(value);
  });
}

// Lee el locale guardado solo en el cliente; en SSR devuelve 'es'.
function getStoredLocale(): Locale | null {
  if (typeof window === 'undefined') return null;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored && LOCALES.includes(stored as Locale)) {
    return stored as Locale;
  }
  return null;
}

export default function LanguageProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // useState con función de inicialización: se ejecuta solo en el cliente,
  // así el estado arranca con el valor correcto sin necesitar un efecto.
  const [locale, setLocaleState] = useState<Locale>('es');

  const setLocale = useCallback((nextLocale: Locale) => {
    setLocaleState(nextLocale);
    window.localStorage.setItem(STORAGE_KEY, nextLocale);
    document.documentElement.lang = nextLocale;
  }, []);

  // Sincroniza el atributo lang del <html> al montar, sin setState.
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    const storedLocale = getStoredLocale();

    if (storedLocale) {
      window.requestAnimationFrame(() => {
        setLocaleState(storedLocale);
        document.documentElement.lang = storedLocale;
      });
    }
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const messages = MESSAGES[locale] ?? MESSAGES.es;
      const fallback = MESSAGES.es;
      const template =
        getNestedValue(messages, key) ??
        getNestedValue(fallback, key) ??
        key;
      return interpolate(template, vars);
    },
    [locale]
  );

  const value = useMemo(
    () => ({ locale, setLocale, t }),
    [locale, setLocale, t]
  );

  return (
    <LanguageContext.Provider value={value}>
      <div suppressHydrationWarning>{children}</div>
    </LanguageContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useI18n must be used within LanguageProvider');
  }
  return context;
}
