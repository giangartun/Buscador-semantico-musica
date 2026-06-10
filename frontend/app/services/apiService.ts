const API_BASE_URL = 'http://127.0.0.1:5000';
const DBPEDIA_TIMEOUT_MS = 8000;

const WARNING_MESSAGES: Record<string, { timeout: string; partial: string }> = {
  es: {
    timeout: 'DBpedia no respondio dentro del tiempo esperado.',
    partial: 'DBpedia no respondio. Se muestran los resultados locales encontrados.',
  },
  en: {
    timeout: 'DBpedia did not respond within the expected time.',
    partial: 'DBpedia did not respond. Showing local results found.',
  },
  fr: {
    timeout: "DBpedia n'a pas repondu dans le temps imparti.",
    partial: "DBpedia n'a pas repondu. Affichage des resultats locaux.",
  },
};

export type SearchMode = 'todo' | 'texto' | 'clase' | 'dbpedia';

export interface SearchResult {
  id: string;
  nombre: string;
  clases: string[];
  descripcion?: string;
  uri?: string;
  origen: string;
  abstract?: string;
  birthDate?: string;
  deathDate?: string;
  genres?: string[];
  instruments?: string[];
  birthPlaces?: string[]
  nationalities?: string[];
  notableWorks?: string[];
  thumbnail?: string;
  wikipediaPage?: string;
  // Relaciones de la ontología local
  obrasCompuestas?: string[];
  instrumentosObra?: string[];
  compositorTexto?: string;
}

export interface SearchResponse {
  total: number;
  resultados: SearchResult[];
  aviso?: string;
}

interface BackendSearchResult {
  id?: string;
  nombre: string;
  clases: string[];
  descripcion?: string;
  uri?: string;
  obrasCompuestas?: string[];
  instrumentosObra?: string[];
  compositorTexto?: string;
}

interface BackendDbpediaResult {
  nombre: string;
  descripcion: string;
  uri_dbpedia: string;
  abstract?: string;
  birthDate?: string;
  deathDate?: string;
  genres?: string[];
  instruments?: string[];
  birthPlaces?: string[];
  nationalities?: string[];
  notableWorks?: string[];
  thumbnail?: string;
  wikipediaPage?: string;
}

interface BackendResponse<T> {
  total: number;
  resultados: T[];
}

type ResultsUpdate = (response: SearchResponse) => void;

async function obtenerJson<T>(
  ruta: string,
  signal?: AbortSignal
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${ruta}`, { signal });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.error ?? `Error HTTP: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function agregarIdioma(ruta: string, locale?: string): string {
  if (!locale) {
    return ruta;
  }

  const separator = ruta.includes('?') ? '&' : '?';
  return `${ruta}${separator}lang=${encodeURIComponent(locale)}`;
}

function obtenerWarning(
  locale: string | undefined,
  key: 'timeout' | 'partial'
): string {
  const messages = WARNING_MESSAGES[locale ?? ''] ?? WARNING_MESSAGES.es;
  return messages[key];
}

function esCancelacion(error: unknown): boolean {
  return error instanceof Error && error.name === 'AbortError';
}

function fusionarResultados(resultados: SearchResult[]): SearchResult[] {
  const mapa = new Map<string, SearchResult>();

  for (const resultado of resultados) {
    const clave = resultado.nombre.trim().toLowerCase();
    const existente = mapa.get(clave);

    if (!existente) {
      mapa.set(clave, resultado);
      continue;
    }

    mapa.set(clave, {
      ...existente,
      clases: Array.from(
        new Set([...existente.clases, ...resultado.clases])
      ),
      descripcion: existente.descripcion ?? resultado.descripcion,
      uri: existente.uri ?? resultado.uri,
      origen: Array.from(
        new Set([
          ...existente.origen.split(', '),
          ...resultado.origen.split(', '),
        ])
      ).join(', '),
    });
  }

  return Array.from(mapa.values());
}

function crearRespuesta(
  resultados: SearchResult[],
  aviso?: string
): SearchResponse {
  const unicos = fusionarResultados(resultados);

  return {
    total: unicos.length,
    resultados: unicos,
    aviso,
  };
}

async function consultarTexto(
  termino: string,
  signal?: AbortSignal,
  locale?: string
): Promise<SearchResult[]> {
  const response = await obtenerJson<BackendResponse<BackendSearchResult>>(
    agregarIdioma(`/api/buscar?texto=${encodeURIComponent(termino)}`, locale),
    signal
  );

  return response.resultados.map((resultado) => ({
    id: resultado.id ?? `texto-${resultado.nombre}`,
    nombre: resultado.nombre,
    clases: resultado.clases,
    descripcion: resultado.descripcion,
    uri: resultado.uri,
    origen: 'Texto local',
    obrasCompuestas: resultado.obrasCompuestas,
    instrumentosObra: resultado.instrumentosObra,
    compositorTexto: resultado.compositorTexto,
  }));
}

async function consultarClase(
  termino: string,
  signal?: AbortSignal,
  locale?: string
): Promise<SearchResult[]> {
  const response = await obtenerJson<BackendResponse<BackendSearchResult>>(
    agregarIdioma(`/api/buscar?clase=${encodeURIComponent(termino)}`, locale),
    signal
  );

  return response.resultados.map((resultado) => ({
    id: resultado.id ?? `clase-${resultado.nombre}`,
    nombre: resultado.nombre,
    clases: resultado.clases,
    descripcion: resultado.descripcion,
    uri: resultado.uri,
    origen: `Clase: ${termino}`,
    obrasCompuestas: resultado.obrasCompuestas,
    instrumentosObra: resultado.instrumentosObra,
    compositorTexto: resultado.compositorTexto,
  }));
}

async function consultarDbpedia(
  termino: string,
  signal?: AbortSignal,
  locale?: string
): Promise<SearchResult[]> {
  const controller = new AbortController();

  const cancelar = () => controller.abort();

  if (signal?.aborted) {
    throw new DOMException('Busqueda cancelada', 'AbortError');
  }

  signal?.addEventListener('abort', cancelar, { once: true });

  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, DBPEDIA_TIMEOUT_MS);

  try {
    const response = await obtenerJson<BackendResponse<BackendDbpediaResult>>(
      agregarIdioma(`/api/dbpedia?nombre=${encodeURIComponent(termino)}`, locale),
      controller.signal
    );

    return response.resultados.map((resultado) => ({
      id: `dbpedia-${resultado.uri_dbpedia}`,
      nombre: resultado.nombre,
      clases: ['DBpedia'],
      descripcion: resultado.abstract ?? resultado.descripcion,
      uri: resultado.uri_dbpedia,
      origen: 'DBpedia',
      abstract: resultado.abstract,
      birthDate: resultado.birthDate,
      deathDate: resultado.deathDate,
      genres: resultado.genres,
      instruments: resultado.instruments,
      birthPlaces: resultado.birthPlaces,
      nationalities: resultado.nationalities,
      notableWorks: resultado.notableWorks,
      thumbnail: resultado.thumbnail,
      wikipediaPage: resultado.wikipediaPage,
    }));
  } finally {
    window.clearTimeout(timeoutId);
    signal?.removeEventListener('abort', cancelar);
  }
}

export async function buscar(
  texto: string,
  modo: SearchMode,
  signal?: AbortSignal,
  onUpdate?: ResultsUpdate,
  locale?: string
): Promise<SearchResponse> {
  const termino = texto.trim();

  if (!termino) {
    return crearRespuesta([]);
  }

  if (modo === 'texto') {
    const resultados = await consultarTexto(termino, signal, locale);
    return crearRespuesta(resultados);
  }

  if (modo === 'clase') {
    const resultados = await consultarClase(termino, signal, locale);
    return crearRespuesta(resultados);
  }

  if (modo === 'dbpedia') {
    try {
      const resultados = await consultarDbpedia(termino, signal, locale);
      return crearRespuesta(resultados);
    } catch (error) {
      if (esCancelacion(error) && signal?.aborted) {
        throw error;
      }

      return crearRespuesta(
        [],
        obtenerWarning(locale, 'timeout')
      );
    }
  }

  const acumulados: SearchResult[] = [];
  let aviso: string | undefined;

  try {
    const resultadosTexto = await consultarTexto(termino, signal, locale);
    acumulados.push(...resultadosTexto);
    onUpdate?.(crearRespuesta(acumulados));
  } catch (error) {
    if (esCancelacion(error)) {
      throw error;
    }
  }

  try {
    const resultadosClase = await consultarClase(termino, signal, locale);
    acumulados.push(...resultadosClase);

    // Aqui ya se muestran los 29 individuos de Instrumento,
    // sin esperar a DBpedia.
    onUpdate?.(crearRespuesta(acumulados));
  } catch (error) {
    if (esCancelacion(error)) {
      throw error;
    }
  }

  try {
    const resultadosDbpedia = await consultarDbpedia(termino, signal, locale);
    acumulados.push(...resultadosDbpedia);
    onUpdate?.(crearRespuesta(acumulados));
  } catch (error) {
    if (signal?.aborted) {
      throw new DOMException('Busqueda cancelada', 'AbortError');
    }

    aviso = obtenerWarning(locale, 'partial');
  }

  return crearRespuesta(acumulados, aviso);
}

export async function verificarSaludBackend(
  signal?: AbortSignal
): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, { signal });
    return response.ok;
  } catch {
    return false;
  }
}