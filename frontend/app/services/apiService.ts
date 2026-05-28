const API_BASE_URL = 'http://127.0.0.1:5000';
const DBPEDIA_TIMEOUT_MS = 8000;

export type SearchMode = 'todo' | 'texto' | 'clase' | 'dbpedia';

export interface SearchResult {
  id: string;
  nombre: string;
  clases: string[];
  descripcion?: string;
  uri?: string;
  origen: string;
}

export interface SearchResponse {
  total: number;
  resultados: SearchResult[];
  aviso?: string;
}

interface BackendSearchResult {
  nombre: string;
  clases: string[];
}

interface BackendDbpediaResult {
  nombre: string;
  descripcion: string;
  uri_dbpedia: string;
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
  signal?: AbortSignal
): Promise<SearchResult[]> {
  const response = await obtenerJson<BackendResponse<BackendSearchResult>>(
    `/api/buscar?texto=${encodeURIComponent(termino)}`,
    signal
  );

  return response.resultados.map((resultado) => ({
    id: `texto-${resultado.nombre}`,
    nombre: resultado.nombre,
    clases: resultado.clases,
    origen: 'Texto local',
  }));
}

async function consultarClase(
  termino: string,
  signal?: AbortSignal
): Promise<SearchResult[]> {
  const response = await obtenerJson<BackendResponse<BackendSearchResult>>(
    `/api/buscar?clase=${encodeURIComponent(termino)}`,
    signal
  );

  return response.resultados.map((resultado) => ({
    id: `clase-${resultado.nombre}`,
    nombre: resultado.nombre,
    clases: resultado.clases,
    origen: `Clase: ${termino}`,
  }));
}

async function consultarDbpedia(
  termino: string,
  signal?: AbortSignal
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
      `/api/dbpedia?nombre=${encodeURIComponent(termino)}`,
      controller.signal
    );

    return response.resultados.map((resultado) => ({
      id: `dbpedia-${resultado.uri_dbpedia}`,
      nombre: resultado.nombre,
      clases: ['DBpedia'],
      descripcion: resultado.descripcion,
      uri: resultado.uri_dbpedia,
      origen: 'DBpedia',
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
  onUpdate?: ResultsUpdate
): Promise<SearchResponse> {
  const termino = texto.trim();

  if (!termino) {
    return crearRespuesta([]);
  }

  if (modo === 'texto') {
    const resultados = await consultarTexto(termino, signal);
    return crearRespuesta(resultados);
  }

  if (modo === 'clase') {
    const resultados = await consultarClase(termino, signal);
    return crearRespuesta(resultados);
  }

  if (modo === 'dbpedia') {
    try {
      const resultados = await consultarDbpedia(termino, signal);
      return crearRespuesta(resultados);
    } catch (error) {
      if (esCancelacion(error) && signal?.aborted) {
        throw error;
      }

      return crearRespuesta(
        [],
        'DBpedia no respondió dentro del tiempo esperado.'
      );
    }
  }

  const acumulados: SearchResult[] = [];
  let aviso: string | undefined;

  try {
    const resultadosTexto = await consultarTexto(termino, signal);
    acumulados.push(...resultadosTexto);
    onUpdate?.(crearRespuesta(acumulados));
  } catch (error) {
    if (esCancelacion(error)) {
      throw error;
    }
  }

  try {
    const resultadosClase = await consultarClase(termino, signal);
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
    const resultadosDbpedia = await consultarDbpedia(termino, signal);
    acumulados.push(...resultadosDbpedia);
    onUpdate?.(crearRespuesta(acumulados));
  } catch (error) {
    if (signal?.aborted) {
      throw new DOMException('Busqueda cancelada', 'AbortError');
    }

    aviso = 'DBpedia no respondió. Se muestran los resultados locales encontrados.';
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