'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import SearchBar from '@/components/SearchBar';
import ResultCard from '@/components/ResultCard';
import { useI18n } from './language/LanguageProvider';
import {
  buscar,
  verificarSaludBackend,
  SearchMode,
  SearchResponse,
  SearchResult,
} from './services/apiService';

const LOCALES = ['es', 'en', 'fr'] as const;

export default function HomePage() {
  const { locale, setLocale, t } = useI18n();

  const MODOS: Array<{ id: SearchMode; texto: string }> = useMemo(
    () => [
      { id: 'todo', texto: t('modes.all') },
      { id: 'texto', texto: t('modes.text') },
      { id: 'clase', texto: t('modes.class') },
      { id: 'dbpedia', texto: t('modes.dbpedia') },
    ],
    [t]
  );

  const nombreModo = useCallback(
    (modo: SearchMode): string =>
      MODOS.find((item) => item.id === modo)?.texto ?? t('modes.all'),
    [MODOS, t]
  );

  function mensajeSinResultados(modo: SearchMode): string {
    if (modo === 'clase') {
      return t('app.noResults.class');
    }

    if (modo === 'dbpedia') {
      return t('app.noResults.dbpedia');
    }

    return t('app.noResults.default');
  }

  const [texto, setTexto] = useState('');
  const [ultimaBusqueda, setUltimaBusqueda] = useState('');
  const [modo, setModo] = useState<SearchMode>('todo');
  const [modoResultado, setModoResultado] = useState<SearchMode>('todo');
  const [resultados, setResultados] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [backendActivo, setBackendActivo] = useState<boolean | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    verificarSaludBackend(controller.signal).then((activo) => {
      if (!controller.signal.aborted) {
        setBackendActivo(activo);
      }
    });

    return () => {
      controller.abort();
      abortControllerRef.current?.abort();
    };
  }, []);

  const aplicarRespuesta = useCallback((response: SearchResponse) => {
    setResultados(response.resultados);
    setTotal(response.total);
    setAviso(response.aviso ?? null);
  }, []);

  const ejecutarBusqueda = useCallback(
    async (consulta: string, fuente: SearchMode) => {
      const termino = consulta.trim();

      if (!termino) {
        return;
      }

      abortControllerRef.current?.abort();

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setUltimaBusqueda(termino);
      setModoResultado(fuente);
      setError(null);
      setAviso(null);
      setIsSearching(true);

      try {
        const response = await buscar(
          termino,
          fuente,
          controller.signal,
          (respuestaParcial) => {
            if (!controller.signal.aborted) {
              aplicarRespuesta(respuestaParcial);
            }
          },
          locale
        );

        if (!controller.signal.aborted) {
          aplicarRespuesta(response);
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          return;
        }

        setError(t('errors.backendQuery', { mode: nombreModo(fuente) }));
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
          setIsSearching(false);
        }
      }
    },
    [aplicarRespuesta, locale, nombreModo, t]
  );

  const handleSearch = useCallback(
    (consulta: string) => {
      ejecutarBusqueda(consulta, modo);
    },
    [ejecutarBusqueda, modo]
  );

  const handleClearInput = useCallback(() => {
    setTexto('');
  }, []);

  const handleModeChange = useCallback(
    (nuevoModo: SearchMode) => {
      setModo(nuevoModo);

      const consulta = texto.trim() || ultimaBusqueda;

      if (consulta) {
        ejecutarBusqueda(consulta, nuevoModo);
      }
    },
    [ejecutarBusqueda, texto, ultimaBusqueda]
  );

  const tieneBusqueda = ultimaBusqueda !== '';

  const resumenKey = total === 1 ? 'app.resultsSummary.one' : 'app.resultsSummary.other';

  return (
    <div className="min-h-screen">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 dark:text-gray-100 mb-2">
            🎵 {t('app.title')}
          </h1>

          <p className="text-gray-500 dark:text-gray-400">
            {t('app.subtitle')}
          </p>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-gray-400">
            <span className="uppercase tracking-wide">
              {t('language.label')}
            </span>
            {LOCALES.map((code) => (
              <button
                key={code}
                type="button"
                onClick={() => setLocale(code)}
                className={`px-2 py-1 rounded-full border transition-colors ${
                  locale === code
                    ? 'bg-slate-900 text-white border-slate-900 dark:bg-slate-100 dark:text-slate-900 dark:border-slate-100'
                    : 'border-slate-200 text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:border-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                }`}
              >
                {t(`language.${code}`)}
              </button>
            ))}
          </div>

          {backendActivo === true && (
            <span className="inline-block mt-3 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
              {t('app.backendOk')}
            </span>
          )}

          {backendActivo === false && (
            <span className="inline-block mt-3 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs rounded-full">
              {t('app.backendFail')}
            </span>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <SearchBar
            value={texto}
            onValueChange={setTexto}
            onSearch={handleSearch}
            onClearInput={handleClearInput}
            isLoading={isSearching}
            placeholder={t('search.placeholder')}
            submitLabel={t('search.button')}
            clearLabel={t('search.clear')}
            loadingLabel={t('search.loading')}
          />

          <div className="flex items-center gap-2 mt-3">
            {MODOS.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => handleModeChange(item.id)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                  modo === item.id
                    ? 'bg-violet-100 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300'
                    : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300'
                }`}
              >
                {item.texto}
              </button>
            ))}
          </div>
        </div>

        {isSearching && (
          <div className="flex items-center gap-2 mb-4 text-sm text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" />
            <span>{t('app.searching', { mode: nombreModo(modoResultado) })}</span>
          </div>
        )}

        {aviso && (
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 mb-4">
            <p className="text-amber-700 dark:text-amber-400 text-sm">
              {aviso}
            </p>
          </div>
        )}

        {error && !isSearching && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
            <p className="text-red-600 dark:text-red-400 text-sm text-center">
              {error}
            </p>
          </div>
        )}

        {!tieneBusqueda && !isSearching && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">🎶</div>
            <p className="text-gray-500">{t('app.emptyState')}</p>
          </div>
        )}

        {tieneBusqueda && !error && (
          <>
            <div className="flex justify-between items-center mb-3">
              <p className="text-sm text-gray-500">
                {t(resumenKey, {
                  total,
                  query: ultimaBusqueda,
                  mode: nombreModo(modoResultado),
                })}
              </p>
            </div>

            {resultados.length > 0 ? (
              <div className="space-y-3">
                {resultados.map((resultado) => (
                  <ResultCard
                    key={resultado.id}
                    title={resultado.nombre}
                    classes={resultado.clases}
                    description={resultado.descripcion}
                    source={resultado.origen}
                    uri={resultado.uri}
                    abstract={resultado.abstract}
                    birthDate={resultado.birthDate}
                    deathDate={resultado.deathDate}
                    genres={resultado.genres}
                    instruments={resultado.instruments}
                    birthPlaces={resultado.birthPlaces}
                    nationalities={resultado.nationalities}
                    notableWorks={resultado.notableWorks}
                    thumbnail={resultado.thumbnail}
                    wikipediaPage={resultado.wikipediaPage}
                  />
                ))}
              </div>
            ) : (
              !isSearching && (
                <div className="text-center py-16">
                  <div className="text-5xl mb-4">🔍</div>
                  <p className="text-gray-500">
                    {mensajeSinResultados(modoResultado)}
                  </p>
                </div>
              )
            )}
          </>
        )}
      </div>
    </div>
  );
}