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
    "violin": ["violin", "violin", "violín"],
    "piano": ["piano"],
    "guitarra": ["guitarra"],
    "flauta": ["flauta"],
    "oboe": ["oboe"],
    "trompeta": ["trompeta"],
    "percusion": ["percusion", "percusión"],
    "cuerda": ["cuerda"],
    "viento": ["viento"],
    "romantico": ["romantico", "romántico"],
    "barroco": ["barroco"],
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
        with onto:
            sync_reasoner(infer_property_values=True) 
            
        _onto_instancia = onto
        print("[Motor] ¡Ontología Académica e Inferencias listas en memoria!")
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
    "instrumentos de cuerda": {
        "query": "instrumentos_cuerda",
    },
    "instrumentos de viento": {
        "query": "instrumentos_viento",
    },
    "instrumentos de percusion": {
        "query": "instrumentos_percusion",
    },
    "instrumentos de percusión": {
        "query": "instrumentos_percusion",
    },
    "obras romanticas": {
        "query": "obras_romanticas",
    },
    "obras románticas": {
        "query": "obras_romanticas",
    },
    "obras de mozart": {
        "query": "obras_por_autor",
        "param": "mozart",
    },
    "obras de chopin": {
        "query": "obras_por_autor",
        "param": "chopin",
    },
    "obras de bach": {
        "query": "obras_por_autor",
        "param": "bach",
    },
    "obras de beethoven": {
        "query": "obras_por_autor",
        "param": "beethoven",
    },
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