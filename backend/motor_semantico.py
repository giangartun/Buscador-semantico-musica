import os
import unicodedata
from owlready2 import *

# Configuración de la ruta de la ontología
ruta_ontologia = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ontology", "musica.owl"))

# Variables globales para persistencia en memoria RAM y optimización de velocidad
_onto_instancia = None
_serialized_cache = {}

# Prefijos semánticos típicos a remover para limpiar la interfaz del frontend
PREFIXES_TO_REMOVE = ["Inst_", "Art_", "Gen_", "Alb_", "Can_", "Obra_", "Aut_"]

SYNONYMS = {
    # Instrumentos (ES / EN / FR)
    "violin": ["violin", "violines", "violín", "fiddle", "violins", "violon", "violons"],
    "piano": ["piano", "pianos", "pianoforte"],
    "guitarra": ["guitarra", "guitarras", "guitar", "guitars", "guitare", "guitares"],
    "flauta": ["flauta", "flautas", "flute", "flutes", "flûte", "flûtes"],
    "oboe": ["oboe", "oboes", "hautbois"],
    "trompeta": ["trompeta", "trompetas", "trumpet", "trumpets", "trompette", "trompettes"],
    "clarinete": ["clarinete", "clarinetes", "clarinet", "clarinets", "clarinette", "clarinettes"],
    "teclado": ["teclado", "teclados", "keyboard", "keyboards", "piano", "pianos", "clavier", "claviers"],
    "arpa": ["arpa", "arpas", "harp", "harps", "harpe", "harpes"],
    "cimbalum": ["cimbalum", "cimbales", "cimbalom", "cimbals", "cymbalum", "cymbales", "cymbal", "cymbals"],
    "clavicordio": ["clavicordio", "clavicordios", "clavichord", "clavichords", "clavicorde", "clavicordes"],
    "contrabajo": ["contrabajo", "contrabajos", "double bass", "double basses", "contrebasse", "contrebasses"],
    "mandolina": ["mandolina", "mandolinas", "mandolin", "mandolins", "mandoline", "mandolines"],
    "corno": ["corno", "corni", "horn", "horns", "cor", "cors"],
    "saxofon": ["saxofon", "saxofones", "saxophone", "saxophones", "saxophone", "saxophones"],
    "trombon": ["trombon", "trombones", "trombone", "trombones", "trombone", "trombones"],
    "tuba": ["tuba", "tubas", "tuba", "tubas", "tuba", "tubas"],
    "aerofono": ["aerofono", "aerofonos", "aerophone", "aerophones", "aérophone", "aérophones"],
    # Familias y Categorías (ES / EN / FR)
    "percusion": ["percusion", "percusión", "percussion", "percussions", "drums"],
    "cuerda": ["cuerda", "cuerdas", "string", "strings", "corde", "cordes"],
    "viento": ["viento", "vientos", "wind", "winds", "brass", "vent", "vents"],
    "viento madera": ["viento madera", "woodwind", "woodwinds", "bois"],
    "madera": ["madera", "wood", "bois"],
    "metal": ["metal", "metales", "metal", "métal", "métaux"],        
    # Periodos Históricos (ES / EN / FR)
    "romantico": ["romantico", "romántico", "romantic", "romanticism", "romantique", "romantisme"],
    "barroco": ["barroco", "baroque"],
    "clasico": ["clasico", "clásico", "classical", "classic", "classique"],
    # Conceptos Generales de la Ontología (ES / EN / FR)
    "composicion": ["composicion", "composición", "composition", "piece", "work", "track", "music", "œuvre", "oeuvre", "morceau"],
    "composiciones": ["composiciones", "compositions", "pieces", "works", "tracks", "œuvres", "oeuvres", "morceaux"],
    "fantasía": ["fantasia", "fantasía", "fantasy", "fantaisie"],
    "artista": ["artista", "musico", "músico", "autor", "creador", "artist", "composer", "author", "compositeur", "auteur"],
    "sinfonia": ["sinfonia", "sinfonía", "symphony", "symphonies", "symphonie", "symphonies"],
    "sonata": ["sonata", "sonatas", "sonate"],
    
    # Niveles de dificultad (ES / EN / FR)
    "alta": ["alta", "alto", "high", "hard", "complex", "difficult", "avanzado", "advanced", "haute", "complexe", "difficile"],
    "media": ["media", "medio", "medium", "intermediate", "normal", "moyenne", "intermédiaire"],
    "baja": ["baja", "bajo", "low", "easy", "simple", "facil", "fácil", "basse", "facile"]
}

def expandir_tokens(tokens):
    resultado = []

    for token in tokens:
        agregado = False

        for base, variantes in SYNONYMS.items():
            if token in variantes:
                resultado.extend(variantes)
                agregado = True
                break

        if not agregado:
            resultado.append(token)

    return list(set(resultado))

def cargar_y_razonar():
    """Carga la ontología y ejecuta el razonador HermiT en una ruta segura (una sola vez)."""
    global _onto_instancia
    if _onto_instancia is not None:
        return _onto_instancia
        
    try:
        print("[Motor] Cargando ontología musical por primera vez...")
        onto = get_ontology(f"file://{ruta_ontologia}").load()
        
        carpeta_segura = os.path.abspath(os.path.join(os.path.dirname(__file__), "propio_temp"))
        os.makedirs(carpeta_segura, exist_ok=True)
        
        print("Ejecutando razonador en entorno seguro...")
        try:
            with onto:
                sync_reasoner(infer_property_values=True)
        except Exception as reasoner_error:
            # Si HermiT falla, conservamos la ontología cargada para no romper la búsqueda.
            print(f"[Motor] Razonador no disponible, usando ontología sin inferencias: {reasoner_error}")

        _onto_instancia = onto
        print("[Motor] ¡Ontología cargada en memoria!")
        return _onto_instancia
        
    except Exception as e:
        print(f"Error al inicializar la ontología: {e}")
        return None

# ==========================================
# UTILIDADES DE TEXTO Y TRADUCCIÓN DE DATOS
# ==========================================
def normalize_text(text):
    if text is None: return ""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.replace("_", " ").replace("-", " ").split())

def clean_ontology_name(value):
    if value is None: return "-"
    text = value.name if hasattr(value, "name") else str(value)
    if "#" in text: text = text.split("#")[-1]
    for prefix in PREFIXES_TO_REMOVE:
        text = text.replace(prefix, "")
    return text.replace("_", " ").strip()

def to_bool(value):
    return str(value).lower() in ["true", "1", "si", "sí", "verdadero", "yes"]

def to_int(value):
    try: return int(float(value))
    except: return 0

def get_first_value(individual, property_name, default="-"):
    try:
        valores = getattr(individual, property_name, [])
        return valores[0] if valores else default
    except:
        return default

# ==========================================
# SERIALIZADOR DE INDIVIDUOS PARA EL FRONTEND
# ==========================================
def serialize_element(ind):
    """Transforma un individuo complejo de Owlready2 en un diccionario plano con caché."""
    if ind.name in _serialized_cache:
        return dict(_serialized_cache[ind.name])

    # Propiedades de datos teóricas e históricas
    nombre = get_first_value(ind, "nombre", ind.name)
    descripcion = get_first_value(ind, "descripcion", "-")
    periodo = get_first_value(ind, "periodoHistorico", "-")       # Ej: Barroco, Romántico
    dificultad = get_first_value(ind, "complejidadTecnica", "-")   # Ej: Alta, Media, Baja
    anio = get_first_value(ind, "anioLanzamiento", "-")            # Año de composición o publicación

    # Relaciones entre objetos
    creador = clean_ontology_name(get_first_value(ind, "creadoPor", None))          # Obras -> Autor
    instrumento = clean_ontology_name(get_first_value(ind, "seTocaCon", None))      # Obras -> Instrumento
    familia = clean_ontology_name(get_first_value(ind, "perteneceAFamilia", None))  # Instrumentos -> Familia técnica

    # Mapeo de Tags dinámicos según propiedades booleanas de la ontología
    tags = []
    if to_bool(get_first_value(ind, "esAcustico", False)): tags.append("Acústico")
    if to_bool(get_first_value(ind, "requiereAfinacion", False)): tags.append("Requiere Afinación")
    if to_bool(get_first_value(ind, "esPolifonica", False)): tags.append("Polifónica")

    clases = [clase.name for clase in ind.is_a if hasattr(clase, 'name')]
    for c in clases: 
        if c != "NamedIndividual": tags.append(c)

    data = {
        "id": ind.name,
        "nombre": clean_ontology_name(nombre),
        "descripcion": str(descripcion),
        "periodoHistorico": str(periodo),
        "complejidadTecnica": str(dificultad),
        "anioLanzamiento": str(anio),
        "autor": creador,
        "instrumentoRequerido": instrumento,
        "familiaInstrumento": familia,
        "clases": clases,
        "tags": tags
    }
    
    _serialized_cache[ind.name] = data
    return dict(data)

# ==========================================
# CORE DE BÚSQUEDAS Y FILTROS SEMÁNTICOS
# ==========================================
def obtener_clases():
    onto = cargar_y_razonar()
    if not onto: return []
    return [{"nombre": clase.name} for clase in onto.classes()]

def buscar_individuos_por_clase(nombre_clase):
    onto = cargar_y_razonar()
    clase_objeto = onto.search_one(iri=f"*{nombre_clase}") if onto else None
    if not clase_objeto: return []
    return [serialize_element(ind) for ind in clase_objeto.instances()]

def buscar_por_texto(palabra_clave):

    onto = cargar_y_razonar()

    if not onto:
        return []

    tokens = [
        t
        for t in normalize_text(palabra_clave).split()
        if len(t) > 1
    ]

    tokens = expandir_tokens(tokens)

    resultados = []

    for ind in onto.individuals():

        data = serialize_element(ind)

        score = 0

        campos = {
            "nombre": normalize_text(data["nombre"]),
            "autor": normalize_text(data["autor"]),
            "periodo": normalize_text(data["periodoHistorico"]),
            "instrumento": normalize_text(data["instrumentoRequerido"]),
            "familia": normalize_text(data["familiaInstrumento"]),
            "tags": normalize_text(" ".join(data["tags"]))
        }

        for token in tokens:

            if token in campos["nombre"]:
                score += 20

            if token in campos["autor"]:
                score += 15

            if token in campos["familia"]:
                score += 10

            if token in campos["instrumento"]:
                score += 10

            if token in campos["periodo"]:
                score += 8

            if token in campos["tags"]:
                score += 5

        if score > 0:
            data["score"] = score
            resultados.append(data)

    resultados.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return resultados

def obtener_detalle_individuo(nombre_individuo):
    onto = cargar_y_razonar()
    individuo = onto.search_one(iri=f"*{nombre_individuo}") if onto else None
    if not individuo: return None
    return serialize_element(individuo)

# ==========================================
# ENRUTADOR DE CONSULTAS SEMÁNTICAS HÍBRIDAS
# ==========================================
def q_obras_complejas_piano():
    return [serialize_element(ind) for ind in cargar_y_razonar().individuals() 
            if normalize_text(serialize_element(ind)["complejidadTecnica"]) == "alta" 
            and "piano" in normalize_text(serialize_element(ind)["instrumentoRequerido"])]

def q_autores_periodo_romantico():
    return [serialize_element(ind) for ind in cargar_y_razonar().individuals() 
            if "romantico" in normalize_text(serialize_element(ind)["periodoHistorico"])]

def q_instrumentos_viento_madera():
    return [serialize_element(ind) for ind in cargar_y_razonar().individuals() 
            if "viento madera" in normalize_text(serialize_element(ind)["familiaInstrumento"])]

def q_instrumentos_cuerda():

    return [

        serialize_element(ind)

        for ind in cargar_y_razonar().individuals()

        if "cuerda"
        in normalize_text(
            serialize_element(ind)["familiaInstrumento"]
        )
    ]
def q_instrumentos_viento():

    return [

        serialize_element(ind)

        for ind in cargar_y_razonar().individuals()

        if "viento"
        in normalize_text(
            serialize_element(ind)["familiaInstrumento"]
        )
    ]

def q_instrumentos_percusion():

    return [

        serialize_element(ind)

        for ind in cargar_y_razonar().individuals()

        if "percusion"
        in normalize_text(
            serialize_element(ind)["familiaInstrumento"]
        )
    ]

def q_obras_romanticas():

    return [

        serialize_element(ind)

        for ind in cargar_y_razonar().individuals()

        if "romantico"
        in normalize_text(
            serialize_element(ind)["periodoHistorico"]
        )
    ]

def q_obras_por_autor(param):
    if not param: return []
    p = normalize_text(param)
    return [serialize_element(ind) for ind in cargar_y_razonar().individuals() 
            if p in normalize_text(serialize_element(ind)["autor"])]

SEMANTIC_QUERY_MAP = {
    # --- FILTROS POR FAMILIAS DE INSTRUMENTOS (ES / EN / FR) ---
    "instrumentos de cuerda": {"query": "instrumentos_cuerda"},
    "instrumentos de cuerdas": {"query": "instrumentos_cuerda"},
    "string instruments": {"query": "instrumentos_cuerda"},
    "strings": {"query": "instrumentos_cuerda"},
    "instruments a cordes": {"query": "instrumentos_cuerda"},
    "instruments à cordes": {"query": "instrumentos_cuerda"},
    
    "instrumentos de viento": {"query": "instrumentos_viento"},
    "wind instruments": {"query": "instrumentos_viento"},
    "brass instruments": {"query": "instrumentos_viento"},
    "instruments a vent": {"query": "instrumentos_viento"},
    "instruments à vent": {"query": "instrumentos_viento"},
    
    "instrumentos de viento madera": {"query": "instrumentos_viento_madera"},
    "woodwind instruments": {"query": "instrumentos_viento_madera"},
    "woodwinds": {"query": "instrumentos_viento_madera"},
    "instruments a vent en bois": {"query": "instrumentos_viento_madera"},
    "instruments à vent en bois": {"query": "instrumentos_viento_madera"},
    
    "instrumentos de percusion": {"query": "instrumentos_percusion"},
    "instrumentos de percusión": {"query": "instrumentos_percusion"},
    "percussion instruments": {"query": "instrumentos_percusion"},
    "percussion": {"query": "instrumentos_percusion"},
    "instruments de percussion": {"query": "instrumentos_percusion"},
    
    # --- FILTROS POR PERIODO (ES / EN / FR) ---
    "obras romanticas": {"query": "obras_romanticas"},
    "obras románticas": {"query": "obras_romanticas"},
    "romantic works": {"query": "obras_romanticas"},
    "romantic pieces": {"query": "obras_romanticas"},
    "romantic music": {"query": "obras_romanticas"},
    "oeuvres romantiques": {"query": "obras_romanticas"},
    "œuvres romantiques": {"query": "obras_romanticas"},
    
    # =========================================================================
    # --- FILTROS DINÁMICOS POR AUTOR TRILINGÜES (TODOS LOS COMPOSITORES) ---
    # =========================================================================

    # VIVALDI
    "obras de antonio vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "obras de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "works of antonio vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "works of vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "list of compositions by antonio vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "list of compositions by vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "oeuvres de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "œuvres de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "liste des compositions de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},

    # PIAZZOLLA
    "obras de astor piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "obras de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "works of astor piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "works of piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "list of compositions by astor piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "list of compositions by piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "oeuvres de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "œuvres de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "liste des compositions de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},

    # LISZT
    "obras de franz liszt": {"query": "obras_por_autor", "param": "liszt"},
    "obras de liszt": {"query": "obras_por_autor", "param": "liszt"},
    "works of franz liszt": {"query": "obras_por_autor", "param": "liszt"},
    "works of liszt": {"query": "obras_por_autor", "param": "liszt"},
    "list of compositions by franz liszt": {"query": "obras_por_autor", "param": "liszt"},
    "list of compositions by liszt": {"query": "obras_por_autor", "param": "liszt"},
    "oeuvres de liszt": {"query": "obras_por_autor", "param": "liszt"},
    "œuvres de liszt": {"query": "obras_por_autor", "param": "liszt"},
    "liste des compositions de liszt": {"query": "obras_por_autor", "param": "liszt"},

    # CHOPIN
    "obras de frederic chopin": {"query": "obras_por_autor", "param": "chopin"},
    "obras de chopin": {"query": "obras_por_autor", "param": "chopin"},
    "works of frederic chopin": {"query": "obras_por_autor", "param": "chopin"},
    "works of chopin": {"query": "obras_por_autor", "param": "chopin"},
    "list of compositions by frederic chopin": {"query": "obras_por_autor", "param": "chopin"},
    "list of compositions by chopin": {"query": "obras_por_autor", "param": "chopin"},
    "oeuvres de chopin": {"query": "obras_por_autor", "param": "chopin"},
    "œuvres de chopin": {"query": "obras_por_autor", "param": "chopin"},
    "liste des compositions de chopin": {"query": "obras_por_autor", "param": "chopin"},

    # JEAN MICHEL JARRE
    "obras de jean michel jarre": {"query": "obras_por_autor", "param": "jarre"},
    "obras de jarre": {"query": "obras_por_autor", "param": "jarre"},
    "works of jean michel jarre": {"query": "obras_por_autor", "param": "jarre"},
    "works of jarre": {"query": "obras_por_autor", "param": "jarre"},
    "list of compositions by jean michel jarre": {"query": "obras_por_autor", "param": "jarre"},
    "list of compositions by jarre": {"query": "obras_por_autor", "param": "jarre"},
    "oeuvres de jarre": {"query": "obras_por_autor", "param": "jarre"},
    "œuvres de jarre": {"query": "obras_por_autor", "param": "jarre"},
    "liste des compositions de jarre": {"query": "obras_por_autor", "param": "jarre"},

    # BACH
    "obras de johann sebastian bach": {"query": "obras_por_autor", "param": "bach"},
    "obras de bach": {"query": "obras_por_autor", "param": "bach"},
    "works of johann sebastian bach": {"query": "obras_por_autor", "param": "bach"},
    "works of bach": {"query": "obras_por_autor", "param": "bach"},
    "list of compositions by johann sebastian bach": {"query": "obras_por_autor", "param": "bach"},
    "list of compositions by bach": {"query": "obras_por_autor", "param": "bach"},
    "oeuvres de bach": {"query": "obras_por_autor", "param": "bach"},
    "œuvres de bach": {"query": "obras_por_autor", "param": "bach"},
    "liste des compositions de bach": {"query": "obras_por_autor", "param": "bach"},

    # BEETHOVEN
    "obras de ludwig van beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "obras de beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "works of ludwig van beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "works of beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "list of compositions by ludwig van beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "list of compositions by beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "oeuvres de beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "œuvres de beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "liste des compositions de beethoven": {"query": "obras_por_autor", "param": "beethoven"},

    # PAGANINI
    "obras de niccolo paganini": {"query": "obras_por_autor", "param": "paganini"},
    "obras de paganini": {"query": "obras_por_autor", "param": "paganini"},
    "works of niccolo paganini": {"query": "obras_por_autor", "param": "paganini"},
    "works of paganini": {"query": "obras_por_autor", "param": "paganini"},
    "list of compositions by niccolo paganini": {"query": "obras_por_autor", "param": "paganini"},
    "list of compositions by paganini": {"query": "obras_por_autor", "param": "paganini"},
    "oeuvres de paganini": {"query": "obras_por_autor", "param": "paganini"},
    "œuvres de paganini": {"query": "obras_por_autor", "param": "paganini"},
    "liste des compositions de paganini": {"query": "obras_por_autor", "param": "paganini"},

    # TCHAIKOVSKY
    "obras de pyotr ilyich tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "obras de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "works of pyotr ilyich tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "works of tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "list of compositions by pyotr ilyich tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "list of compositions by tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "oeuvres de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "œuvres de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "liste des compositions de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},

    # RACHMANINOFF
    "obras de sergei rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "obras de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "works of sergei rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "works of rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "list of compositions by sergei rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "list of compositions by rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "oeuvres de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "œuvres de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "liste des compositions de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},

    # MOZART
    "obras de wolfgang amadeus mozart": {"query": "obras_por_autor", "param": "mozart"},
    "obras de mozart": {"query": "obras_por_autor", "param": "mozart"},
    "works of wolfgang amadeus mozart": {"query": "obras_por_autor", "param": "mozart"},
    "works of mozart": {"query": "obras_por_autor", "param": "mozart"},
    "list of compositions by wolfgang amadeus mozart": {"query": "obras_por_autor", "param": "mozart"},
    "list of compositions by mozart": {"query": "obras_por_autor", "param": "mozart"},
    "oeuvres de mozart": {"query": "obras_por_autor", "param": "mozart"},
    "œuvres de mozart": {"query": "obras_por_autor", "param": "mozart"},
    "liste des compositions de mozart": {"query": "obras_por_autor", "param": "mozart"}
}
def detectar_consulta_semantica(texto):
    texto = normalize_text(texto)

    for frase, info in SEMANTIC_QUERY_MAP.items():
        if normalize_text(frase) in texto:
            return info.get("query"), info.get("param")

    return None, None

def ejecutar_consulta_semantica_musical(query_name, param=None):
    """Router central dinámico para invocar las consultas de lógica técnica."""
    queries = {
        "obras_complejas_piano": q_obras_complejas_piano,
        "autores_periodo_romantico": q_autores_periodo_romantico,
        "instrumentos_viento_madera": q_instrumentos_viento_madera,
        "instrumentos_cuerda": q_instrumentos_cuerda,
        "instrumentos_viento": q_instrumentos_viento,
        "instrumentos_percusion": q_instrumentos_percusion,
        "obras_romanticas": q_obras_romanticas,
    }
    queries_with_param = {
        "obras_por_autor": q_obras_por_autor,
    }

    if query_name in queries: return queries[query_name]()
    if query_name in queries_with_param: return queries_with_param[query_name](param)
    return []

# ==========================================
# ÁREA DE PRUEBAS LOCALES
# ==========================================
if __name__ == "__main__":
    termino = "Chopin"
    resultados = buscar_por_texto(termino)
    print(f"\n--- Coincidencias de prueba local para '{termino}': {len(resultados)} ---")
    for r in resultados:
        print(f"-> {r['nombre']} (Autor: {r['autor']} | Tags: {r['tags']})")