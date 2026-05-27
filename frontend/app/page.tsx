'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import SearchBar from '@/components/SearchBar';
import ResultCard from '@/components/ResultCard';
import {
  buscar,
  verificarSaludBackend,
  SearchMode,
  SearchResponse,
  SearchResult,
} from './services/apiService';

const MODOS: Array<{ id: SearchMode; texto: string }> = [
  { id: 'todo', texto: 'Todo' },
  { id: 'texto', texto: 'Texto' },
  { id: 'clase', texto: 'Clase' },
  { id: 'dbpedia', texto: 'DBpedia' },
];

function nombreModo(modo: SearchMode): string {
  return MODOS.find((item) => item.id === modo)?.texto ?? 'Todo';
}

function mensajeSinResultados(modo: SearchMode): string {
  if (modo === 'clase') {
    return 'No se encontraron individuos para esa clase.';
  }

  if (modo === 'dbpedia') {
    return 'DBpedia no devolvió resultados para esta búsqueda.';
  }

  return 'No se encontraron resultados.';
}

export default function HomePage() {
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
          }
        );

        if (!controller.signal.aborted) {
          aplicarRespuesta(response);
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          return;
        }

        setError(
          `No se pudo consultar ${nombreModo(fuente)}. El backend puede seguir activo.`
        );
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
          setIsSearching(false);
        }
      }
    },
    [aplicarRespuesta]
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 dark:text-gray-100 mb-2">
            🎵 Buscador Semántico
          </h1>

          <p className="text-gray-500 dark:text-gray-400">
            Ontología de Instrumentos Musicales
          </p>

          {backendActivo === true && (
            <span className="inline-block mt-2 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
              Backend conectado
            </span>
          )}

          {backendActivo === false && (
            <span className="inline-block mt-2 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs rounded-full">
              Backend no conectado
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
            placeholder="Buscar instrumento, clase o recurso en DBpedia..."
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
            <span>Buscando en {nombreModo(modoResultado)}...</span>
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
            <p className="text-gray-500">
              Busca instrumentos, conceptos o recursos enlazados
            </p>
          </div>
        )}

        {tieneBusqueda && !error && (
          <>
            <div className="flex justify-between items-center mb-3">
              <p className="text-sm text-gray-500">
                {total} resultado{total !== 1 ? 's' : ''} para &quot;
                {ultimaBusqueda}&quot; en {nombreModo(modoResultado)}
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