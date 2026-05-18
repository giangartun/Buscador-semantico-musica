'use client';

import SearchBar from '@/components/SearchBar';
import ResultCard from '@/components/ResultCard';
import { useState } from 'react';

interface SearchResult {
  title?: string;
  name?: string;
  artist?: string;
  description?: string;
  similarity?: number;
  clases?: string[];
}

const MOCK_RESULTS: SearchResult[] = [
  {
    title: 'Acordeon_Cromatico',
    description: 'Instrumento de viento con lengüetas vibrantes',
    clases: ['Instrumento', 'Aerófono'],
    similarity: 0.92,
  },
  {
    title: 'Aerofono_Andino',
    description: 'Instrumento de viento tradicional de los Andes',
    clases: ['Instrumento', 'Tradicional'],
    similarity: 0.87,
  },
  {
    title: 'Capacidad_Extrema_Piano',
    description: 'Capacidad extrema de ejecución en piano',
    clases: ['Capacidad', 'Piano'],
    similarity: 0.81,
  },
];

export default function Home() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(
        `http://localhost:5000/api/buscar?texto=${encodeURIComponent(query)}`
      );
      if (response.ok) {
        const data = await response.json();
        setResults(data.resultados || []);
      } else {
        setResults([]);
      }
    } catch {
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const displayResults = results.length > 0 ? results : MOCK_RESULTS;
  const hasRealResults = results.length > 0;

  return (
    <div className="min-h-screen bg-[#0f1117]">
      <div className="flex flex-col items-center justify-center min-h-screen px-4 py-16">
        <main className="w-full max-w-xl">

          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-100 mb-2">
              Buscador semántico de música
            </h1>
            <p className="text-sm text-slate-500">
              Encuentra instrumentos y conceptos utilizando búsqueda semántica
            </p>
          </div>

          {/* Search Bar */}
          <div className="mb-8 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3">
            <SearchBar
              onSearch={handleSearch}
              placeholder="Busca por instrumento, género, concepto..."
            />
          </div>

          {/* Results */}
          {isSearching ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-violet-500" />
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                  {hasRealResults ? `Resultados (${results.length})` : 'Ejemplos'}
                </p>
                {hasRealResults && (
                  <p className="text-xs text-violet-400">ordenados por relevancia</p>
                )}
              </div>

              <div className="flex flex-col gap-2.5">
                {displayResults.map((result, index) => (
                  <ResultCard
                    key={hasRealResults ? index : `mock-${index}`}
                    title={result.title || result.name || ''}
                    name={result.name}
                    description={result.description}
                    classes={result.clases}
                    similarity={result.similarity}
                    //rank={index}
                  />
                ))}
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}