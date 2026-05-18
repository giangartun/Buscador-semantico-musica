
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export interface ResultadoBusqueda {
  nombre: string;
  clases: string[];
}

export interface RespuestaBusqueda {
  total: number;
  resultados: ResultadoBusqueda[];
}

export const buscarPorTexto = async (texto: string): Promise<RespuestaBusqueda> => {
  const url = `${API_BASE_URL}/api/buscar?texto=${encodeURIComponent(texto)}`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Error HTTP: ${response.status}`);
  }
  return response.json();
};

export const buscarPorClase = async (clase: string): Promise<RespuestaBusqueda> => {
  const url = `${API_BASE_URL}/api/buscar?clase=${encodeURIComponent(clase)}`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Error HTTP: ${response.status}`);
  }
  return response.json();
};

export const verificarSaludBackend = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
};