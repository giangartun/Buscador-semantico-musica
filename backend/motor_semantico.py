import os
import re
import unicodedata
from owlready2 import *

# Configuración de la ruta de la ontología
ruta_ontologia = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ontology", "musica.owl"))

# Variables globales para persistencia en memoria RAM y optimización de velocidad
_onto_instancia = None
_serialized_cache = {}

# Prefijos semánticos típicos a remover para limpiar la interfaz del frontend
PREFIXES_TO_REMOVE = ["Inst_", "Art_", "Gen_", "Alb_", "Can_", "Obra_", "Aut_"]
SUPPORTED_LANGS = {"es", "en", "fr"}

LANGUAGE_HINTS = {
    "es": {
        "acordeon", "aerofono", "arpa", "autor", "barroco", "baja", "cancion",
        "clasico", "clarinete", "composicion", "composiciones", "compositor",
        "concierto", "cuerda", "cuerdas", "facil", "flauta", "guitarra",
        "instrumento", "instrumentos", "mandolina", "metal", "musico", "obra",
        "obras", "percusion", "piano", "romantico", "saxofon", "sinfonia",
        "sonata", "teclado", "trombon", "trompeta", "viento", "violin",
    },
    "en": {
        "accordion", "aerophone", "author", "baroque", "clarinet", "classic",
        "classical", "composition", "compositions", "composer", "concerto",
        "easy", "flute", "guitar", "harp", "instrument", "instruments",
        "keyboard", "mandolin", "metal", "music", "musician", "percussion",
        "piece", "pieces", "piano", "romantic", "saxophone", "song", "sonata",
        "string", "strings", "symphony", "trombone", "trumpet", "violin",
        "wind", "work", "works",
    },
    "fr": {
        "accordeon", "aerophone", "auteur", "baroque", "chanson", "clarinette",
        "classique", "compositeur", "composition", "compositions", "concerto",
        "corde", "cordes", "facile", "flute", "guitare", "harpe",
        "instrument", "instruments", "mandoline", "metal", "morceau",
        "morceaux", "musicien", "oeuvre", "oeuvres", "percussion", "piano",
        "romantique", "saxophone", "sonate", "symphonie", "trombone",
        "trompette", "vent", "violon",
    },
}

LANGUAGE_RAW_HINTS = {
    "es": {
        "acordeón", "aerófono", "canción", "clásico", "composición",
        "fácil", "músico", "percusión", "romántico", "saxofón",
        "sinfonía", "trombón", "violín",
    },
    "fr": {
        "à", "flûte", "flûtes", "métal", "métaux", "œuvre", "œuvres",
        "pièce", "prélude", "préludes",
    },
}

LANGUAGE_STOPWORDS = {
    "es": {"de", "del", "la", "el", "los", "las", "para", "por", "con"},
    "en": {"of", "by", "the", "for", "with", "and"},
    "fr": {"de", "des", "du", "la", "le", "les", "pour", "avec", "et"},
}

LANGUAGE_EXACT_OVERRIDES = {
    "violin": "en",
    "flute": "en",
    "trumpet": "en",
    "clarinet": "en",
    "harp": "en",
    "keyboard": "en",
    "string": "en",
    "strings": "en",
    "wind": "en",
    "work": "en",
    "works": "en",
}

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

DOMAIN_TRANSLATIONS = {
    "en": {
        "Acústico": "Acoustic",
        "Requiere Afinación": "Requires tuning",
        "Polifónica": "Polyphonic",
        "Compositor": "Composer",
        "Obra": "Work",
        "Instrumento": "Instrument",
        "Capacidad": "Capability",
        "Thing": "Thing",
        "Instrumento_Cuerda": "String instrument",
        "Instrumento_Viento": "Wind instrument",
        "Instrumento_Percusion": "Percussion instrument",
        "Instrumento_Teclado": "Keyboard instrument",
        "Sinfonia": "Symphony",
        "Sinfonía": "Symphony",
        "Concierto": "Concerto",
        "Sonata": "Sonata",
        "Fuga": "Fugue",
        "Tocata": "Toccata",
        "Primavera": "Spring",
        "Lago de los Cisnes": "Swan Lake",
        "Claro de Luna": "Moonlight",
        "Cascanueces": "Nutcracker",
        "Danza Hada": "Fairy Dance",
        "Violin": "Violin",
        "Violín": "Violin",
        "Violin Solista": "Solo violin",
        "Piano Cola": "Grand piano",
        "Flauta": "Flute",
        "Guitarra": "Guitar",
        "Clarinete": "Clarinet",
        "Trompeta": "Trumpet",
        "Trombon": "Trombone",
        "Trombón": "Trombone",
        "Tuba": "Tuba",
        "Fagot": "Bassoon",
        "Corno Frances": "French horn",
        "Arpa": "Harp",
        "Contrabajo": "Double bass",
        "Viola": "Viola",
        "Violonchelo": "Cello",
        "Timbal": "Timpani",
        "Transposicion": "Transposition",
        "Transposición": "Transposition",
        "Organo": "Organ",
        "Órgano": "Organ",
        "Acordeon": "Accordion",
        "Acordeón": "Accordion",
        "Cuerda": "String",
        "Cuerdas": "Strings",
        "Viento": "Wind",
        "Percusion": "Percussion",
        "Percusión": "Percussion",
        "Romantico": "Romantic",
        "Romántico": "Romantic",
        "Clasico": "Classical",
        "Clásico": "Classical",
        "Barroco": "Baroque",
        "Alta": "High",
        "Media": "Medium",
        "Baja": "Low",
    },
    "fr": {
        "Acústico": "Acoustique",
        "Requiere Afinación": "Accord requis",
        "Polifónica": "Polyphonique",
        "Compositor": "Compositeur",
        "Obra": "Oeuvre",
        "Instrumento": "Instrument",
        "Capacidad": "Capacité",
        "Thing": "Entité",
        "Instrumento_Cuerda": "Instrument à cordes",
        "Instrumento_Viento": "Instrument à vent",
        "Instrumento_Percusion": "Instrument de percussion",
        "Instrumento_Teclado": "Instrument à clavier",
        "Sinfonia": "Symphonie",
        "Sinfonía": "Symphonie",
        "Concierto": "Concerto",
        "Sonata": "Sonate",
        "Fuga": "Fugue",
        "Tocata": "Toccata",
        "Primavera": "Printemps",
        "Lago de los Cisnes": "Lac des cygnes",
        "Claro de Luna": "Clair de lune",
        "Cascanueces": "Casse-noisette",
        "Danza Hada": "Danse de la fee",
        "Violin": "Violon",
        "Violín": "Violon",
        "Violin Solista": "Violon soliste",
        "Piano Cola": "Piano à queue",
        "Flauta": "Flûte",
        "Guitarra": "Guitare",
        "Clarinete": "Clarinette",
        "Trompeta": "Trompette",
        "Trombon": "Trombone",
        "Trombón": "Trombone",
        "Tuba": "Tuba",
        "Fagot": "Basson",
        "Corno Frances": "Cor",
        "Arpa": "Harpe",
        "Contrabajo": "Contrebasse",
        "Viola": "Alto",
        "Violonchelo": "Violoncelle",
        "Timbal": "Timbales",
        "Transposicion": "Transposition",
        "Transposición": "Transposition",
        "Organo": "Orgue",
        "Órgano": "Orgue",
        "Acordeon": "Accordeon",
        "Acordeón": "Accordeon",
        "Cuerda": "Corde",
        "Cuerdas": "Cordes",
        "Viento": "Vent",
        "Percusion": "Percussion",
        "Percusión": "Percussion",
        "Romantico": "Romantique",
        "Romántico": "Romantique",
        "Clasico": "Classique",
        "Clásico": "Classique",
        "Barroco": "Baroque",
        "Alta": "Haute",
        "Media": "Moyenne",
        "Baja": "Basse",
    },
}

def guardar_ontologia():
    """
    Guarda físicamente musica.owl.
    """
    global _onto_instancia

    if _onto_instancia is None:
        return False

    try:
        _onto_instancia.save(file=ruta_ontologia)
        print(f"[OWL] Ontología guardada en: {ruta_ontologia}")
        return True

    except Exception as e:
        print(f"[OWL] Error al guardar ontología: {e}")
        return False


def recargar_ontologia():
    """
    Fuerza la recarga completa de musica.owl.
    """
    global _onto_instancia
    global _serialized_cache

    _onto_instancia = None
    _serialized_cache.clear()

    return cargar_y_razonar()

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
        except Exception as razonador_error:
            print(f"[Motor] Razonador no disponible, continuando con relaciones directas: {razonador_error}")
            
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

def normalize_lang(lang):
    if not lang:
        return "es"

    lang = str(lang).lower()
    return lang if lang in SUPPORTED_LANGS else "es"

def detectar_idioma_busqueda(texto, fallback="es"):
    fallback = normalize_lang(fallback)
    texto_original = str(texto or "").lower().strip()
    texto_normalizado = normalize_text(texto)

    if not texto_normalizado:
        return fallback

    tokens = texto_normalizado.split()
    raw_tokens = texto_original.replace("_", " ").replace("-", " ").split()
    scores = {lang: 0 for lang in SUPPORTED_LANGS}

    for token in tokens:
        override_lang = LANGUAGE_EXACT_OVERRIDES.get(token)
        if override_lang:
            scores[override_lang] += 3

    for lang, hints in LANGUAGE_RAW_HINTS.items():
        for hint in hints:
            if hint in texto_original:
                scores[lang] += 4

    for lang, stopwords in LANGUAGE_STOPWORDS.items():
        for token in raw_tokens:
            if token in stopwords:
                scores[lang] += 1

    for lang, hints in LANGUAGE_HINTS.items():
        for token in tokens:
            if token in hints:
                scores[lang] += 2

        for phrase in hints:
            if " " in phrase and phrase in texto_normalizado:
                scores[lang] += 3

    winner, winner_score = max(scores.items(), key=lambda item: item[1])

    if winner_score == 0:
        return fallback

    tied = [lang for lang, score in scores.items() if score == winner_score]

    if "fr" in tied and any(char in texto_original for char in "àâçéèêëîïôûùüÿœ"):
        return "fr"

    if "es" in tied and any(char in texto_original for char in "áéíóúñü"):
        return "es"

    return fallback if fallback in tied else winner

def translate_domain_text(value, lang="es"):
    lang = normalize_lang(lang)

    if value is None or lang == "es":
        return value

    text = str(value)
    translations = DOMAIN_TRANSLATIONS.get(lang, {})

    if text in translations:
        return translations[text]

    translated = text
    for source, target in sorted(translations.items(), key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(re.escape(source), target, translated, flags=re.IGNORECASE)

    return translated

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

def get_relation_values(individual, property_names):
    values = []

    for property_name in property_names:
        try:
            values.extend(getattr(individual, property_name, []))
        except:
            pass

    return values

def unique_clean_names(values, lang="es"):
    seen = set()
    cleaned = []

    for value in values:
        name = translate_domain_text(clean_ontology_name(value), lang)
        key = normalize_text(name)

        if name and name != "-" and key not in seen:
            seen.add(key)
            cleaned.append(name)

    return cleaned

def find_related_by_property(target, property_names):
    onto = cargar_y_razonar()
    related = []

    if not onto:
        return related

    for candidate in onto.individuals():
        for value in get_relation_values(candidate, property_names):
            if value == target:
                related.append(candidate)
                break

    return related

# ==========================================
# SERIALIZADOR DE INDIVIDUOS PARA EL FRONTEND
# ==========================================
def serialize_element(ind, lang="es"):
    """Transforma un individuo complejo de Owlready2 en un diccionario plano con caché."""
    lang = normalize_lang(lang)
    cache_key = f"{ind.name}:{lang}"

    if cache_key in _serialized_cache:
        return dict(_serialized_cache[cache_key])

    # Propiedades de datos teóricas e históricas
    nombre = get_first_value(ind, "nombre", ind.name)
    descripcion = get_first_value(ind, "descripcion", "-")
    periodo = get_first_value(ind, "periodoHistorico", "-")       # Ej: Barroco, Romántico
    dificultad = get_first_value(ind, "complejidadTecnica", "-")   # Ej: Alta, Media, Baja
    anio = get_first_value(ind, "anioLanzamiento", "-")            # Año de composición o publicación

    # Relaciones entre objetos
    creador = translate_domain_text(clean_ontology_name(get_first_value(ind, "creadoPor", None)), lang)          # Obras -> Autor
    instrumento = translate_domain_text(clean_ontology_name(get_first_value(ind, "seTocaCon", None)), lang)      # Obras -> Instrumento
    familia = translate_domain_text(clean_ontology_name(get_first_value(ind, "perteneceAFamilia", None)), lang)  # Instrumentos -> Familia técnica

    # Obras compuestas por este individuo. Usa la inversa inferida y un
    # respaldo directo sobre las obras que apuntan al compositor.
    obras_compuestas = unique_clean_names(
        get_relation_values(ind, ["compuso"]) +
        find_related_by_property(ind, ["compuestaPor"]),
        lang
    )

    # Instrumentos que interpretan o requiere esta obra.
    instrumentos_obra = unique_clean_names(
        get_relation_values(ind, ["interpretadaPor", "seTocaCon"]),
        lang
    )

    # Compositor desde data property (para Obras que tienen 'compositor' como string)
    compositor_dp = "-"
    try:
        vals = list(getattr(ind, "compositor", []))
        if vals:
            compositor_dp = translate_domain_text(str(vals[0]), lang)
    except:
        pass

    compositores_relacionados = unique_clean_names(
        get_relation_values(ind, ["compuestaPor", "creadoPor"]),
        lang
    )

    if compositor_dp == "-" and compositores_relacionados:
        compositor_dp = compositores_relacionados[0]

    if creador == "-" and compositores_relacionados:
        creador = compositores_relacionados[0]

    if instrumento == "-" and instrumentos_obra:
        instrumento = instrumentos_obra[0]

    # Mapeo de Tags dinámicos según propiedades booleanas de la ontología
    tags = []
    if to_bool(get_first_value(ind, "esAcustico", False)): tags.append(translate_domain_text("Acústico", lang))
    if to_bool(get_first_value(ind, "requiereAfinacion", False)): tags.append(translate_domain_text("Requiere Afinación", lang))
    if to_bool(get_first_value(ind, "esPolifonica", False)): tags.append(translate_domain_text("Polifónica", lang))

    clases = [
        translate_domain_text(clase.name, lang)
        for clase in ind.is_a
        if hasattr(clase, 'name')
    ]
    for c in clases: 
        if c != "NamedIndividual": tags.append(c)

    data = {
        "id": ind.name,
        "nombre": translate_domain_text(clean_ontology_name(nombre), lang),
        "descripcion": translate_domain_text(str(descripcion), lang),
        "periodoHistorico": translate_domain_text(str(periodo), lang),
        "complejidadTecnica": translate_domain_text(str(dificultad), lang),
        "anioLanzamiento": str(anio),
        "autor": creador,
        "instrumentoRequerido": instrumento,
        "familiaInstrumento": familia,
        "clases": clases,
        "tags": tags,
        "obrasCompuestas": obras_compuestas,
        "instrumentosObra": instrumentos_obra,
        "compositorTexto": compositor_dp,
    }
    
    _serialized_cache[cache_key] = data
    return dict(data)

# ==========================================
# CORE DE BÚSQUEDAS Y FILTROS SEMÁNTICOS
# ==========================================
def obtener_clases():
    onto = cargar_y_razonar()
    if not onto: return []
    return [{"nombre": clase.name} for clase in onto.classes()]

def buscar_individuos_por_clase(nombre_clase, lang="es"):
    onto = cargar_y_razonar()
    clase_objeto = onto.search_one(iri=f"*{nombre_clase}") if onto else None
    if not clase_objeto: return []
    return [serialize_element(ind, lang) for ind in clase_objeto.instances()]

def buscar_por_texto(palabra_clave, lang="es"):

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

        data = serialize_element(ind, lang)

        score = 0

        campos = {
            "nombre": normalize_text(data["nombre"]),
            "autor": normalize_text(data["autor"]),
            "compositor": normalize_text(data["compositorTexto"]),
            "periodo": normalize_text(data["periodoHistorico"]),
            "instrumento": normalize_text(data["instrumentoRequerido"]),
            "instrumentos_obra": normalize_text(" ".join(data["instrumentosObra"])),
            "familia": normalize_text(data["familiaInstrumento"]),
            "obras_compuestas": normalize_text(" ".join(data["obrasCompuestas"])),
            "tags": normalize_text(" ".join(data["tags"]))
        }

        for token in tokens:

            if token in campos["nombre"]:
                score += 20

            if token in campos["autor"]:
                score += 15

            if token in campos["compositor"]:
                score += 15

            if token in campos["obras_compuestas"]:
                score += 12

            if token in campos["familia"]:
                score += 10

            if token in campos["instrumento"]:
                score += 10

            if token in campos["instrumentos_obra"]:
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

def obtener_detalle_individuo(nombre_individuo, lang="es"):
    onto = cargar_y_razonar()
    individuo = onto.search_one(iri=f"*{nombre_individuo}") if onto else None
    if not individuo: return None
    return serialize_element(individuo, lang)

# ==========================================
# ENRUTADOR DE CONSULTAS SEMÁNTICAS HÍBRIDAS
# ==========================================
def q_obras_complejas_piano(lang="es"):
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if normalize_text(serialize_element(ind, "es")["complejidadTecnica"]) == "alta" 
            and "piano" in normalize_text(serialize_element(ind, "es")["instrumentoRequerido"])]

def q_autores_periodo_romantico(lang="es"):
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if "romantico" in normalize_text(serialize_element(ind, "es")["periodoHistorico"])]

def q_instrumentos_viento_madera(lang="es"):
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if "viento madera" in normalize_text(serialize_element(ind, "es")["familiaInstrumento"])]

def q_instrumentos_cuerda(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "cuerda"
        in normalize_text(
            serialize_element(ind, "es")["familiaInstrumento"]
        )
    ]
def q_instrumentos_viento(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "viento"
        in normalize_text(
            serialize_element(ind, "es")["familiaInstrumento"]
        )
    ]

def q_instrumentos_percusion(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "percusion"
        in normalize_text(
            serialize_element(ind, "es")["familiaInstrumento"]
        )
    ]

def q_obras_romanticas(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "romantico"
        in normalize_text(
            serialize_element(ind, "es")["periodoHistorico"]
        )
    ]

def q_obras_por_autor(param, lang="es"):
    if not param: return []
    p = normalize_text(param)
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if p in normalize_text(serialize_element(ind, "es")["autor"])
            or p in normalize_text(serialize_element(ind, "es")["compositorTexto"])]

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

def ejecutar_consulta_semantica_musical(query_name, param=None, lang="es"):
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

    if query_name in queries: return queries[query_name](lang)
    if query_name in queries_with_param: return queries_with_param[query_name](param, lang)
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
