import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen
from owlready2 import default_world, Thing
import types
import motor_semantico  # Acceso directo a nuestra ontología en memoria RAM

# Configuración de Endpoints usando la estrategia del otro grupo
DBPEDIA_LOOKUP_ENDPOINT = "https://lookup.dbpedia.org/api/search"

# Diccionario de mapeo directo para música clásica.
# Esto garantiza que cuando busquen autores clave, el enlace a DBpedia sea instantáneo e infalible.
PHRASE_RESOURCE_MAP = {
    "mozart": ["Wolfgang_Amadeus_Mozart"],
    "wolfgang amadeus mozart": ["Wolfgang_Amadeus_Mozart"],
    "chopin": ["Frédéric_Chopin"],
    "frederic chopin": ["Frédéric_Chopin"],
    "beethoven": ["Ludwig_van_Beethoven"],
    "ludwig van beethoven": ["Ludwig_van_Beethoven"],
    "bach": ["Johann_Sebastian_Bach"],
    "johann sebastian bach": ["Johann_Sebastian_Bach"],
    "piano": ["Piano"],
    "violin": ["Violin"],
    "violín": ["Violin"],
}

STOPWORDS = {"de", "del", "la", "el", "los", "las", "en", "con", "y", "por", "para", "un", "una", "al", "a"}

def consultar_por_sparql_local(texto_busqueda):
    """
    Ejecuta una consulta SPARQL nativa utilizando el motor interno de Owlready2.
    """
    onto = motor_semantico.cargar_y_razonar()
    if not onto:
        return []

    print(f"\n[SPARQL Local] Buscando instancias locales que coincidan con: '{texto_busqueda}'...")
    query = f"""
    SELECT ?individuo ?clase
    WHERE {{
        ?individuo rdf:type ?clase .
        FILTER(?clase != owl:NamedIndividual)
        FILTER(regex(str(?individuo), "{texto_busqueda}", "i"))
    }}
    """
    try:
        resultados_raw = list(default_world.sparql(query))
        return [{
            "nombre_individuo": fila[0].name,
            "clase_maestra": fila[1].name
        } for fila in resultados_raw if hasattr(fila[0], 'name') and hasattr(fila[1], 'name')]
    except Exception as e:
        print(f"[SPARQL] Error interno: {e}")
        return []

def consultar_dbpedia_artistas(nombre_artista):
    """
    Consulta remota utilizando la estrategia híbrida ganadora del otro grupo:
    Usa el diccionario directo o ataca la API de DBpedia Lookup de forma infalible.
    """
    termino_limpio = nombre_artista.strip().lower()
    print(f"\n[DBpedia] Buscando información externa para: '{nombre_artista}'...")

    # Estrategia 1: Mapeo directo por diccionario (Instantáneo)
    if termino_limpio in PHRASE_RESOURCE_MAP:
        print(f"[DBpedia] Coincidencia directa encontrada en el mapa musical para '{termino_limpio}'.")
        recursos = PHRASE_RESOURCE_MAP[termino_limpio]
        resultados = []
        for res in recursos:
            # Construimos un objeto limpio simulando la respuesta
            resultados.append({
                "uri_dbpedia": f"http://dbpedia.org/resource/{res}",
                "nombre": res.replace("_", " "),
                "descripcion": f"Recurso histórico musical de alta relevancia en DBpedia sobre {res.replace('_', ' ')}."
            })
        poblar_ontologia_con_dbpedia(resultados, "Artista")
        return resultados

    # Estrategia 2: Si no está en el mapa, usamos DBpedia Lookup de forma dinámica
    url = f"{DBPEDIA_LOOKUP_ENDPOINT}?query={quote(nombre_artista)}&format=JSON"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "SemanticMusicApp-Academic/1.0",
        },
    )

    try:
        with urlopen(request, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        docs = data.get("docs", [])
        if not docs:
            print("[DBpedia Lookup] No se encontraron coincidencias en el servidor global.")
            return []

        resultados_limpios = []
        # Traemos hasta 3 resultados del Lookup
        for doc in docs[:3]:
            resource_list = doc.get("resource", [])
            label_list = doc.get("label", [])
            comment_list = doc.get("comment", [])

            if resource_list:
                uri = resource_list[0]
                # Limpiar etiquetas HTML que a veces mete Lookup usando expresiones regulares simples
                nombre = re.sub(r"<[^>]+>", "", label_list[0]) if label_list else nombre_artista
                desc = re.sub(r"<[^>]+>", "", comment_list[0]) if comment_list else "Personaje o elemento del catálogo de música clásica."
                
                if len(desc) > 200: 
                    desc = desc[:200] + "..."

                resultados_limpios.append({
                    "uri_dbpedia": uri,
                    "nombre": nombre,
                    "descripcion": desc
                })

        if resultados_limpios:
            # Poblamos en caliente sobre nuestra ontología activa
            poblar_ontologia_con_dbpedia(resultados_limpios, "Artista")
            return resultados_limpios

        return []

    except Exception as e:
        print(f"[DBpedia] Falló la conexión con el servicio Lookup: {e}")
        return []

def poblar_ontologia_con_dbpedia(datos_remotos, nombre_clase_local="Artista"):
    """
    Inserta los datos recuperados de DBpedia directo en la memoria RAM 
    de la ontología actual, manteniendo el backend compacto y veloz.
    """
    if not datos_remotos:
        return False
        
    onto = motor_semantico.cargar_y_razonar()
    if not onto:
        return False
    
    print(f"[Poblado] Inyectando datos en la sesión activa bajo la clase '{nombre_clase_local}'...")
    ClaseLocal = getattr(onto, nombre_clase_local, None)
    
    if ClaseLocal is None:
        with onto:
            ClaseLocal = types.new_class(nombre_clase_local, (Thing,))
        
    for item in datos_remotos:
        id_individuo = item["nombre"].replace(" ", "_").replace(".", "").strip()
        try:
            with onto:
                nuevo_individuo = ClaseLocal(id_individuo)
                if hasattr(onto, "nombre"):
                    nuevo_individuo.nombre.append(item["nombre"])
                if hasattr(onto, "descripcion"):
                    nuevo_individuo.descripcion.append(item["descripcion"])
                if hasattr(onto, "sameAs"):
                    nuevo_individuo.sameAs.append(item["uri_dbpedia"])
                
            print(f"[Poblado] ¡Éxito! Individuo '{id_individuo}' guardado en memoria RAM.")
            
            # Eliminamos de la caché para forzar al motor a refrescar la lista
            if id_individuo in motor_semantico._serialized_cache:
                del motor_semantico._serialized_cache[id_individuo]
        except Exception as e:
            pass # El individuo ya existía o está duplicado, se maneja de forma segura
            
    return True

# ==========================================
# PRUEBA LOCAL EN CONSOLA
# ==========================================
if __name__ == "__main__":
    # Probamos directo a Mozart
    res = consultar_dbpedia_artistas("Mozart")
    print(f"\nResultados de la prueba técnica: {json.dumps(res, indent=2, ensure_ascii=False)}")