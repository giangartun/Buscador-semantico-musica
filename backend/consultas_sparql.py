from owlready2 import default_world
from motor_semantico import cargar_y_razonar
import json
from SPARQLWrapper import SPARQLWrapper, JSON

def consultar_por_sparql_local(texto_busqueda):
    """
    Ejecuta una consulta SPARQL nativa utilizando el motor interno de Owlready2.
    Valida los tipos de datos para evitar errores con enteros del sistema.
    """
    onto = cargar_y_razonar()
    if not onto:
        print("[SPARQL] Error: No se pudo cargar la ontología.")
        return []

    print(f"\n[SPARQL Local] Buscando instancias que coincidan con: '{texto_busqueda}'...")

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
        resultado_limpio = []
        for fila in resultados_raw:
            if hasattr(fila[0], 'name') and hasattr(fila[1], 'name'):
                resultado_limpio.append({
                    "nombre_individuo": fila[0].name,
                    "clase_maestra": fila[1].name
                })
        return resultado_limpio

    except Exception as e:
        print(f"[SPARQL] Error al ejecutar la consulta: {e}")
        return []

def consultar_dbpedia_artistas(nombre_artista):
    """
    Consulta remota a DBpedia utilizando la librería SPARQLWrapper de forma infalible.
    """
    # Pasamos a minúsculas para hacer un filtro flexible e independiente del sistema operativo
    termino = nombre_artista.strip().lower()
    print(f"\n[SPARQLWrapper] Conectando a DBpedia para buscar: '{nombre_artista}'...")
    
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    
    # QUERY CORREGIDA: Convertimos la etiqueta a string y comparamos en minúsculas.
    # Esto evita los problemas de codificación de Windows con el "@es".
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbo: <http://dbpedia.org/ontology/>

    SELECT DISTINCT ?concepto ?nombre ?descripcion
    WHERE {{
        ?concepto rdfs:label ?nombre .
        ?concepto rdfs:comment ?descripcion .
        
        # Filtros de idioma tradicionales
        FILTER (lang(?nombre) = "es")
        FILTER (lang(?descripcion) = "es")
        
        # Validación exacta de texto plano sin interferencias de red
        FILTER (contains(lcase(str(?nombre)), "{termino}"))
    }}
    LIMIT 1
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    # Cabecera profesional simulando un agente estándar
    sparql.addCustomHttpHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    try:
        resultados = sparql.query().convert()
        resultados_raw = []
        
        # Validación de seguridad por si el JSON viene con estructuras nulas
        if "results" in resultados and "bindings" in resultados["results"]:
            resultados_raw = resultados["results"]["bindings"]
        
        if len(resultados_raw) > 0:
            resultados_limpios = []
            for fila in resultados_raw:
                desc = fila["descripcion"]["value"]
                if len(desc) > 180: desc = desc[:180] + "..."
                
                resultados_limpios.append({
                    "uri_dbpedia": fila["concepto"]["value"],
                    "nombre": fila["nombre"]["value"],
                    "descripcion": desc
                })
            return resultados_limpios
            
        print("[SPARQLWrapper] El servidor respondió con éxito, pero la tabla de resultados vino VACÍA (0 filas).")
        return []
        
    except Exception as e:
        print(f"[SPARQLWrapper] Error de red o sintaxis al conectar con DBpedia: {e}")
        return []

def poblar_ontologia_con_dbpedia(datos_remotos, nombre_clase_local="Instrumento"):
    """
    Agarra los datos descargados en vivo de DBpedia y los inserta (pobla)
    dentro de la ontología local en memoria usando Owlready2.
    """
    if not datos_remotos:
        print("[Poblado] No hay datos remotos para insertar.")
        return False
        
    onto = cargar_y_razonar()
    
    print(f"\n[Poblado] Iniciando inserción de datos en la clase local: '{nombre_clase_local}'...")
    
    # Buscamos la clase dentro de tu ontología (ej: onto.Instrumento o onto.Artista)
    ClaseLocal = getattr(onto, nombre_clase_local, None)
    
    if ClaseLocal is None:
        print(f"[Poblado] Error: La clase '{nombre_clase_local}' no existe en tu ontología musica.owl.")
        return False
        
    for item in datos_remotos:
        # Reemplazamos espacios para crear un ID de individuo válido en la ontología
        id_individuo = item["nombre"].replace(" ", "_").strip()
        
        # Creamos el nuevo individuo de forma real dentro de tu ontología
        with onto:
            nuevo_individuo = ClaseLocal(id_individuo)
            
            # Le asignamos las propiedades semánticas si tu ontología las tiene definidas
            # (Ej: si tienes data properties como 'tieneDescripcion' o 'tieneUriGlobal')
            if hasattr(onto, "tieneDescripcion"):
                nuevo_individuo.tieneDescripcion.append(item["descripcion"])
            
            # Mapeo Linked Open Data: Guardamos la relación con la URI de internet
            if hasattr(onto, "sameAs"): 
                # owl:sameAs es la propiedad estándar para enlazar a DBpedia
                nuevo_individuo.sameAs.append(item["uri_dbpedia"])
                
        print(f"[Poblado] ¡Éxito! Se ha creado el individuo '{id_individuo}' en la ontología local.")
        
    # Guardamos los cambios físicamente en el archivo para que el cambio sea permanente
    try:
        onto.save(file="musica_poblada.owl", format="rdfxml")
        print("[Poblado] Ontología guardada con éxito en 'musica_poblada.owl' con los nuevos datos de DBpedia.")
        return True
    except Exception as e:
        print(f"[Poblado] Error al guardar el archivo OWL: {e}")
        return False
# ==========================================
# PRUEBA EN VIVO CONEXIÓN A DBPEDIA Y POBLADO DE ONTOLOGÍA LOCAL
# ==========================================
if __name__ == "__main__":
    # 1. Tu motor local (procesando tus axiomas e inferencias en memoria)
    termino_local = "Afinacion"
    res_local = consultar_por_sparql_local(termino_local)
    print(f"--- [SPARQL Local] Se encontraron {len(res_local)} resultados ---")
        # 1. Buscamos en internet (DBpedia) de forma REAL
    termino_remoto = "Guitarra"
    datos_internet = consultar_dbpedia_artistas(termino_remoto)
    
    # 2. Si internet nos dio resultados, POBLAMOS la ontología local con ellos
    if datos_internet:
        # Pasamos los datos y le decimos bajo qué clase de tu ontología guardarlos
        poblar_ontologia_con_dbpedia(datos_internet, nombre_clase_local="Instrumento")