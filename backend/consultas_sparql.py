import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen
from owlready2 import default_world, Thing
import types
import motor_semantico
import unicodedata  # Acceso directo a nuestra ontología en memoria RAM

# Configuración de Endpoints usando lookup
DBPEDIA_LOOKUP_ENDPOINT = "https://lookup.dbpedia.org/api/search"
DBPEDIA_SPARQL_ENDPOINT = "https://dbpedia.org/sparql"

# Diccionario de mapeo directo para música clásica.
# Esto garantiza que cuando busquen autores clave, el enlace a DBpedia sea instantáneo.
PHRASE_RESOURCE_MAP = {
    # ==========================================
    # AUTORES CLAVE (INTERCEPCIÓN DIRECTA)
    # ==========================================
    "mozart": ["Wolfgang_Amadeus_Mozart", "List_of_compositions_by_Wolfgang_Amadeus_Mozart"],
    "beethoven": ["Ludwig_van_Beethoven", "List_of_compositions_by_Ludwig_van_Beethoven"],
    "bach": ["Johann_Sebastian_Bach", "List_of_compositions_by_Johann_Sebastian_Bach"],
    "chopin": ["Frédéric_Chopin", "List_of_compositions_by_Frédéric_Chopin_by_genre"],
    "schubert": ["Franz_Schubert", "List_of_compositions_by_Franz_Schubert"],
    "liszt": ["Franz_Liszt", "List_of_compositions_by_Franz_Liszt"],
    "vivaldi": ["Antonio_Vivaldi", "List_of_compositions_by_Antonio_Vivaldi"],
    "rachmaninoff": ["Sergei_Rachmaninoff", "List_of_compositions_by_Sergei_Rachmaninoff"],
    "tchaikovsky": ["Pyotr_Ilyich_Tchaikovsky", "List_of_compositions_by_Pyotr_Ilyich_Tchaikovsky"],
    "paganini": ["Niccolò_Paganini", "List_of_compositions_by_Niccolò_Paganini"],
    "strauss": ["Johann_Strauss_II", "List_of_compositions_by_Johann_Strauss_II"],
    "handel": ["George_Frideric_Handel", "List_of_compositions_by_George_Frideric_Handel"],
    "piazzolla": ["Astor_Piazzolla"],
    "jarre": ["Jean_Michel_Jarre"],
    "debussy": ["Claude_Debussy"],

    # ==========================================
    # INSTRUMENTOS TRILINGÜES (ES / EN / FR)
    # ==========================================
    # Piano
    "piano": ["Piano"], "pianos": ["Piano"], "pianoforte": ["Piano"],
    
    # Violín
    "violin": ["Violin"], "violines": ["Violin"], "violín": ["Violin"], 
    "fiddle": ["Violin"], "violins": ["Violin"], "violon": ["Violin"], "violons": ["Violin"],
    
    # Guitarra
    "guitarra": ["Guitar"], "guitarras": ["Guitar"], "guitar": ["Guitar"], 
    "guitars": ["Guitar"], "guitare": ["Guitar"], "guitares": ["Guitar"],
    
    # Flauta
    "flauta": ["Flute"], "flautas": ["Flute"], "flute": ["Flute"], 
    "flutes": ["Flute"], "flûte": ["Flute"], "flûtes": ["Flute"],
    
    # Oboe
    "oboe": ["Oboe"], "oboes": ["Oboe"], "hautbois": ["Oboe"],
    
    # Trompeta
    "trompeta": ["Trumpet"], "trompetas": ["Trumpet"], "trumpet": ["Trumpet"], 
    "trumpets": ["Trumpet"], "trompette": ["Trumpet"], "trompettes": ["Trumpet"],
    
    # Clarinete
    "clarinete": ["Clarinet"], "clarinetes": ["Clarinet"], "clarinet": ["Clarinet"], 
    "clarinets": ["Clarinet"], "clarinette": ["Clarinet"], "clarinettes": ["Clarinet"],
    
    # Teclado
    "teclado": ["Keyboard"], "teclados": ["Keyboard"], 
    "keyboard": ["Keyboard"], "keyboards": ["Keyboard"], 
    "clavier": ["Keyboard"], "claviers": ["Keyboard"],
    
    # Arpa
    "arpa": ["Harp"], "arpas": ["Harp"], "harp": ["Harp"], 
    "harps": ["Harp"], "harpe": ["Harp"], "harpes": ["Harp"],
    
    # Cimbalum
    "cimbalum": ["Cimbalom"], "cimbales": ["Cimbalom"], "cimbalom": ["Cimbalom"], 
    "cimbals": ["Cimbalom"], "cymbalum": ["Cimbalom"], "cymbales": ["Cimbalom"], 
    "cymbal": ["Cimbalom"], "cymbals": ["Cimbalom"],
    
    # Clavicordio
    "clavicordio": ["Clavichord"], "clavicordios": ["Clavichord"], "clavichord": ["Clavichord"], 
    "clavichords": ["Clavichord"], "clavicorde": ["Clavichord"], "clavicordes": ["Clavichord"],
    
    # Contrabajo
    "contrabajo": ["Double_bass"], "contrabajos": ["Double_bass"], "double bass": ["Double_bass"], 
    "double basses": ["Double_bass"], "contrebasse": ["Double_bass"], "contrebasses": ["Double_bass"],
    
    # Mandolina
    "mandolina": ["Mandolin"], "mandolinas": ["Mandolin"], "mandolin": ["Mandolin"], 
    "mandolins": ["Mandolin"], "mandoline": ["Mandolin"], "mandolines": ["Mandolin"],
    
    # Corno
    "corno": ["French_horn"], "corni": ["French_horn"], "horn": ["French_horn"], 
    "horns": ["French_horn"], "cor": ["French_horn"], "cors": ["French_horn"],
    
    # Saxofón
    "saxofon": ["Saxophone"], "saxofones": ["Saxophone"], "saxophone": ["Saxophone"], "saxophones": ["Saxophone"],
    
    # Trombón
    "trombon": ["Trombone"], "trombones": ["Trombone"], "trombone": ["Trombone"],
    
    # Tuba
    "tuba": ["Tuba"], "tubas": ["Tuba"],
    
    # Aerófono
    "aerofono": ["Aerophone"], "aerofonos": ["Aerophone"], "aerophone": ["Aerophone"], 
    "aerophones": ["Aerophone"], "aérophone": ["Aerophone"], "aérophones": ["Aerophone"],

    # ==========================================
    # FAMILIAS Y CATEGORÍAS (ES / EN / FR)
    # ==========================================
    # Percusión
    "percusion": ["Percussion_instrument"], "percusión": ["Percussion_instrument"], 
    "percussion": ["Percussion_instrument"], "percussions": ["Percussion_instrument"], "drums": ["Percussion_instrument"],
    
    # Cuerda
    "cuerda": ["String_instrument"], "cuerdas": ["String_instrument"], 
    "string": ["String_instrument"], "strings": ["String_instrument"], "corde": ["String_instrument"], "cordes": ["String_instrument"],
    
    # Viento
    "viento": ["Wind_instrument"], "vientos": ["Wind_instrument"], "wind": ["Wind_instrument"], 
    "winds": ["Wind_instrument"], "brass": ["Brass_instrument"], "vent": ["Wind_instrument"], "vents": ["Wind_instrument"],
    
    # Viento Madera
    "viento madera": ["Woodwind instrument"], "woodwind": ["Woodwind instrument"], 
    "woodwinds": ["Woodwind_instrument"], "bois": ["Woodwind_instrument"],
    
    # Madera y Metal
    "madera": ["Wood"], "wood": ["Wood"],
    "metal": ["Metal"], "metales": ["Metal"], "brass": ["Brass_instrument"], "métal": ["Metal"], "métaux": ["Metal"],

    # ==========================================
    # PERIODOS HISTÓRICOS (ES / EN / FR)
    # ==========================================
    "romantico": ["Romantic_music"], "romántico": ["Romantic_music"], "romantic": ["Romantic_music"], 
    "romanticism": ["Romanticism"], "romantique": ["Romantic_music"], "romantisme": ["Romanticism"],
    
    "barroco": ["Baroque_music"], "baroque": ["Baroque_music"],
    
    "clasico": ["Classical_period_(music)"], "clásico": ["Classical_period_(music)"], 
    "classical": ["Classical_period_(music)"], "classic": ["Classical_period_(music)"], "classique": ["Classical_period_(music)"],

    # =========================================================================
    # MULTI-RESULTADOS: LISTADOS MÚLTIPLES DIRECTOS
    # =========================================================================
    "composicion": ["Catalogues_of_classical_compositions"], 
    "composición": ["Catalogues_of_classical_compositions"], 
    "composition": ["Catalogues_of_classical_compositions"],
    "piece": ["Musical_composition"], "work": ["Musical_composition"], "track": ["Musical_composition"], "piste": ["Musical_composition"], "pièce": ["Musical_composition"],
    "music": ["Music"], "oeuvre": ["Musical_composition"], "œuvre": ["Musical_composition"], "morceau": ["Musical_composition"],
    "song": ["Song"], "cancion": ["Song"], "canción": ["Song"],"chanson": ["Song"], "chansons": ["Song"], "chanson": ["Song"],
    
    # Composiciones / Obras
    "composiciones": [
        "Catalogues_of_classical_compositions",
        "List_of_compositions_by_Johann_Sebastian_Bach",
        "List_of_compositions_by_Franz_Schubert",
        "List_of_compositions_by_Frédéric_Chopin_by_genre",
        "List_of_compositions_by_Ludwig_van_Beethoven",
        "List_of_compositions_by_Wolfgang_Amadeus_Mozart"
    ],
    "compositions": [
        "Catalogues_of_classical_compositions",
        "List_of_compositions_by_Johann_Sebastian_Bach",
        "List_of_compositions_by_Franz_Schubert",
        "List_of_compositions_by_Ludwig_van_Beethoven"
    ],
    "pieces": [
        "Catalogues_of_classical_compositions",
        "List_of_compositions_by_Johann_Sebastian_Bach",
        "List_of_compositions_by_Franz_Schubert",
        "List_of_compositions_by_Ludwig_van_Beethoven"
    ],
    "works": ["Compositions"], "tracks": ["Compositions"], "oeuvres": ["Compositions"], "œuvres": ["Compositions"], "morceaux": ["Compositions"],
    
    # Fantasía
    "fantasia": ["Fantaisie"], "fantasía": ["Fantaisie"], "fantasy": ["Fantaisie"], "fantaisie": ["Fantaisie"],
    
    # Artista / Compositor
    "artista": ["Composer"], "musico": ["Composer"], "músico": ["Composer"], "autor": ["Composer"], 
    "creador": ["Composer"], "artist": ["Composer"], "composer": ["Composer"], "author": ["Composer"], 
    "compositeur": ["Composer"], "auteur": ["Composer"],
    
    # Sinfonía
    "sinfonia": ["Symphony"], "sinfonía": ["Symphony"], "symphony": ["Symphony"], 
    "symphonies": ["Symphony"], "symphonie": ["Symphony"],
    
    # Sonata
    "sonata": ["Sonata"], "sonatas": ["Sonata"], "sonate": ["Sonata"],

    # ==========================================
    # NIVELES DE DIFICULTAD (CONCEPTUAL RECURSO)
    # ==========================================
    "alta": ["Complexity"], "alto": ["Complexity"], "high": ["Complexity"], "hard": ["Complexity"], 
    "complex": ["Complexity"], "difficult": ["Complexity"], "avanzado": ["Complexity"], 
    "advanced": ["Complexity"], "haute": ["Complexity"], "complexe": ["Complexity"], "difficile": ["Complexity"],
    
    "media": ["Average"], "medio": ["Average"], "medium": ["Average"], "intermediate": ["Average"], 
    "normal": ["Average"], "moyenne": ["Average"], "intermédiaire": ["Average"],
    
    "baja": ["Simplicity"], "bajo": ["Simplicity"], "low": ["Simplicity"], "easy": ["Simplicity"], 
    "simple": ["Simplicity"], "facil": ["Simplicity"], "fácil": ["Simplicity"], "basse": ["Simplicity"], "facile": ["Simplicity"],

    # =========================================================================
    # 1. FORMAS Y GÉNEROS MUSICALES ESTRUCTURALES (ES / EN / FR)
    # =========================================================================
    # Concierto
    "concierto": ["Concerto"], "conciertos": ["Concerto"], 
    "concerto": ["Concerto"], "concertos": ["Concerto"], 
    "concert": ["Concerto"], "concerts": ["Concerto"],
    
    # Ópera
    "opera": ["Opera"], "ópera": ["Opera"], "operas": ["Opera"], 
    "operes": ["Opera"],
    
    # Preludio
    "preludio": ["Prelude"], "preludios": ["Prelude"], 
    "prelude": ["Prelude"], "preludes": ["Prelude"], 
    "prélude": ["Prelude"], "préludes": ["Prelude"],
    
    # Fuga
    "fuga": ["Fugue"], "fugas": ["Fugue"], 
    "fugue": ["Fugue"], "fugues": ["Fugue"],
    
    # Nocturno
    "nocturno": ["Nocturne"], "nocturnos": ["Nocturne"], 
    "nocturne": ["Nocturne"], "nocturnes": ["Nocturne"],

    # =========================================================================
    # 2. ROLES DEL DOMINIO E INTÉRPRETES (ES / EN / FR)
    # =========================================================================
    # Director / Orquesta
    "director": ["Music_director"], "directores": ["Music_director"], 
    "conductor": ["Music_director"], "conductors": ["Music_director"], 
    "chef d orchestre": ["Music_director"], "orquesta": ["Orchestra"], 
    "orchestra": ["Orchestra"], "orchestre": ["Orchestra"],
    
    # Pianista
    "pianista": ["Pianist"], "pianistas": ["Pianist"], 
    "pianist": ["Pianist"], "pianists": ["Pianist"], 
    "pianiste": ["Pianist"], "pianistes": ["Pianist"],
    
    # Violinista
    "violinista": ["Violinist"], "violinistas": ["Violinist"], 
    "violinist": ["Violinist"], "violinists": ["Violinist"], 
    "violoniste": ["Violinist"], "violonistes": ["Violinist"],
    
    # Violonchelista
    "violonchelista": ["Cellist"], "violonchelistas": ["Cellist"], 
    "cellist": ["Cellist"], "cellists": ["Cellist"], 
    "celliste": ["Cellist"], "cellistes": ["Cellist"],

    # =========================================================================
    # 3. VOCABULARIO TÉCNICO Y TEORÍA DE PARTITURAS (ES / EN / FR)
    # =========================================================================
    # Partitura / Registro
    "partitura": ["Sheet_music"], "partituras": ["Sheet_music"], 
    "score": ["Sheet_music"], "scores": ["Sheet_music"], "sheet music": ["Sheet_music"], 
    "partition": ["Sheet_music"], "partitions": ["Sheet_music"],
    
    # Ritmo
    "ritmo": ["Rhythm"], "ritmos": ["Rhythm"], 
    "rhythm": ["Rhythm"], "rhythms": ["Rhythm"], 
    "rythme": ["Rhythm"], "rythmes": ["Rhythm"],
    
    # Melodía
    "melodia": ["Melody"], "melodía": ["Melody"], "melodias": ["Melody"], 
    "melody": ["Melody"], "melodies": ["Melody"], 
    "melodie": ["Melody"], "mélodie": ["Melody"], "mélodies": ["Melody"],
    
    # Armonía
    "armonia": ["Harmony"], "armonía": ["Harmony"], 
    "harmony": ["Harmony"], "harmonies": ["Harmony"], 
    "harmonie": ["Harmony"], "harmonies": ["Harmony"],
    
    # Tempo / Escala
    "tempo": ["Tempo"], "tempos": ["Tempo"], "mouvement": ["Tempo"], 
    "escala": ["Scale_(music)"], "escalas": ["Scale_(music)"], 
    "scale": ["Scale_(music)"], "scales": ["Scale_(music)"], 
    "gamme": ["Scale_(music)"], "gammes": ["Scale_(music)"],
}

STOPWORDS = {"de", "del", "la", "el", "los", "las", "en", "con", "y", "por", "para", "un", "una", "al", "a"}

def _safe_first(values, default=None):
    if not values:
        return default
    return values[0]

def consultar_dbpedia_detalles(uri):
    """
    Obtiene mas campos desde DBpedia por SPARQL (abstract, fechas, genero, instrumento, imagen, lugar, nacionalidad, obras).
    """
    query = f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    SELECT ?abstract ?birthDate ?deathDate ?genreLabel ?instrumentLabel ?birthPlaceLabel ?nationalityLabel ?notableWorkLabel ?thumbnail ?wiki
    WHERE {{
        OPTIONAL {{ <{uri}> dbo:abstract ?abstract . FILTER(lang(?abstract) = "es") }}
        OPTIONAL {{ <{uri}> dbo:abstract ?abstract . FILTER(lang(?abstract) = "en") }}
        OPTIONAL {{ <{uri}> dbo:birthDate ?birthDate . }}
        OPTIONAL {{ <{uri}> dbo:deathDate ?deathDate . }}
        OPTIONAL {{ <{uri}> dbo:genre ?genre . ?genre rdfs:label ?genreLabel . FILTER(lang(?genreLabel) = "es") }}
        OPTIONAL {{ <{uri}> dbo:instrument ?instrument . ?instrument rdfs:label ?instrumentLabel . FILTER(lang(?instrumentLabel) = "es") }}
        OPTIONAL {{ <{uri}> dbo:birthPlace ?birthPlace . ?birthPlace rdfs:label ?birthPlaceLabel . FILTER(lang(?birthPlaceLabel) = "es") }}
        OPTIONAL {{ <{uri}> dbo:nationality ?nationality . ?nationality rdfs:label ?nationalityLabel . FILTER(lang(?nationalityLabel) = "es") }}
        OPTIONAL {{ <{uri}> dbo:notableWork ?notableWork . ?notableWork rdfs:label ?notableWorkLabel . FILTER(lang(?notableWorkLabel) = "es") }}
        OPTIONAL {{ <{uri}> dbo:thumbnail ?thumbnail . }}
        OPTIONAL {{ <{uri}> foaf:isPrimaryTopicOf ?wiki . }}
    }}
    """

    url = f"{DBPEDIA_SPARQL_ENDPOINT}?query={quote(query)}&format=json"
    request = Request(
        url,
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": "SemanticMusicApp-Academic/1.0",
        },
    )

    try:
        with urlopen(request, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}

    rows = data.get("results", {}).get("bindings", [])
    if not rows:
        return {}

    abstract = None
    birth_date = None
    death_date = None
    thumbnail = None
    wikipedia = None
    genres = set()
    instruments = set()
    birth_places = set()
    nationalities = set()
    notable_works = set()

    for row in rows:
        if not abstract:
            abstract = row.get("abstract", {}).get("value")
        if not birth_date:
            birth_date = row.get("birthDate", {}).get("value")
        if not death_date:
            death_date = row.get("deathDate", {}).get("value")
        if not thumbnail:
            thumbnail = row.get("thumbnail", {}).get("value")
        if not wikipedia:
            wikipedia = row.get("wiki", {}).get("value")

        genre_label = row.get("genreLabel", {}).get("value")
        if genre_label:
            genres.add(genre_label)

        instrument_label = row.get("instrumentLabel", {}).get("value")
        if instrument_label:
            instruments.add(instrument_label)

        birth_place_label = row.get("birthPlaceLabel", {}).get("value")
        if birth_place_label:
            birth_places.add(birth_place_label)

        nationality_label = row.get("nationalityLabel", {}).get("value")
        if nationality_label:
            nationalities.add(nationality_label)

        notable_work_label = row.get("notableWorkLabel", {}).get("value")
        if notable_work_label:
            notable_works.add(notable_work_label)

    return {
        "abstract": abstract,
        "birthDate": birth_date,
        "deathDate": death_date,
        "genres": sorted(genres),
        "instruments": sorted(instruments),
        "birthPlaces": sorted(birth_places),
        "nationalities": sorted(nationalities),
        "notableWorks": sorted(notable_works),
        "thumbnail": thumbnail,
        "wikipediaPage": wikipedia,
    }

def consultar_por_sparql_local(texto_busqueda):
    """
    Ejecuta una consulta SPARQL nativa utilizando el motor interno de Owlready2.
    """
    onto = motor_semantico.cargar_y_razonar()
    if not onto:
        return []

    print(f"\n[SPARQL Local] Buscando instancias locales que coincidan con: '{texto_busqueda}'...")
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
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
    Consulta remota utilizando la estrategia híbrida optimizada trilingüe.
    """
    if not nombre_artista:
        return []

    # =========================================================================
    # NORMALIZACIÓN ULTRA ESTRICTA (IGUAL QUE EN EL MOTOR SEMÁNTICO)
    # =========================================================================
    # 1. Pasar a minúsculas y limpiar espacios de los extremos
    texto = str(nombre_artista).lower().strip()
    # 2. Descomponer caracteres para remover acentos/diacríticos
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    # 3. Remover guiones o guiones bajos y colapsar espacios internos duplicados
    termino_limpio = " ".join(texto.replace("_", " ").replace("-", " ").split())

    print(f"\n[DBpedia] Buscando información externa para: '{nombre_artista}' (Limpio: '{termino_limpio}')...")

    # =========================================================================
    # INTERCEPTOR TRILINGÜE DE LISTADOS LARGOS (EVITA TIMEOUTS EN LOOKUP)
    # =========================================================================
    indicadores_listado = [
        "list of compositions by", "list of works by", "pieces of",
        "lista de obras de", "composiciones de", "obras de",
        "liste des compositions de", "oeuvres de", "œuvres de"
    ]
    
    for indicador in indicadores_listado:
        if indicador in termino_limpio:
            posible_autor = termino_limpio.split(indicador)[-1].strip()
            print(f"[DBpedia Redirección Trilingüe] Detectado listado complejo. Buscando directamente al autor: '{posible_autor}'")
            return consultar_dbpedia_artistas(posible_autor)

    # Contingencia secundaria por palabras clave sueltas de listados estructurales
    autores_sistema = ["vivaldi", "piazzolla", "liszt", "chopin", "jarre", "bach", "beethoven", "paganini", "tchaikovsky", "rachmaninoff", "mozart", "debussy", "strauss", "handel", "schubert"]
    if any(ind in termino_limpio for ind in ["list", "compositions", "liste", "oeuvres", "obras"]):
        for autor in autores_sistema:
            if autor in termino_limpio:
                print(f"[DBpedia Contingencia] Extrayendo palabra raíz del autor: '{autor}'")
                return consultar_dbpedia_artistas(autor)

    # =========================================================================
    # Estrategia 1: Mapeo directo por diccionario (REPLAZADO Y BLINDADO)
    # =========================================================================
    if termino_limpio in PHRASE_RESOURCE_MAP:
        print(f"[DBpedia] Coincidencia directa encontrada en el mapa musical para '{termino_limpio}'.")
        recursos = PHRASE_RESOURCE_MAP[termino_limpio]
        resultados = []
        
        for res in recursos:
            uri = f"http://dbpedia.org/resource/{res}"
            
            # BLINDAJE ULTRA-RÁPIDO: Evita llamar a internet si es una página estructural de listado
            if "List_of" in res or "Catalogues" in res:
                detalles = {
                    "abstract": f"Índice y catálogo estructural de las obras y partituras históricas de {res.replace('List_of_compositions_by_', '').replace('_', ' ')}.",
                    "birthDate": None, "deathDate": None, "genres": [], "instruments": [],
                    "birthPlaces": [], "nationalities": [], "notableWorks": [], "thumbnail": None, "wikipediaPage": None
                }
            else:
                # Solo hace la llamada SPARQL real para la biografía principal del autor
                detalles = consultar_dbpedia_detalles(uri)

            resultados.append({
                "uri_dbpedia": uri,
                "nombre": res.replace("_", " "),
                "descripcion": f"Recurso histórico musical de alta relevancia en DBpedia.",
                **detalles,
            })

        if motor_semantico._onto_instancia is not None:
            poblar_ontologia_con_dbpedia(resultados, "Compositor")

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
        with urlopen(request, timeout=12) as response:
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

                detalles = consultar_dbpedia_detalles(uri)
                resultados_limpios.append({
                    "uri_dbpedia": uri,
                    "nombre": nombre,
                    "descripcion": desc,
                    **detalles,
                })

        if resultados_limpios:
            # Poblamos sobre nuestra ontologia activa si ya esta en memoria
            if motor_semantico._onto_instancia is not None:
                poblar_ontologia_con_dbpedia(resultados_limpios, "Compositor")
            return resultados_limpios

        return []

    except Exception as e:
        print(f"[DBpedia] Falló la conexión con el servicio Lookup: {e}")
        return []

def poblar_ontologia_con_dbpedia(datos_remotos, nombre_clase_local="Compositor"):
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